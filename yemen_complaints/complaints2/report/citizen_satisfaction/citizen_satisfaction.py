from __future__ import annotations

import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    field = "category" if (filters.group_by or "Category") == "Category" else "government_entity"
    label = _("Category") if field == "category" else _("Government Entity")

    data = frappe.db.sql(
        f"""
        select
            coalesce({field}, '—') as grouping_label,
            count(*) as total_cases,
            sum(case when status in ('Resolved', 'Closed') then 1 else 0 end) as resolved_cases,
            round(avg(case when satisfaction_score > 0 then satisfaction_score end), 2) as avg_satisfaction,
            round(avg(case when resolved_on is not null then datediff(date(resolved_on), date(creation)) end), 2) as avg_resolution_days
        from `tabComplaint Case`
        group by {field}
        order by avg_satisfaction desc, resolved_cases desc
        """,
        as_dict=True,
    )

    columns = [
        {"label": label, "fieldname": "grouping_label", "fieldtype": "Data", "width": 240},
        {"label": _("Total Cases"), "fieldname": "total_cases", "fieldtype": "Int", "width": 120},
        {"label": _("Resolved Cases"), "fieldname": "resolved_cases", "fieldtype": "Int", "width": 130},
        {"label": _("Avg Satisfaction"), "fieldname": "avg_satisfaction", "fieldtype": "Float", "width": 130},
        {"label": _("Avg Resolution Days"), "fieldname": "avg_resolution_days", "fieldtype": "Float", "width": 150},
    ]

    chart = {
        "data": {
            "labels": [r.grouping_label for r in data[:10]],
            "datasets": [{"name": _("Average Satisfaction"), "values": [r.avg_satisfaction or 0 for r in data[:10]]}],
        },
        "type": "line",
    }

    return columns, data, None, chart, []
