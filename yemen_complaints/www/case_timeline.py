from __future__ import annotations

import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "الخط الزمني للحالة"
    context.case_id = frappe.form_dict.get("case_id")
    context.is_guest = frappe.session.user == "Guest"
    return context
