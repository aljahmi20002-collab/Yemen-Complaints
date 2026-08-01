from __future__ import annotations

import frappe
from frappe import _


FIELD_MAP = {
    "Advisor": "advisor_user",
    "Agency Officer": "agency_officer_user",
    "Follow-up Officer": "follow_up_user",
}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    role_dimension = filters.role_dimension or "Advisor"
    target_field = FIELD_MAP[role_dimension]

    rows = frappe.db.sql(
        f"""
        select
            {target_field} as responsible_user,
            count(*) as total_cases,
            sum(case when status in ('New', 'Under Review', 'Assigned', 'In Progress', 'Waiting Citizen', 'Overdue') then 1 else 0 end) as open_cases,
            sum(case when status = 'Overdue' then 1 else 0 end) as overdue_cases,
            sum(case when status in ('Resolved', 'Closed') then 1 else 0 end) as resolved_cases
        from `tabComplaint Case`
        where ifnull({target_field}, '') != ''
        group by {target_field}
        order by open_cases desc, overdue_cases desc
        """,
        as_dict=True,
    )

    columns = [
        {"label": _("Responsible User"), "fieldname": "responsible_user", "fieldtype": "Link", "options": "User", "width": 220},
        {"label": _("Total Cases"), "fieldname": "total_cases", "fieldtype": "Int", "width": 120},
        {"label": _("Open Cases"), "fieldname": "open_cases", "fieldtype": "Int", "width": 120},
        {"label": _("Overdue Cases"), "fieldname": "overdue_cases", "fieldtype": "Int", "width": 120},
        {"label": _("Resolved Cases"), "fieldname": "resolved_cases", "fieldtype": "Int", "width": 130},
    ]

    chart = {
        "data": {
            "labels": [r.responsible_user for r in rows[:12]],
            "datasets": [
                {"name": _("Open Cases"), "values": [r.open_cases for r in rows[:12]]},
                {"name": _("Overdue Cases"), "values": [r.overdue_cases for r in rows[:12]]},
            ],
        },
        "type": "bar",
    }

    return columns, rows, None, chart, []
