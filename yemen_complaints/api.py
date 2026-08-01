from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime, today

from yemen_complaints.security import (
    AI_APPLY_USER_LIMIT,
    AI_APPLY_USER_WINDOW,
    AI_ASSISTANT_USER_LIMIT,
    AI_ASSISTANT_USER_WINDOW,
    AI_TEXT_USER_LIMIT,
    AI_TEXT_USER_WINDOW,
    PUBLIC_TRACK_IP_LIMIT,
    PUBLIC_TRACK_IP_WINDOW,
    enforce_rate_limit,
    get_request_ip,
)
from yemen_complaints.utils import ROLE_MAP

OPEN_STATUS_LIST = ["New", "Under Review", "Assigned", "In Progress", "Waiting Citizen", "Overdue"]
CLOSED_STATUS_LIST = ["Resolved", "Closed"]


@frappe.whitelist(allow_guest=True)
def track_case(case_id: str, email: str | None = None, mobile: str | None = None):
    if not case_id:
        frappe.throw(_("Case ID is required"))

    enforce_rate_limit(
        "public_track_ip",
        get_request_ip(),
        limit=PUBLIC_TRACK_IP_LIMIT,
        window_seconds=PUBLIC_TRACK_IP_WINDOW,
        error_message=_("Too many tracking requests from this network. Please try again later."),
        event_type="Public Tracking IP Limit",
        severity="High",
        metadata={"case_id": case_id},
    )

    doc = frappe.get_doc("Complaint Case", case_id)

    email_matches = email and email.strip().lower() == (doc.email or "").strip().lower()
    mobile_matches = mobile and mobile.strip() == (doc.mobile_number or "").strip()
    session_user_matches = frappe.session.user != "Guest" and frappe.session.user == doc.citizen_user

    if not (email_matches or mobile_matches or session_user_matches):
        frappe.throw(_("Tracking verification failed"), frappe.PermissionError)

    return {
        "name": doc.name,
        "subject": doc.subject,
        "case_type": doc.case_type,
        "status": doc.status,
        "priority": doc.priority,
        "government_entity": doc.government_entity,
        "target_resolution_date": doc.target_resolution_date,
        "last_public_update": doc.last_public_update,
        "resolution_summary": doc.resolution_summary if doc.status in ["Resolved", "Closed"] else None,
    }


@frappe.whitelist()
def get_my_cases():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)

    user_email = frappe.db.get_value("User", frappe.session.user, "email")
    filters = [["Complaint Case", "citizen_user", "=", frappe.session.user]]
    or_filters = [["Complaint Case", "email", "=", user_email]] if user_email else None

    rows = frappe.get_all(
        "Complaint Case",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "subject",
            "case_type",
            "status",
            "priority",
            "government_entity",
            "creation",
            "target_resolution_date",
            "last_public_update",
        ],
        order_by="modified desc",
    )

    return rows


@frappe.whitelist()
def get_case_timeline(case_id: str):
    if not case_id:
        frappe.throw(_("Case ID is required"))

    doc = frappe.get_doc("Complaint Case", case_id)
    if not _can_access_case(doc) and not _can_access_case_as_staff(doc):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    staff_view = _can_access_case_as_staff(doc)
    updates = []
    for row in doc.get("updates") or []:
        if row.visibility == "Public" or staff_view:
            updates.append(
                {
                    "posted_on": row.posted_on,
                    "author": row.author,
                    "update_type": row.update_type,
                    "visibility": row.visibility,
                    "new_status": row.new_status,
                    "message": row.message,
                }
            )

    assignments = []
    if staff_view:
        for row in doc.get("assignments") or []:
            assignments.append(
                {
                    "assigned_to": row.assigned_to,
                    "role_type": row.role_type,
                    "assigned_on": row.assigned_on,
                    "due_date": row.due_date,
                    "status": row.status,
                    "instructions": row.instructions,
                }
            )

    return {
        "viewer_mode": "staff" if staff_view else "citizen",
        "case": {
            "name": doc.name,
            "subject": doc.subject,
            "status": doc.status,
            "case_type": doc.case_type,
            "priority": doc.priority,
            "government_entity": doc.government_entity,
            "target_resolution_date": doc.target_resolution_date,
        },
        "updates": updates,
        "assignments": assignments,
    }


@frappe.whitelist()
def get_case_activity_feed(case_id: str):
    if not case_id:
        frappe.throw(_("Case ID is required"))

    doc = frappe.get_doc("Complaint Case", case_id)
    if not _can_access_case_as_staff(doc):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    feed = []
    for row in doc.get("assignments") or []:
        feed.append(
            {
                "event_type": "assignment",
                "timestamp": row.assigned_on,
                "title": row.role_type,
                "user": row.assigned_to,
                "description": row.instructions,
                "status": row.status,
            }
        )

    for row in doc.get("updates") or []:
        feed.append(
            {
                "event_type": "update",
                "timestamp": row.posted_on,
                "title": row.update_type,
                "user": row.author,
                "description": row.message,
                "status": row.new_status or row.visibility,
            }
        )

    feed = sorted(feed, key=lambda d: d.get("timestamp") or "", reverse=True)
    return feed


