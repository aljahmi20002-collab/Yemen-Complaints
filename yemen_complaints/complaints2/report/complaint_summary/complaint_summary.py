from __future__ import annotations

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = []
    values = {}

    if filters.from_date:
        conditions.append("creation >= %(from_date)s")
        values["from_date"] = filters.from_date
    if filters.to_date:
        conditions.append("creation <= %(to_date)s")
        values["to_date"] = filters.to_date
    if filters.case_type:
        conditions.append("case_type = %(case_type)s")
        values["case_type"] = filters.case_type
    if filters.government_entity:
        conditions.append("government_entity = %(government_entity)s")
        values["government_entity"] = filters.government_entity

    where_clause = " where " + " and ".join(conditions) if conditions else ""
    data = frappe.db.sql(
        f"""
        select
            coalesce(government_entity, '—') as government_entity,
            status,
            priority,
            count(*) as total_cases,
            sum(case when is_overdue = 1 then 1 else 0 end) as overdue_cases,
            sum(case when status in ('Resolved', 'Closed') then 1 else 0 end) as resolved_cases,
            round(avg(case when resolved_on is not null then datediff(date(resolved_on), date(creation)) end), 2) as avg_resolution_days
        from `tabComplaint Case`
        {where_clause}
        group by government_entity, status, priority
        order by total_cases desc, government_entity asc
        """,
        values,
        as_dict=True,
    )

    columns = [
        {"label": _("Government Entity"), "fieldname": "government_entity", "fieldtype": "Data", "width": 240},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
        {"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 110},
        {"label": _("Total Cases"), "fieldname": "total_cases", "fieldtype": "Int", "width": 120},
        {"label": _("Overdue Cases"), "fieldname": "overdue_cases", "fieldtype": "Int", "width": 130},
        {"label": _("Resolved Cases"), "fieldname": "resolved_cases", "fieldtype": "Int", "width": 130},
        {"label": _("Avg Resolution Days"), "fieldname": "avg_resolution_days", "fieldtype": "Float", "width": 150},
    ]

    status_counts = frappe.db.sql(
        f"""
        select status, count(*) as total
        from `tabComplaint Case`
        {where_clause}
        group by status
        order by total desc
        """,
        values,
        as_dict=True,
    )

    chart = {
        "data": {
            "labels": [d.status for d in status_counts],
            "datasets": [{"name": _("Cases"), "values": [d.total for d in status_counts]}],
        },
        "type": "donut",
    }

    total_cases = sum((row.total_cases or 0) for row in data)
    overdue_cases = sum((row.overdue_cases or 0) for row in data)
    resolved_cases = sum((row.resolved_cases or 0) for row in data)
    summary = [
        {"label": _("Total Cases"), "value": total_cases, "indicator": "Blue"},
        {"label": _("Overdue Cases"), "value": overdue_cases, "indicator": "Red"},
        {"label": _("Resolved Cases"), "value": resolved_cases, "indicator": "Green"},
    ]

    return columns, data, None, chart, summary
