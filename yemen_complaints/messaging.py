from __future__ import annotations

from pathlib import Path

import frappe
import requests
from frappe import _
from frappe.utils import cstr, strip_html

ROOT = Path(__file__).resolve().parent
EMAIL_DIR = ROOT / "templates" / "emails"


def get_notification_settings():
    if not frappe.db.exists("DocType", "Complaint Notification Settings"):
        return None
    try:
        return frappe.get_single("Complaint Notification Settings")
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Unable to load Complaint Notification Settings"))
        return None


def render_email_template(template_name: str, context: dict) -> str:
    template = (EMAIL_DIR / template_name).read_text(encoding="utf-8")
    return frappe.render_template(template, context)


def send_citizen_notification(
    doc,
    *,
    subject: str,
    html_message: str,
    text_message: str,
    event_key: str = "general",
):
    settings = get_notification_settings()

    if doc.email and is_email_enabled(settings):
        safe_send_email([doc.email], subject, html_message)

    if doc.mobile_number and settings and settings.enable_sms and settings.allow_citizen_sms:
        safe_send_sms(
            to=normalize_mobile(doc.mobile_number, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key=event_key,
        )

    if doc.mobile_number and settings and settings.enable_whatsapp and settings.allow_citizen_whatsapp:
        safe_send_whatsapp(
            to=normalize_mobile(doc.mobile_number, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key=event_key,
        )

    if getattr(doc, "telegram_id", None) and settings and settings.enable_telegram and settings.allow_citizen_telegram:
        safe_send_telegram(
            to=doc.telegram_id,
            message=text_message,
            settings=settings,
            event_key=event_key,
        )


def send_user_notification(
    user: str,
    *,
    subject: str,
    html_message: str,
    text_message: str,
    event_key: str = "staff",
):
    if not user or user == "Guest":
        return

    settings = get_notification_settings()
    user_email, mobile = frappe.db.get_value("User", user, ["email", "mobile_no"])

    if user_email and is_email_enabled(settings):
        safe_send_email([user_email], subject, html_message)

    if mobile and settings and settings.enable_sms and settings.allow_staff_sms:
        safe_send_sms(
            to=normalize_mobile(mobile, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key=event_key,
        )

    if mobile and settings and settings.enable_whatsapp and settings.allow_staff_whatsapp:
        safe_send_whatsapp(
            to=normalize_mobile(mobile, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key=event_key,
        )


def send_identity_verification_notification(*, channel: str, contact_value: str, verification_code: str):
    settings = get_notification_settings()
    if not settings:
        frappe.throw(_("Complaint Notification Settings are not configured."))

    text_message = f"رمز التحقق الخاص بك لإرسال الشكوى هو: {verification_code}. صالح لفترة محدودة."
    html_message = (
        f"<div style='direction:rtl;font-family:Tahoma,Arial,sans-serif;'>"
        f"<h3>رمز التحقق لهوية مقدم الشكوى</h3>"
        f"<p>رمز التحقق الخاص بك هو: <b>{verification_code}</b></p>"
        f"<p>هذا الرمز صالح لفترة محدودة ويستخدم لإتمام إرسال الشكوى أو التظلم.</p>"
        f"</div>"
    )

    if channel == "Email":
        if not is_email_enabled(settings) or not cint_bool(getattr(settings, "allow_email_verification", 1)):
            frappe.throw(_("Email verification is disabled in Complaint Notification Settings."))
        subject = getattr(settings, "verification_email_subject", None) or _("Complaint Identity Verification Code")
        safe_send_email([contact_value], subject, html_message)
        return

    if channel == "SMS":
        if not (cint_bool(getattr(settings, "enable_sms", 0)) and cint_bool(getattr(settings, "allow_sms_verification", 0))):
            frappe.throw(_("SMS verification is disabled in Complaint Notification Settings."))
        if not getattr(settings, "sms_endpoint", None):
            frappe.throw(_("SMS endpoint is not configured."))
        safe_send_sms(
            to=normalize_mobile(contact_value, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key="identity_verification",
        )
        return

    if channel == "WhatsApp":
        if not (cint_bool(getattr(settings, "enable_whatsapp", 0)) and cint_bool(getattr(settings, "allow_whatsapp_verification", 0))):
            frappe.throw(_("WhatsApp verification is disabled in Complaint Notification Settings."))
        if not getattr(settings, "whatsapp_endpoint", None):
            frappe.throw(_("WhatsApp endpoint is not configured."))
        safe_send_whatsapp(
            to=normalize_mobile(contact_value, settings.default_country_code),
            message=text_message,
            settings=settings,
            event_key="identity_verification",
        )
        return

    if channel == "Telegram":
        if not (cint_bool(getattr(settings, "enable_telegram", 0)) and cint_bool(getattr(settings, "allow_telegram_verification", 0))):
            frappe.throw(_("Telegram verification is disabled in Complaint Notification Settings."))
        if not getattr(settings, "telegram_endpoint", None):
            frappe.throw(_("Telegram endpoint is not configured."))
        safe_send_telegram(
            to=contact_value,
            message=text_message,
            settings=settings,
            event_key="identity_verification",
        )
        return

    frappe.throw(_("Unsupported verification channel: {0}").format(channel))


def is_email_enabled(settings) -> bool:
    if not settings:
        return True
    return cint_bool(getattr(settings, "enable_email", 1))


def safe_send_email(recipients: list[str], subject: str, message: str):
    try:
        frappe.sendmail(recipients=recipients, subject=subject, message=message, delayed=False)
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Yemen Complaints Email Notification Failure"))


def safe_send_sms(*, to: str, message: str, settings, event_key: str):
    if not getattr(settings, "sms_endpoint", None):
        return

    payload = {
        "to": to,
        "message": message,
        "event": event_key,
        "source": "yemen_complaints",
    }
    headers = build_headers(
        token=getattr(settings, "sms_api_key", None),
        auth_header=getattr(settings, "sms_auth_header", None),
    )
    post_json(
        endpoint=settings.sms_endpoint,
        payload=payload,
        headers=headers,
        timeout=getattr(settings, "sms_timeout", 10) or 10,
        title=_("Yemen Complaints SMS Notification Failure"),
    )


def safe_send_whatsapp(*, to: str, message: str, settings, event_key: str):
    if not getattr(settings, "whatsapp_endpoint", None):
        return

    payload = {
        "to": to,
        "message": message,
        "event": event_key,
        "source": "yemen_complaints",
        "template_name": getattr(settings, "whatsapp_template_name", None),
    }
    headers = build_headers(
        token=getattr(settings, "whatsapp_token", None),
        auth_header=getattr(settings, "whatsapp_auth_header", None),
    )
    post_json(
        endpoint=settings.whatsapp_endpoint,
        payload=payload,
        headers=headers,
        timeout=getattr(settings, "whatsapp_timeout", 10) or 10,
        title=_("Yemen Complaints WhatsApp Notification Failure"),
    )


def safe_send_telegram(*, to: str, message: str, settings, event_key: str):
    if not getattr(settings, "telegram_endpoint", None):
        return

    payload = {
        "to": to,
        "message": message,
        "event": event_key,
        "source": "yemen_complaints",
    }
    headers = build_headers(
        token=getattr(settings, "telegram_token", None),
        auth_header=getattr(settings, "telegram_auth_header", None),
    )
    post_json(
        endpoint=settings.telegram_endpoint,
        payload=payload,
        headers=headers,
        timeout=getattr(settings, "telegram_timeout", 10) or 10,
        title=_("Yemen Complaints Telegram Notification Failure"),
    )


def build_headers(token: str | None = None, auth_header: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers[auth_header or "Authorization"] = token
    return headers


def post_json(*, endpoint: str, payload: dict, headers: dict, timeout: int, title: str):
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception:
        frappe.log_error(
            message=f"Payload: {frappe.as_json(payload)}\n\n{frappe.get_traceback()}",
            title=title,
        )


def normalize_mobile(number: str, default_country_code: str | None = None) -> str:
    raw = cstr(number or "").strip().replace(" ", "")
    if not raw:
        return raw
    if raw.startswith("+"):
        return raw
    if default_country_code:
        code = cstr(default_country_code).strip()
        if code and not code.startswith("+"):
            code = f"+{code}"
        if raw.startswith("0"):
            raw = raw[1:]
        return f"{code}{raw}"
    return raw


def make_plain_text(value: str) -> str:
    return strip_html(value or "").strip()


def cint_bool(value) -> bool:
    return cstr(value).strip() not in {"", "0", "False", "false", "None", "none"}