@frappe.whitelist()
def get_internal_dashboard_summary(
    status_filter: str | None = None,
    priority_filter: str | None = None,
    entity_filter: str | None = None,
    time_filter: str | None = None,
):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)

    roles = set(frappe.get_roles())
    role_priority = [
        (ROLE_MAP["manager"], _("System Manager")),
        (ROLE_MAP["advisor"], _("Advisor")),
        (ROLE_MAP["follow_up"], _("Follow-up Officer")),
        (ROLE_MAP["agency"], _("Agency Officer")),
    ]
    primary_role = next((label for role, label in role_priority if role in roles), _("Internal User"))
    dashboard_filters = _build_dashboard_filters(status_filter, priority_filter, entity_filter, time_filter)

    role_key = next((role for role, _label in role_priority if role in roles), "internal")

    summary = {
        "role_label": primary_role,
        "role_key": role_key,
        "applied_filters": {
            "status_filter": status_filter or "",
            "priority_filter": priority_filter or "",
            "entity_filter": entity_filter or "",
            "time_filter": time_filter or "",
        },
        "filter_options": {
            "statuses": ["", *OPEN_STATUS_LIST, "Resolved", "Rejected", "Closed"],
            "priorities": ["", "Low", "Medium", "High", "Critical"],
            "entities": [""] + [row.get("label") for row in _group_case_counts("government_entity", limit=50, exclude_empty=True)],
            "time_ranges": [
                {"value": "", "label": _("All Time")},
                {"value": "today", "label": _("Today")},
                {"value": "7d", "label": _("Last 7 Days")},
                {"value": "30d", "label": _("Last 30 Days")},
                {"value": "90d", "label": _("Last 90 Days")},
            ],
        },
        "counts": {
            "total_visible": _count_cases(dashboard_filters or None),
            "open_cases": _count_cases(_merge_case_filters({"status": ["in", OPEN_STATUS_LIST]}, dashboard_filters, allow_override=False)),
            "new_cases": _count_cases(_merge_case_filters({"status": "New"}, dashboard_filters, allow_override=False)),
            "under_review": _count_cases(_merge_case_filters({"status": "Under Review"}, dashboard_filters, allow_override=False)),
            "waiting_citizen": _count_cases(_merge_case_filters({"status": "Waiting Citizen"}, dashboard_filters, allow_override=False)),
            "overdue": _count_cases(_merge_case_filters({"status": "Overdue"}, dashboard_filters, allow_override=False)),
            "resolved": _count_cases(_merge_case_filters({"status": ["in", CLOSED_STATUS_LIST]}, dashboard_filters, allow_override=False)),
            "high_priority": _count_cases(_merge_case_filters({"priority": ["in", ["High", "Critical"]]}, dashboard_filters, allow_override=False)),
        },
        "my_queue": [],
        "recent_cases": frappe.get_list(
            "Complaint Case",
            filters=dashboard_filters or None,
            fields=["name", "subject", "status", "priority", "government_entity", "modified", "target_resolution_date"],
            order_by="modified desc",
            page_length=8,
        ),
        "urgent_cases": frappe.get_list(
            "Complaint Case",
            filters=_merge_case_filters({"priority": ["in", ["High", "Critical"]], "status": ["in", OPEN_STATUS_LIST]}, dashboard_filters, allow_override=False),
            fields=["name", "subject", "status", "priority", "government_entity", "target_resolution_date"],
            order_by="modified desc",
            page_length=6,
        ),
        "quick_links": [
            {"label": _("Complaint Cases"), "route": "/app/complaint-case"},
            {"label": _("Complaint Summary Report"), "route": "/app/query-report/Complaint%20Summary"},
            {"label": _("SLA Breaches Report"), "route": "/app/query-report/SLA%20Breaches"},
            {"label": _("Officer Workload Report"), "route": "/app/query-report/Officer%20Workload"},
            {"label": _("Executive Leadership Dashboard"), "route": "/app/executive-leadership-dashboard"},
            {"label": _("AI Logs"), "route": "/app/complaint-ai-log"},
            {"label": _("Identity Verification Records"), "route": "/app/complaint-identity-verification"},
            {"label": _("Security Events"), "route": "/app/complaint-security-event"},
        ],
    }

    queue_filters = []
    if ROLE_MAP["advisor"] in roles:
        queue_filters.append((_("Advisor Queue"), {"status": ["in", ["New", "Under Review"]]}))
    if ROLE_MAP["agency"] in roles:
        queue_filters.append((_("Agency Queue"), {"agency_officer_user": frappe.session.user, "status": ["in", OPEN_STATUS_LIST]}))
    if ROLE_MAP["follow_up"] in roles:
        queue_filters.append((_("Follow-up Queue"), {"follow_up_user": frappe.session.user, "status": ["in", OPEN_STATUS_LIST]}))
    if ROLE_MAP["manager"] in roles:
        queue_filters.append((_("Manager Oversight"), {"status": ["in", OPEN_STATUS_LIST]}))

    for label, filters in queue_filters:
        summary["my_queue"].append({
            "label": label,
            "count": _count_cases(_merge_case_filters(filters, dashboard_filters, allow_override=False)),
        })

    summary["status_breakdown"] = _group_case_counts("status", filters=dashboard_filters or None)
    summary["priority_breakdown"] = _group_case_counts("priority", filters=dashboard_filters or None)
    summary["entity_breakdown"] = _group_case_counts("government_entity", limit=6, exclude_empty=True, filters=dashboard_filters or None)
    summary["monthly_trend"] = _get_monthly_case_trend(limit=6, filters=dashboard_filters or None)
    summary["verification_breakdown"] = _get_identity_verification_summary(limit=4)
    summary["verification_health"] = _get_verification_health_summary(limit=6)
    summary["ai_activity"] = _get_ai_activity_summary(limit=6)
    summary["top_officers"] = _get_top_officers(filters=dashboard_filters or None)
    summary["sla_health"] = _get_sla_health_summary(filters=dashboard_filters or None)
    summary["top_overdue_entities"] = _get_top_overdue_entities(filters=dashboard_filters or None)
    summary["executive_summary"] = _build_executive_summary(summary)
    summary["action_center"] = _build_action_center(summary)
    summary["alert_center"] = _build_alert_center(summary)

    return summary


