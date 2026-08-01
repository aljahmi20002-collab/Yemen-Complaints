from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import add_days, add_to_date, getdate, now_datetime, today

from yemen_complaints.utils import CASE_PREFIX, CLOSED_STATUSES, ROLE_MAP
from yemen_complaints.verification import mark_verification_as_used, validate_complaint_identity_verification

STATUS_TRANSITION_ROLES = {
    "New": {ROLE_MAP["advisor"], ROLE_MAP["manager"]},
    "Under Review": {ROLE_MAP["advisor"], ROLE_MAP["manager"]},
    "Assigned": {ROLE_MAP["advisor"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
    "In Progress": {ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
    "Waiting Citizen": {ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
    "Resolved": {ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
    "Rejected": {ROLE_MAP["advisor"], ROLE_MAP["manager"]},
    "Closed": {ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
    "Overdue": {ROLE_MAP["follow_up"], ROLE_MAP["manager"]},
}

STAFF_ROLES = {
    ROLE_MAP["advisor"],
    ROLE_MAP["agency"],
    ROLE_MAP["follow_up"],
    ROLE_MAP["manager"],
}


class ComplaintCase(Document):
    def autoname(self):
        prefix = CASE_PREFIX.get(self.case_type or "Complaint", "CMP")
        year = getdate(today()).year
        self.name = make_autoname(f"{prefix}-{year}-.#####")

    def validate(self):
        self.bind_logged_in_citizen()
        apply_sla_and_defaults(self, None)
        self.validate_contact_details()
        self.validate_location_hierarchy()
        validate_complaint_identity_verification(self)
        self.enforce_state_transition_rules()
        self.sync_status_flags()
        self.refresh_last_public_update()

    def after_insert(self):
        mark_verification_as_used(self)

    def before_save(self):
        if self.status in ["Resolved", "Closed"] and not self.resolved_on:
            self.resolved_on = now_datetime()
        if self.status not in ["Resolved", "Closed"]:
            self.resolved_on = None

    def bind_logged_in_citizen(self):
        if frappe.session.user != "Guest" and is_pure_citizen() and not self.citizen_user:
            self.citizen_user = frappe.session.user

    def validate_contact_details(self):
        if not self.mobile_number and not self.email:
            frappe.throw(_("At least one contact channel (mobile or email) is required."))

    def validate_location_hierarchy(self):
        self._validate_district_matches_governorate('citizen_governorate', 'citizen_district', _('Citizen District'))
        self._validate_district_matches_governorate('incident_governorate', 'incident_district', _('Incident District'))

    def _validate_district_matches_governorate(self, governorate_field: str, district_field: str, district_label):
        governorate = self.get(governorate_field)
        district = self.get(district_field)
        if not district:
            return
        if not governorate:
            frappe.throw(_('{0} requires a governorate to be selected first.').format(district_label))

        district_governorate = frappe.db.get_value('Yemen District', district, 'governorate')
        if district_governorate and district_governorate != governorate:
            frappe.throw(_('{0} does not belong to the selected governorate.').format(district_label))

    def enforce_state_transition_rules(self):
        if self.status in {"Resolved", "Closed"} and not self.resolution_summary:
            frappe.throw(_("Resolution Summary is required before resolving or closing the case."))

        if self.status == "Assigned" and not any([self.advisor_user, self.agency_officer_user, self.follow_up_user, self.get("assignments")]):
            frappe.throw(_("At least one assignment or responsible user is required before moving to Assigned."))

        previous = self.get_doc_before_save()
        if not previous or previous.status == self.status:
            return

        if frappe.session.user == "Administrator":
            return

        roles = set(frappe.get_roles())
        allowed_roles = STATUS_TRANSITION_ROLES.get(self.status, set())
        if allowed_roles and not roles.intersection(allowed_roles):
            frappe.throw(
                _("You are not allowed to move the case to status: {0}").format(self.status),
                frappe.PermissionError,
            )

    def sync_status_flags(self):
        if self.status in CLOSED_STATUSES:
            self.is_overdue = 0
            return
        if self.target_resolution_date and getdate(self.target_resolution_date) < getdate(today()):
            self.is_overdue = 1
            if self.status != "Overdue":
                self.status = "Overdue"
        else:
            self.is_overdue = 0

    def refresh_last_public_update(self):
        public_updates = [d for d in self.get("updates") if d.visibility == "Public" and d.message]
        if public_updates:
            latest = sorted(public_updates, key=lambda x: x.posted_on or now_datetime())[-1]
            text = frappe.utils.strip_html(latest.message or "")
            self.last_public_update = text[:280]
        elif self.is_new():
            self.last_public_update = ""


@frappe.whitelist()
def add_public_update(
    docname: str,
    message: str,
    new_status: str | None = None,
    visibility: str | None = None,
    update_type: str | None = None,
):
    doc = frappe.get_doc("Complaint Case", docname)
    message = (message or "").strip()
    if not message:
        frappe.throw(_("Message is required."))

    pure_citizen = is_pure_citizen()
    final_visibility = visibility or ("Public" if pure_citizen else "Internal")
    final_update_type = update_type or ("Citizen Note" if pure_citizen else "Internal Note")

    if pure_citizen:
        if final_visibility != "Public":
            frappe.throw(_("Citizen updates must be public."), frappe.PermissionError)
        if new_status:
            frappe.throw(_("Citizens cannot change case status directly."), frappe.PermissionError)
        final_update_type = "Citizen Note"

    row = doc.append(
        "updates",
        {
            "posted_on": now_datetime(),
            "author": frappe.session.user,
            "update_type": final_update_type,
            "visibility": final_visibility,
            "message": message,
            "new_status": new_status,
        },
    )

    if final_visibility == "Public" and not pure_citizen and not doc.first_response_on:
        doc.first_response_on = row.posted_on

    if new_status:
        doc.status = new_status

    doc.save(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def assign_case(docname: str, assigned_to: str, role_type: str, due_date: str | None = None, instructions: str | None = None):
    roles = set(frappe.get_roles())
    allowed_roles = {ROLE_MAP["advisor"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]}
    if frappe.session.user != "Administrator" and not roles.intersection(allowed_roles):
        frappe.throw(_("You are not allowed to assign complaint cases."), frappe.PermissionError)

    doc = frappe.get_doc("Complaint Case", docname)
    doc.append(
        "assignments",
        {
            "assigned_to": assigned_to,
            "role_type": role_type,
            "assigned_on": now_datetime(),
            "due_date": due_date,
            "status": "Open",
            "instructions": instructions,
        },
    )

    if role_type == "Advisor":
        doc.advisor_user = assigned_to
    elif role_type == "Agency Officer":
        doc.agency_officer_user = assigned_to
    elif role_type == "Follow-up Officer":
        doc.follow_up_user = assigned_to

    if doc.status in ["New", "Under Review"]:
        doc.status = "Assigned"

    doc.save(ignore_permissions=True)
    return doc.name


@frappe.whitelist()
def get_allowed_status_transitions(case_name: str):
    doc = frappe.get_doc("Complaint Case", case_name)
    roles = set(frappe.get_roles())
    if frappe.session.user == "Administrator":
        return sorted(STATUS_TRANSITION_ROLES.keys())

    allowed = []
    for status, status_roles in STATUS_TRANSITION_ROLES.items():
        if roles.intersection(status_roles):
            allowed.append(status)
    return allowed



def apply_sla_and_defaults(doc, method):
    if not doc.status:
        doc.status = "New"
    if not doc.case_type:
        doc.case_type = "Complaint"

    category = None
    if doc.category:
        category = frappe.get_cached_doc("Complaint Category", doc.category)

    if not doc.priority:
        doc.priority = category.default_priority if category and category.default_priority else "Medium"
    elif category and category.default_priority and doc.priority == "Medium" and doc.is_new():
        doc.priority = category.default_priority

    if category:
        if not doc.government_entity and category.default_entity:
            doc.government_entity = category.default_entity
        if not doc.target_response_on and category.sla_first_response_hours:
            doc.target_response_on = add_to_date(now_datetime(), hours=category.sla_first_response_hours)
        if not doc.target_resolution_date and category.sla_resolution_days:
            doc.target_resolution_date = add_days(today(), category.sla_resolution_days)

    if doc.government_entity and not doc.agency_officer_user:
        entity = frappe.get_cached_doc("Government Entity", doc.government_entity)
        if entity.default_officer:
            doc.agency_officer_user = entity.default_officer


def is_pure_citizen() -> bool:
    roles = set(frappe.get_roles())
    return ROLE_MAP["citizen"] in roles and not roles.intersection(STAFF_ROLES)
