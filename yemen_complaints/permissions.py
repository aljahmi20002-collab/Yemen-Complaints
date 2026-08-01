from __future__ import annotations

import frappe

from yemen_complaints.utils import ROLE_MAP


def app_has_access():
    roles = set(frappe.get_roles())
    return any(role in roles for role in ROLE_MAP.values())


def complaint_case_query_conditions(user: str | None = None) -> str:
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    escaped_user = frappe.db.escape(user)

    if ROLE_MAP["manager"] in roles:
        return ""
    if ROLE_MAP["advisor"] in roles:
        return (
            f"(`tabComplaint Case`.`advisor_user` = {escaped_user} "
            f"or ifnull(`tabComplaint Case`.`advisor_user`, '') = '' "
            f"or `tabComplaint Case`.`status` in ('New', 'Under Review'))"
        )
    if ROLE_MAP["agency"] in roles:
        return f"(`tabComplaint Case`.`agency_officer_user` = {escaped_user})"
    if ROLE_MAP["follow_up"] in roles:
        return f"(`tabComplaint Case`.`follow_up_user` = {escaped_user})"
    return (
        f"(`tabComplaint Case`.`citizen_user` = {escaped_user} "
        f"or `tabComplaint Case`.`owner` = {escaped_user})"
    )


def complaint_case_has_permission(doc, user: str | None = None, permission_type: str | None = None) -> bool:
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))

    if ROLE_MAP["manager"] in roles:
        return True
    if ROLE_MAP["advisor"] in roles:
        return doc.advisor_user == user or not doc.advisor_user or doc.status in ["New", "Under Review"]
    if ROLE_MAP["agency"] in roles:
        return doc.agency_officer_user == user
    if ROLE_MAP["follow_up"] in roles:
        return doc.follow_up_user == user
    return doc.citizen_user == user or doc.owner == user