@frappe.whitelist()
def get_executive_dashboard_summary(
    time_filter: str | None = None,
    entity_filter: str | None = None,
    governorate_filter: str | None = None,
    category_filter: str | None = None,
):
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and ROLE_MAP["manager"] not in roles:
        frappe.throw(_("Only system managers can access the executive dashboard."), frappe.PermissionError)

    executive_filters = _build_executive_filters(
        time_filter=time_filter,
        entity_filter=entity_filter,
        governorate_filter=governorate_filter,
        category_filter=category_filter,
    )

    counts = {
        "total_cases": _count_cases(executive_filters or None),
        "open_cases": _count_cases(_merge_case_filters({"status": ["in", OPEN_STATUS_LIST]}, executive_filters, allow_override=False)),
        "resolved_cases": _count_cases(_merge_case_filters({"status": ["in", CLOSED_STATUS_LIST]}, executive_filters, allow_override=False)),
        "overdue_cases": _count_cases(_merge_case_filters({"status": "Overdue"}, executive_filters, allow_override=False)),
        "high_priority_cases": _count_cases(_merge_case_filters({"priority": ["in", ["High", "Critical"]]}, executive_filters, allow_override=False)),
        "appeal_cases": _count_cases(_merge_case_filters({"case_type": "Appeal"}, executive_filters, allow_override=False)),
        "waiting_citizen_cases": _count_cases(_merge_case_filters({"status": "Waiting Citizen"}, executive_filters, allow_override=False)),
    }

    kpis = {
        "first_response_sla_rate": _get_first_response_sla_rate(executive_filters or None),
        "resolution_sla_rate": _get_resolution_sla_rate(executive_filters or None),
        "avg_satisfaction": _get_average_satisfaction(executive_filters or None),
        "distinct_entities": _get_distinct_field_count("government_entity", executive_filters or None),
        "distinct_governorates": _get_distinct_field_count("citizen_governorate", executive_filters or None),
        "distinct_countries": _get_distinct_field_count("current_country", executive_filters or None),
    }

    summary = {
        "applied_filters": {
            "time_filter": time_filter or "",
            "entity_filter": entity_filter or "",
            "governorate_filter": governorate_filter or "",
            "category_filter": category_filter or "",
        },
        "filter_options": {
            "time_ranges": [
                {"value": "", "label": _("All Time")},
                {"value": "today", "label": _("Today")},
                {"value": "7d", "label": _("Last 7 Days")},
                {"value": "30d", "label": _("Last 30 Days")},
                {"value": "90d", "label": _("Last 90 Days")},
            ],
            "entities": [""] + [row.get("label") for row in _group_case_counts("government_entity", limit=100, exclude_empty=True)],
            "governorates": [""] + [row.get("label") for row in _group_case_counts("citizen_governorate", limit=100, exclude_empty=True)],
            "categories": [""] + [row.get("label") for row in _group_case_counts("category", limit=100, exclude_empty=True)],
        },
        "counts": counts,
        "kpis": kpis,
        "status_breakdown": _group_case_counts("status", filters=executive_filters or None),
        "priority_breakdown": _group_case_counts("priority", filters=executive_filters or None),
        "entity_breakdown": _group_case_counts("government_entity", limit=8, exclude_empty=True, filters=executive_filters or None),
        "governorate_breakdown": _group_case_counts("citizen_governorate", limit=8, exclude_empty=True, filters=executive_filters or None),
        "category_breakdown": _group_case_counts("category", limit=8, exclude_empty=True, filters=executive_filters or None),
        "country_breakdown": _group_case_counts("current_country", limit=8, exclude_empty=True, filters=executive_filters or None),
        "channel_breakdown": _group_case_counts("channel", limit=8, exclude_empty=True, filters=executive_filters or None),
        "monthly_intake_trend": _get_monthly_case_trend(limit=12, filters=executive_filters or None),
        "monthly_closure_trend": _get_monthly_case_trend(limit=12, filters=_merge_case_filters({"status": ["in", CLOSED_STATUS_LIST]}, executive_filters, allow_override=False)),
        "recent_critical_cases": frappe.get_list(
            "Complaint Case",
            filters=_merge_case_filters({"priority": ["in", ["High", "Critical"]], "status": ["in", OPEN_STATUS_LIST]}, executive_filters, allow_override=False),
            fields=["name", "subject", "status", "priority", "government_entity", "target_resolution_date", "modified"],
            order_by="modified desc",
            page_length=10,
        ),
        "top_overdue_entities": _get_top_overdue_entities(filters=executive_filters or None, limit=6),
        "verification_health": _get_verification_health_summary(limit=8),
        "verification_channels": _get_identity_verification_summary(limit=8),
        "ai_health": _get_ai_health_summary(),
        "quick_links": [
            {"label": _("Complaint Cases"), "route": "/app/complaint-case"},
            {"label": _("Complaint Summary Report"), "route": "/app/query-report/Complaint%20Summary"},
            {"label": _("SLA Breaches Report"), "route": "/app/query-report/SLA%20Breaches"},
            {"label": _("Officer Workload Report"), "route": "/app/query-report/Officer%20Workload"},
            {"label": _("Internal Operations Dashboard"), "route": "/app/internal-operations-dashboard"},
            {"label": _("AI Logs"), "route": "/app/complaint-ai-log"},
            {"label": _("Identity Verification Records"), "route": "/app/complaint-identity-verification"},
            {"label": _("Security Events"), "route": "/app/complaint-security-event"},
        ],
    }

    summary["executive_alerts"] = _build_executive_alerts(summary)
    summary["decision_support"] = _build_decision_support(summary)
    return summary


