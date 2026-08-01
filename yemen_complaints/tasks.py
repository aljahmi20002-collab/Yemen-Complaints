from __future__ import annotations

import frappe
from frappe.utils import add_days, date_diff, today

from yemen_complaints.messaging import render_email_template, send_user_notification
from yemen_complaints.utils import OPEN_STATUSES, ROLE_MAP



def update_overdue_cases():
    open_cases = frappe.get_all(
        "Complaint Case",
        filters={
            "status": ["in", list(OPEN_STATUSES)],
            "target_resolution_date": ["<", today()],
        },
        fields=["name", "status", "is_overdue"],
    )

    for row in open_cases:
        values = {"is_overdue": 1}
        if row.status != "Overdue":
            values["status"] = "Overdue"
        frappe.db.set_value("Complaint Case", row.name, values, update_modified=False)



def send_sla_reminders():
    soon = add_days(today(), 1)
    due_cases = frappe.get_all(
        "Complaint Case",
        filters={
            "status": ["in", list(OPEN_STATUSES)],
            "target_resolution_date": ["<=", soon],
        },
        fields=[
            "name",
            "subject",
            "priority",
            "status",
            "target_resolution_date",
            "government_entity",
            "advisor_user",
            "agency_officer_user",
            "follow_up_user",
        ],
    )

    for case in due_cases:
        recipients = collect_case_recipients(case)
        if not recipients:
            continue

        doc = frappe.get_doc("Complaint Case", case.name)
        days_overdue = date_diff(today(), case.target_resolution_date) if case.target_resolution_date and date_diff(today(), case.target_resolution_date) > 0 else None
        message = render_email_template("sla_escalation.html", {"doc": doc, "days_overdue": days_overdue})
        subject = f"[SLA] {case.name} - {case.status}"
        text_message = f"تنبيه SLA للحالة {case.name} بعنوان {case.subject}. الحالة الحالية: {case.status}."
        for recipient in recipients:
            send_user_notification(
                recipient,
                subject=subject,
                html_message=message,
                text_message=text_message,
                event_key="sla_escalation",
            )



def collect_case_recipients(case) -> list[str]:
    recipients: list[str] = []
    for user in [case.advisor_user, case.agency_officer_user, case.follow_up_user]:
        if user and user != "Guest" and user not in recipients:
            recipients.append(user)

    if case.government_entity:
        escalation_user = frappe.db.get_value("Government Entity", case.government_entity, "escalation_user")
        if escalation_user and escalation_user != "Guest" and escalation_user not in recipients:
            recipients.append(escalation_user)

    manager_users = frappe.get_all(
        "Has Role",
        filters={"role": ROLE_MAP["manager"], "parenttype": "User"},
        pluck="parent",
    )
    for user in manager_users:
        if user and user != "Guest" and user not in recipients:
            recipients.append(user)

    return recipients
