from __future__ import annotations

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = ["status not in ('Resolved', 'Rejected', 'Closed')", "target_resolution_date is not null"]
    values = {}

    if filters.government_entity:
        conditions.append("government_entity = %(government_entity)s")
        values["government_entity"] = filters.government_entity
    if filters.priority:
        conditions.append("priority = %(priority)s")
        values["priority"] = filters.priority
    if filters.status:
        conditions.append("status = %(status)s")
        values["status"] = filters.status

    data = frappe.db.sql(
        f"""
        select
            name,
            subject,
            citizen_full_name,
            government_entity,
            priority,
            status,
            target_response_on,
            target_resolution_date,
            datediff(curdate(), target_resolution_date) as days_overdue,
            advisor_user,
            agency_officer_user,
            follow_up_user
        from `tabComplaint Case`
        where {' and '.join(conditions)}
          and target_resolution_date < curdate()
        order by days_overdue desc, priority desc
        """,
        values,
        as_dict=True,
    )

    columns = [
        {"label": _("Case ID"), "fieldname": "name", "fieldtype": "Link", "options": "Complaint Case", "width": 150},
        {"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
        {"label": _("Citizen"), "fieldname": "citizen_full_name", "fieldtype": "Data", "width": 180},
        {"label": _("Government Entity"), "fieldname": "government_entity", "fieldtype": "Link", "options": "Government Entity", "width": 220},
        {"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 110},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": _("Target Response"), "fieldname": "target_response_on", "fieldtype": "Datetime", "width": 160},
        {"label": _("Target Resolution"), "fieldname": "target_resolution_date", "fieldtype": "Date", "width": 140},
        {"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 120},
        {"label": _("Advisor"), "fieldname": "advisor_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": _("Agency Officer"), "fieldname": "agency_officer_user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": _("Follow-up"), "fieldname": "follow_up_user", "fieldtype": "Link", "options": "User", "width": 180}
    ]

    chart = {
        "data": {
            "labels": [row.name for row in data[:10]],
            "datasets": [{"name": _("Days Overdue"), "values": [row.days_overdue for row in data[:10]]}]
        },
        "type": "bar"
    }

    summary = [
        {"label": _("Breached Cases"), "value": len(data), "indicator": "Red"},
        {"label": _("Avg Days Overdue"), "value": round(sum([d.days_overdue for d in data]) / len(data), 2) if data else 0, "indicator": "Orange"}
    ]

    return columns, data, None, chart, summary