@frappe.whitelist()
def get_security_monitoring_summary(time_filter: str | None = None, severity_filter: str | None = None, status_filter: str | None = None):
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and ROLE_MAP["manager"] not in roles:
        frappe.throw(_("Only system managers can access the security dashboard."), frappe.PermissionError)

    filters = _build_security_filters(time_filter=time_filter, severity_filter=severity_filter, status_filter=status_filter)
    counts = {
        "total_events": _count_security_events(filters or None),
        "blocked_events": _count_security_events(_merge_case_filters({"status": "Blocked"}, filters, allow_override=False)),
        "observed_events": _count_security_events(_merge_case_filters({"status": "Observed"}, filters, allow_override=False)),
        "allowed_events": _count_security_events(_merge_case_filters({"status": "Allowed"}, filters, allow_override=False)),
        "critical_events": _count_security_events(_merge_case_filters({"severity": "Critical"}, filters, allow_override=False)),
        "high_events": _count_security_events(_merge_case_filters({"severity": "High"}, filters, allow_override=False)),
    }

    summary = {
        "applied_filters": {
            "time_filter": time_filter or "",
            "severity_filter": severity_filter or "",
            "status_filter": status_filter or "",
        },
        "filter_options": {
            "time_ranges": [
                {"value": "", "label": _("All Time")},
                {"value": "today", "label": _("Today")},
                {"value": "7d", "label": _("Last 7 Days")},
                {"value": "30d", "label": _("Last 30 Days")},
                {"value": "90d", "label": _("Last 90 Days")},
            ],
            "severities": ["", "Low", "Medium", "High", "Critical"],
            "statuses": ["", "Allowed", "Blocked", "Observed"],
        },
        "counts": counts,
        "event_type_breakdown": _group_security_counts("event_type", filters=filters or None),
        "severity_breakdown": _group_security_counts("severity", filters=filters or None),
        "status_breakdown": _group_security_counts("status", filters=filters or None),
        "endpoint_breakdown": _group_security_counts("endpoint", filters=filters or None, limit=8),
        "ip_breakdown": _group_security_counts("ip_address", filters=filters or None, limit=8, exclude_empty=True),
        "recent_events": frappe.get_list(
            "Complaint Security Event",
            filters=filters or None,
            fields=["name", "event_type", "severity", "status", "endpoint", "identifier", "ip_address", "occurred_on", "message"],
            order_by="occurred_on desc, modified desc",
            page_length=12,
        ),
        "event_trend": _get_security_trend(filters=filters or None, limit=12),
        "top_identifiers": _group_security_counts("identifier", filters=filters or None, limit=8, exclude_empty=True),
        "top_users": _group_security_counts("user", filters=filters or None, limit=8, exclude_empty=True),
        "quick_links": [
            {"label": _("Security Events"), "route": "/app/complaint-security-event"},
            {"label": _("Identity Verification Records"), "route": "/app/complaint-identity-verification"},
            {"label": _("AI Logs"), "route": "/app/complaint-ai-log"},
            {"label": _("Executive Leadership Dashboard"), "route": "/app/executive-leadership-dashboard"},
            {"label": _("Internal Operations Dashboard"), "route": "/app/internal-operations-dashboard"},
        ],
    }
    summary["alerts"] = _build_security_alerts(summary)
    return summary



