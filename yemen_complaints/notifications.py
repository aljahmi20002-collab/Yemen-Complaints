from __future__ import annotations

import frappe

from yemen_complaints.messaging import make_plain_text, render_email_template, send_citizen_notification, send_user_notification

ASSIGNMENT_FIELDS = {
    "advisor_user": "المستشار",
    "agency_officer_user": "موظف الجهة",
    "follow_up_user": "المتابع",
}

TERMINAL_STATUSES = {"Resolved", "Rejected", "Closed"}



def after_insert_complaint_case(doc, method=None):
    bind_citizen_user_by_email(doc)
    send_citizen_receipt(doc)
    for fieldname, role_label in ASSIGNMENT_FIELDS.items():
        if doc.get(fieldname):
            send_assignment_notification(doc, doc.get(fieldname), role_label, is_new_case=True)



def on_update_complaint_case(doc, method=None):
    previous = doc.get_doc_before_save()
    ensure_first_response_timestamp(doc)

    if not previous:
        return

    for fieldname, role_label in ASSIGNMENT_FIELDS.items():
        old_value = previous.get(fieldname)
        new_value = doc.get(fieldname)
        if new_value and new_value != old_value:
            send_assignment_notification(doc, new_value, role_label, previous_assignee=old_value)

    latest_public_update = get_latest_public_update_if_new(doc, previous)
    status_changed = previous.status != doc.status

    if status_changed:
        send_citizen_status_update(doc, previous.status)

    if latest_public_update and doc.status not in TERMINAL_STATUSES:
        send_citizen_public_update(doc, latest_public_update)



def bind_citizen_user_by_email(doc):
    if doc.citizen_user or not doc.email:
        return

    user = frappe.db.get_value("User", {"email": doc.email}, "name")
    if user:
        doc.db_set("citizen_user", user, update_modified=False)
        doc.citizen_user = user



def ensure_first_response_timestamp(doc):
    if doc.first_response_on:
        return

    for row in sorted(doc.get("updates") or [], key=lambda d: d.posted_on or d.creation or ""):
        if row.visibility == "Public" and row.update_type != "Citizen Note":
            doc.db_set("first_response_on", row.posted_on, update_modified=False)
            doc.first_response_on = row.posted_on
            return



def get_latest_public_update_if_new(doc, previous):
    current_updates = doc.get("updates") or []
    previous_count = len(previous.get("updates") or [])
    if len(current_updates) <= previous_count:
        return None

    latest = current_updates[-1]
    if latest.visibility != "Public":
        return None
    if latest.update_type == "Citizen Note":
        return None
    return latest



def send_citizen_receipt(doc):
    subject = f"تم استلام طلبك - {doc.name}"
    message = render_email_template(
        "citizen_receipt.html",
        {
            "doc": doc,
            "tracking_url": f"/track-complaint?case_id={doc.name}",
        },
    )
    send_citizen_notification(
        doc,
        subject=subject,
        html_message=message,
        text_message=f"تم استلام طلبك {doc.name} بعنوان {doc.subject}. يمكنك متابعة الحالة عبر المنصة.",
        event_key="citizen_receipt",
    )



def send_assignment_notification(doc, recipient, role_label, previous_assignee=None, is_new_case=False):
    if not recipient or recipient == "Guest":
        return

    subject = f"إحالة حالة جديدة: {doc.name}"
    message = render_email_template(
        "assignment_notification.html",
        {
            "doc": doc,
            "role_label": role_label,
            "previous_assignee": previous_assignee,
            "is_new_case": is_new_case,
        },
    )
    send_user_notification(
        recipient,
        subject=subject,
        html_message=message,
        text_message=f"تم إسناد الحالة {doc.name} إليك بصفتك {role_label}. الموضوع: {doc.subject}.",
        event_key="assignment_notification",
    )



def send_citizen_status_update(doc, previous_status):
    subject = f"تحديث حالة الطلب {doc.name}: {doc.status}"
    message = render_email_template(
        "citizen_status_update.html",
        {
            "doc": doc,
            "previous_status": previous_status,
        },
    )
    send_citizen_notification(
        doc,
        subject=subject,
        html_message=message,
        text_message=f"تم تحديث حالة طلبك {doc.name} من {previous_status} إلى {doc.status}.",
        event_key="citizen_status_update",
    )



def send_citizen_public_update(doc, update_row):
    subject = f"تحديث جديد على الطلب {doc.name}"
    message = render_email_template(
        "citizen_public_update.html",
        {
            "doc": doc,
            "update_row": update_row,
        },
    )
    send_citizen_notification(
        doc,
        subject=subject,
        html_message=message,
        text_message=f"ورد تحديث جديد على طلبك {doc.name}: {make_plain_text(update_row.message)[:140]}",
        event_key="citizen_public_update",
    )
