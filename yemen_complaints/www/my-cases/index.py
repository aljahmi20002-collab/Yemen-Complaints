from __future__ import annotations

import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "My Cases"
    context.is_guest = frappe.session.user == "Guest"
    context.user = frappe.session.user
    context.cases = []
    context.summary = {
        "total": 0,
        "open": 0,
        "resolved": 0,
        "overdue": 0,
    }

    if context.is_guest:
        return context

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
            "resolution_summary",
        ],
        order_by="modified desc",
    )

    context.cases = rows
    context.summary = {
        "total": len(rows),
        "open": len([r for r in rows if r.status not in ["Resolved", "Rejected", "Closed"]]),
        "resolved": len([r for r in rows if r.status in ["Resolved", "Closed"]]),
        "overdue": len([r for r in rows if r.status == "Overdue"]),
    }
    return context