def _build_executive_filters(
    time_filter: str | None = None,
    entity_filter: str | None = None,
    governorate_filter: str | None = None,
    category_filter: str | None = None,
) -> dict:
    filters = {}
    if entity_filter:
        filters["government_entity"] = entity_filter
    if governorate_filter:
        filters["citizen_governorate"] = governorate_filter
    if category_filter:
        filters["category"] = category_filter
    date_filter = _get_time_range_filter(time_filter)
    if date_filter:
        filters["creation"] = date_filter
    return filters



def _build_security_filters(
    time_filter: str | None = None,
    severity_filter: str | None = None,
    status_filter: str | None = None,
) -> dict:
    filters = {}
    if severity_filter:
        filters["severity"] = severity_filter
    if status_filter:
        filters["status"] = status_filter
    date_filter = _get_time_range_filter(time_filter)
    if date_filter:
        filters["occurred_on"] = date_filter
    return filters



def _build_dashboard_filters(
    status_filter: str | None = None,
    priority_filter: str | None = None,
    entity_filter: str | None = None,
    time_filter: str | None = None,
) -> dict:
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if priority_filter:
        filters["priority"] = priority_filter
    if entity_filter:
        filters["government_entity"] = entity_filter

    date_filter = _get_time_range_filter(time_filter)
    if date_filter:
        filters["creation"] = date_filter
    return filters



def _merge_case_filters(base_filters: dict | None = None, extra_filters: dict | None = None, allow_override: bool = True) -> dict:
    filters = dict(base_filters or {})
    for key, value in (extra_filters or {}).items():
        if key in filters and not allow_override:
            continue
        filters[key] = value
    return filters



def _get_time_range_filter(time_filter: str | None = None):
    if not time_filter:
        return None
    if time_filter == "today":
        return [">=", today()]
    if time_filter == "7d":
        return [">=", add_days(today(), -7)]
    if time_filter == "30d":
        return [">=", add_days(today(), -30)]
    if time_filter == "90d":
        return [">=", add_days(today(), -90)]
    return None



def _count_cases(filters: dict | None = None, or_filters: list | None = None) -> int:
    rows = frappe.get_list(
        "Complaint Case",
        filters=filters,
        or_filters=or_filters,
        fields=["count(name) as total"],
        page_length=1,
    )
    return int((rows[0].get("total") if rows else 0) or 0)



def _count_security_events(filters: dict | None = None) -> int:
    if not frappe.db.exists("DocType", "Complaint Security Event"):
        return 0
    rows = frappe.get_list(
        "Complaint Security Event",
        filters=filters,
        fields=["count(name) as total"],
        page_length=1,
    )
    return int((rows[0].get("total") if rows else 0) or 0)



def _group_case_counts(fieldname: str, limit: int = 8, exclude_empty: bool = False, filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=filters,
        fields=[fieldname, "count(name) as total"],
        group_by=fieldname,
        order_by="total desc",
        page_length=limit,
    )
    output = []
    for row in rows:
        label = row.get(fieldname)
        if exclude_empty and not label:
            continue
        output.append({"label": label or _("Unspecified"), "count": int(row.get("total") or 0)})
    return output[:limit]



def _group_security_counts(fieldname: str, limit: int = 8, exclude_empty: bool = False, filters: dict | None = None):
    if not frappe.db.exists("DocType", "Complaint Security Event"):
        return []
    rows = frappe.get_list(
        "Complaint Security Event",
        filters=filters,
        fields=[fieldname, "count(name) as total"],
        group_by=fieldname,
        order_by="total desc",
        page_length=limit,
    )
    output = []
    for row in rows:
        label = row.get(fieldname)
        if exclude_empty and not label:
            continue
        output.append({"label": label or _("Unspecified"), "count": int(row.get("total") or 0)})
    return output[:limit]



def _get_monthly_case_trend(limit: int = 6, filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=filters,
        fields=["creation"],
        order_by="creation desc",
        page_length=5000,
    )
    month_counts = {}
    for row in rows:
        month_key = frappe.utils.getdate(row.creation).strftime("%Y-%m")
        month_counts[month_key] = month_counts.get(month_key, 0) + 1
    sorted_items = sorted(month_counts.items())[-limit:]
    return [{"label": key, "count": count} for key, count in sorted_items]



def _get_identity_verification_summary(limit: int = 4):
    if not frappe.db.exists("DocType", "Complaint Identity Verification"):
        return []
    rows = frappe.get_list(
        "Complaint Identity Verification",
        fields=["channel", "count(name) as total"],
        group_by="channel",
        order_by="total desc",
        page_length=limit,
    )
    return [{"label": row.get("channel") or _("Unknown"), "count": int(row.get("total") or 0)} for row in rows]



