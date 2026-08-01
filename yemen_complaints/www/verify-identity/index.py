from __future__ import annotations

import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "Identity Verification"
    context.channel = frappe.form_dict.get("channel")
    context.email = frappe.form_dict.get("email")
    context.mobile = frappe.form_dict.get("mobile")
    context.telegram_id = frappe.form_dict.get("telegram_id")
    context.full_name = frappe.form_dict.get("full_name")
    context.return_to = frappe.form_dict.get("return_to")
    return context