def _get_verification_health_summary(limit: int = 6):
    if not frappe.db.exists("DocType", "Complaint Identity Verification"):
        return []
    rows = frappe.get_list(
        "Complaint Identity Verification",
        fields=["status", "count(name) as total"],
        group_by="status",
        order_by="total desc",
        page_length=limit,
    )
    return [{"label": row.get("status") or _("Unknown"), "count": int(row.get("total") or 0)} for row in rows]



def _get_average_satisfaction(filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=filters,
        fields=["avg(satisfaction_score) as avg_score"],
        page_length=1,
    )
    return round(float((rows[0].get("avg_score") if rows else 0) or 0), 2)



def _get_distinct_field_count(fieldname: str, filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=filters,
        fields=[fieldname],
        page_length=5000,
    )
    values = {row.get(fieldname) for row in rows if row.get(fieldname)}
    return len(values)



def _get_first_response_sla_rate(filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=_merge_case_filters({"target_response_on": ["is", "set"]}, filters, allow_override=False),
        fields=["target_response_on", "first_response_on"],
        page_length=5000,
    )
    eligible = [row for row in rows if row.get("first_response_on")]
    if not eligible:
        return 0
    on_time = 0
    for row in eligible:
        if row.first_response_on and row.target_response_on and row.first_response_on <= row.target_response_on:
            on_time += 1
    return round((on_time / len(eligible)) * 100, 2)



def _get_resolution_sla_rate(filters: dict | None = None):
    rows = frappe.get_list(
        "Complaint Case",
        filters=_merge_case_filters({"target_resolution_date": ["is", "set"], "status": ["in", CLOSED_STATUS_LIST]}, filters, allow_override=False),
        fields=["target_resolution_date", "resolved_on"],
        page_length=5000,
    )
    eligible = [row for row in rows if row.get("resolved_on")]
    if not eligible:
        return 0
    on_time = 0
    for row in eligible:
        if row.resolved_on and row.target_resolution_date and getdate(row.resolved_on) <= getdate(row.target_resolution_date):
            on_time += 1
    return round((on_time / len(eligible)) * 100, 2)



def _get_ai_activity_summary(limit: int = 6):
    if not frappe.db.exists("DocType", "Complaint AI Log"):
        return []
    rows = frappe.get_list(
        "Complaint AI Log",
        fields=["provider", "action_label", "status", "reference_name", "executed_on"],
        order_by="executed_on desc, modified desc",
        page_length=limit,
    )
    return rows



def _get_ai_health_summary():
    if not frappe.db.exists("DocType", "Complaint AI Log"):
        return {"success": 0, "error": 0, "success_rate": 0}

    success_rows = frappe.get_list("Complaint AI Log", filters={"status": "Success"}, fields=["count(name) as total"], page_length=1)
    error_rows = frappe.get_list("Complaint AI Log", filters={"status": "Error"}, fields=["count(name) as total"], page_length=1)
    success = int((success_rows[0].get("total") if success_rows else 0) or 0)
    error = int((error_rows[0].get("total") if error_rows else 0) or 0)
    total = success + error
    return {
        "success": success,
        "error": error,
        "success_rate": round((success / total) * 100, 2) if total else 0,
    }



def _get_top_officers(filters: dict | None = None, limit: int = 6):
    rows = frappe.get_list(
        "Complaint Case",
        filters=_merge_case_filters({"status": ["in", OPEN_STATUS_LIST]}, filters, allow_override=False),
        fields=["advisor_user", "agency_officer_user", "follow_up_user"],
        page_length=5000,
    )
    counters = {}
    for row in rows:
        for fieldname, label in [
            ("advisor_user", _("Advisor")),
            ("agency_officer_user", _("Agency Officer")),
            ("follow_up_user", _("Follow-up Officer")),
        ]:
            user = row.get(fieldname)
            if not user:
                continue
            key = (user, label)
            counters[key] = counters.get(key, 0) + 1
    output = [
        {"user": key[0], "role_label": key[1], "count": value}
        for key, value in sorted(counters.items(), key=lambda item: item[1], reverse=True)
    ]
    return output[:limit]



def _get_sla_health_summary(filters: dict | None = None):
    overdue_count = _count_cases(_merge_case_filters({"status": "Overdue"}, filters, allow_override=False))
    open_count = _count_cases(_merge_case_filters({"status": ["in", OPEN_STATUS_LIST]}, filters, allow_override=False))
    resolved_count = _count_cases(_merge_case_filters({"status": ["in", CLOSED_STATUS_LIST]}, filters, allow_override=False))

    if frappe.db.exists("DocType", "Complaint AI Log"):
        ai_success = frappe.get_list(
            "Complaint AI Log",
            filters={"status": "Success"},
            fields=["count(name) as total"],
            page_length=1,
        )
        ai_error = frappe.get_list(
            "Complaint AI Log",
            filters={"status": "Error"},
            fields=["count(name) as total"],
            page_length=1,
        )
        ai_success_total = int((ai_success[0].get("total") if ai_success else 0) or 0)
        ai_error_total = int((ai_error[0].get("total") if ai_error else 0) or 0)
    else:
        ai_success_total = 0
        ai_error_total = 0

    return {
        "open_cases": open_count,
        "overdue_cases": overdue_count,
        "resolved_cases": resolved_count,
        "sla_risk_ratio": round((overdue_count / open_count) * 100, 2) if open_count else 0,
        "ai_success": ai_success_total,
        "ai_error": ai_error_total,
    }



def _get_top_overdue_entities(filters: dict | None = None, limit: int = 5):
    rows = _group_case_counts(
        "government_entity",
        limit=limit,
        exclude_empty=True,
        filters=_merge_case_filters({"status": "Overdue"}, filters, allow_override=False),
    )
    return rows



def _get_security_trend(filters: dict | None = None, limit: int = 12):
    if not frappe.db.exists("DocType", "Complaint Security Event"):
        return []
    rows = frappe.get_list(
        "Complaint Security Event",
        filters=filters,
        fields=["occurred_on"],
        order_by="occurred_on desc",
        page_length=5000,
    )
    day_counts = {}
    for row in rows:
        if not row.get("occurred_on"):
            continue
        day_key = getdate(row.occurred_on).strftime("%Y-%m-%d")
        day_counts[day_key] = day_counts.get(day_key, 0) + 1
    sorted_items = sorted(day_counts.items())[-limit:]
    return [{"label": key, "count": count} for key, count in sorted_items]



def _build_executive_summary(summary: dict):
    counts = summary.get("counts", {})
    sla_health = summary.get("sla_health", {})
    verification_health = summary.get("verification_health", [])
    verification_total = sum(row.get("count", 0) for row in verification_health)
    ai_total = (sla_health.get("ai_success", 0) or 0) + (sla_health.get("ai_error", 0) or 0)
    ai_success_rate = round(((sla_health.get("ai_success", 0) or 0) / ai_total) * 100, 2) if ai_total else 0
    return {
        "open_cases": counts.get("open_cases", 0),
        "overdue_cases": counts.get("overdue_cases", counts.get("overdue", 0)),
        "high_priority_cases": counts.get("high_priority_cases", counts.get("high_priority", 0)),
        "verification_total": verification_total,
        "ai_total": ai_total,
        "ai_success_rate": ai_success_rate,
    }



def _build_action_center(summary: dict):
    actions = []
    counts = summary.get("counts", {})
    top_entities = summary.get("top_overdue_entities", [])
    if counts.get("new_cases", 0) > 0:
        actions.append({
            "label": _("Review new intake cases"),
            "count": counts.get("new_cases", 0),
            "route": "/app/complaint-case",
            "severity": "gold",
            "description": _("There are fresh cases waiting for intake review and triage."),
        })
    if counts.get("overdue", 0) > 0:
        actions.append({
            "label": _("Investigate overdue cases"),
            "count": counts.get("overdue", 0),
            "route": "/app/query-report/SLA%20Breaches",
            "severity": "red",
            "description": _("Overdue cases require escalation or immediate follow-up.") + (f" ({top_entities[0]['label']})" if top_entities else ""),
        })
    if counts.get("waiting_citizen", 0) > 0:
        actions.append({
            "label": _("Follow up waiting citizen cases"),
            "count": counts.get("waiting_citizen", 0),
            "route": "/app/complaint-case",
            "severity": "orange",
            "description": _("Cases in waiting-citizen state may need reminders or closure decisions."),
        })
    if summary.get("sla_health", {}).get("ai_error", 0) > 0:
        actions.append({
            "label": _("Review AI failures"),
            "count": summary.get("sla_health", {}).get("ai_error", 0),
            "route": "/app/complaint-ai-log",
            "severity": "purple",
            "description": _("Some AI operations failed and may need prompt, model, or provider review."),
        })
    if not actions:
        actions.append({
            "label": _("Operations stable"),
            "count": 0,
            "route": "/app/internal-operations-dashboard",
            "severity": "green",
            "description": _("No immediate operational action is required right now."),
        })
    return actions



def _build_decision_support(summary: dict):
    counts = summary.get("counts", {})
    kpis = summary.get("kpis", {})
    insights = []
    if counts.get("overdue_cases", 0) > 0:
        insights.append(_("Focus on overdue cases first to improve SLA performance and reduce escalation risk."))
    if kpis.get("resolution_sla_rate", 0) < 70:
        insights.append(_("Resolution SLA rate is below target and may require operational escalation or rebalancing workloads."))
    if kpis.get("first_response_sla_rate", 0) < 75:
        insights.append(_("First-response SLA performance needs attention; intake or routing may be slowing down response time."))
    if kpis.get("avg_satisfaction", 0) and kpis.get("avg_satisfaction", 0) < 3:
        insights.append(_("Citizen satisfaction appears low; review service quality and closure communications."))
    if not insights:
        insights.append(_("Core leadership indicators are stable within the current dashboard scope."))
    return insights



def _build_executive_alerts(summary: dict):
    alerts = []
    counts = summary.get("counts", {})
    kpis = summary.get("kpis", {})
    top_entities = summary.get("top_overdue_entities", [])
    ai_health = summary.get("ai_health", {})

    if counts.get("overdue_cases", 0) > 0:
        alerts.append({
            "severity": "red",
            "title": _("Overdue operational backlog detected"),
            "description": _("There are {0} overdue cases in the current scope.").format(counts.get("overdue_cases", 0)) + (f" {_('Top affected entity')}: {top_entities[0]['label']}" if top_entities else ""),
            "route": "/app/query-report/SLA%20Breaches",
        })
    if counts.get("high_priority_cases", 0) > 0:
        alerts.append({
            "severity": "orange",
            "title": _("High-priority cases require leadership visibility"),
            "description": _("There are {0} high-priority cases still in the active pipeline.").format(counts.get("high_priority_cases", 0)),
            "route": "/app/complaint-case",
        })
    if kpis.get("resolution_sla_rate", 0) < 70 and counts.get("resolved_cases", 0) > 0:
        alerts.append({
            "severity": "purple",
            "title": _("Resolution SLA below expected threshold"),
            "description": _("Current resolution SLA rate is {0}% within the selected scope.").format(kpis.get("resolution_sla_rate", 0)),
            "route": "/app/query-report/Complaint%20Summary",
        })
    if ai_health.get("error", 0) > 0:
        alerts.append({
            "severity": "purple",
            "title": _("AI operational exceptions detected"),
            "description": _("There are {0} AI failures that may require technical review.").format(ai_health.get("error", 0)),
            "route": "/app/complaint-ai-log",
        })
    if not alerts:
        alerts.append({
            "severity": "green",
            "title": _("Leadership dashboard stable"),
            "description": _("No critical executive alerts were detected in the selected scope."),
            "route": "/app/executive-leadership-dashboard",
        })
    return alerts



def _build_security_alerts(summary: dict):
    alerts = []
    counts = summary.get("counts", {})
    top_ips = summary.get("ip_breakdown", [])

    if counts.get("critical_events", 0) > 0:
        alerts.append({
            "severity": "red",
            "title": _("Critical security events detected"),
            "description": _("There are {0} critical security events in the selected scope.").format(counts.get("critical_events", 0)),
            "route": "/app/complaint-security-event",
        })
    if counts.get("blocked_events", 0) > 0:
        ip_hint = f" — {_('Top IP')}: {top_ips[0]['label']}" if top_ips else ""
        alerts.append({
            "severity": "orange",
            "title": _("Blocked requests observed"),
            "description": _("There are {0} blocked security events.").format(counts.get("blocked_events", 0)) + ip_hint,
            "route": "/app/complaint-security-event",
        })
    if not alerts:
        alerts.append({
            "severity": "green",
            "title": _("Security posture stable"),
            "description": _("No critical or blocked security alerts were detected in the selected scope."),
            "route": "/app/security-monitoring-dashboard",
        })
    return alerts



def _build_alert_center(summary: dict):
    alerts = []
    counts = summary.get("counts", {})
    sla_health = summary.get("sla_health", {})
    top_entities = summary.get("top_overdue_entities", [])

    if counts.get("overdue", 0) > 0:
        entity_hint = f" — الأعلى: {top_entities[0]['label']}" if top_entities else ""
        alerts.append({
            "severity": "red",
            "title": _("Overdue cases require immediate follow-up"),
            "description": _("There are {0} overdue cases currently visible to this user").format(counts.get("overdue", 0)) + entity_hint,
            "route": "/app/query-report/SLA%20Breaches",
        })

    if counts.get("high_priority", 0) > 0:
        alerts.append({
            "severity": "orange",
            "title": _("High-priority cases need attention"),
            "description": _("There are {0} high-priority open or visible cases").format(counts.get("high_priority", 0)),
            "route": "/app/complaint-case",
        })

    if sla_health.get("ai_error", 0) > 0:
        alerts.append({
            "severity": "purple",
            "title": _("AI processing errors detected"),
            "description": _("Recent AI logs contain {0} failed operations").format(sla_health.get("ai_error", 0)),
            "route": "/app/complaint-ai-log",
        })

    if not alerts:
        alerts.append({
            "severity": "green",
            "title": _("Operations are stable"),
            "description": _("No urgent alerts were detected in the current dashboard scope."),
            "route": "/app/internal-operations-dashboard",
        })

    return alerts



def _can_access_case(doc) -> bool:
    if frappe.session.user == "Guest":
        return False

    if frappe.session.user == doc.citizen_user:
        return True

    user_email = frappe.db.get_value("User", frappe.session.user, "email")
    return bool(user_email and user_email == doc.email)



def _can_access_case_as_staff(doc) -> bool:
    if frappe.session.user == "Guest":
        return False

    roles = set(frappe.get_roles())
    staff_roles = {ROLE_MAP["advisor"], ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]}
    if not roles.intersection(staff_roles) and frappe.session.user != "Administrator":
        return False

    return frappe.has_permission("Complaint Case", "read", doc=doc)
