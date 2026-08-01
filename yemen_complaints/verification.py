from __future__ import annotations

import hashlib
import json
import random
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_datetime, now_datetime

from yemen_complaints.messaging import get_notification_settings, normalize_mobile, send_identity_verification_notification
from yemen_complaints.security import (
    OTP_SEND_CONTACT_LIMIT,
    OTP_SEND_CONTACT_WINDOW,
    OTP_SEND_IP_LIMIT,
    OTP_SEND_IP_WINDOW,
    OTP_STATUS_IP_LIMIT,
    OTP_STATUS_IP_WINDOW,
    OTP_VERIFY_IP_LIMIT,
    OTP_VERIFY_IP_WINDOW,
    enforce_rate_limit,
    get_request_ip,
    log_security_event,
)
from yemen_complaints.utils import ROLE_MAP

VERIFICATION_PURPOSE = "Complaint Submission"
VERIFIED_STATUS = "Verified"


@frappe.whitelist(allow_guest=True)
def send_identity_verification_code(
    channel: str,
    contact_value: str,
    citizen_full_name: str | None = None,
    email: str | None = None,
    mobile_number: str | None = None,
    telegram_id: str | None = None,
):
    settings = get_notification_settings()
    ensure_verification_enabled(settings)

    channel = normalize_channel(channel)
    contact_value = (contact_value or "").strip()
    citizen_full_name = (citizen_full_name or "").strip()
    email = (email or "").strip()
    mobile_number = (mobile_number or "").strip()
    telegram_id = (telegram_id or "").strip()

    if not contact_value:
        frappe.throw(_("Contact value is required for identity verification."))

    normalized_contact = normalize_contact_for_channel(channel, contact_value, settings)
    ensure_channel_contact_consistency(channel, normalized_contact, email, mobile_number, telegram_id, settings)
    enforce_resend_cooldown(channel, normalized_contact, settings)
    enforce_rate_limit(
        f"otp_send_contact:{channel}",
        normalized_contact,
        limit=OTP_SEND_CONTACT_LIMIT,
        window_seconds=OTP_SEND_CONTACT_WINDOW,
        error_message=_("Too many verification code requests for this contact. Please try again later."),
        event_type="OTP Send Limit",
        severity="High",
        metadata={"channel": channel},
    )
    enforce_rate_limit(
        "otp_send_ip",
        get_request_ip(),
        limit=OTP_SEND_IP_LIMIT,
        window_seconds=OTP_SEND_IP_WINDOW,
        error_message=_("Too many verification attempts from this network. Please try again later."),
        event_type="OTP Send IP Limit",
        severity="High",
        metadata={"channel": channel, "contact": normalized_contact},
    )

    code_length = cint(getattr(settings, "verification_code_length", 6) or 6)
    verification_code = generate_numeric_code(code_length)
    expires_on = add_to_date(now_datetime(), minutes=cint(getattr(settings, "verification_expiry_minutes", 10) or 10))
    max_attempts = cint(getattr(settings, "verification_max_attempts", 5) or 5)

    event_log = [
        make_event("created", f"Verification request created for {channel} and code sent."),
    ]

    doc = frappe.get_doc(
        {
            "doctype": "Complaint Identity Verification",
            "verification_purpose": VERIFICATION_PURPOSE,
            "status": "Pending",
            "channel": channel,
            "contact_value": normalized_contact,
            "citizen_full_name": citizen_full_name,
            "email": email or (normalized_contact if channel == "Email" else None),
            "mobile_number": normalize_mobile(mobile_number or contact_value, getattr(settings, "default_country_code", None)) if channel in {"SMS", "WhatsApp"} else mobile_number,
            "telegram_id": telegram_id or (normalized_contact if channel == "Telegram" else None),
            "verification_code_hash": build_code_hash(code=verification_code, contact_value=normalized_contact),
            "expires_on": expires_on,
            "attempts": 0,
            "max_attempts": max_attempts,
            "last_sent_on": now_datetime(),
            "metadata_json": json.dumps({"channel": channel, "contact": normalized_contact}, ensure_ascii=False),
            "event_log_json": json.dumps(event_log, ensure_ascii=False, indent=2),
        }
    )
    doc.insert(ignore_permissions=True)

    send_identity_verification_notification(
        channel=channel,
        contact_value=normalized_contact,
        verification_code=verification_code,
    )
    log_security_event(
        event_type="OTP Send",
        endpoint="send_identity_verification_code",
        scope=f"OTP:{channel}",
        identifier=normalized_contact,
        status="Allowed",
        severity="Low",
        message="Identity verification code issued.",
        metadata={"channel": channel, "reference": doc.name},
    )

    return {
        "reference": doc.name,
        "channel": channel,
        "masked_contact": mask_contact(channel, normalized_contact),
        "expires_on": doc.expires_on,
        "attempts": 0,
        "max_attempts": max_attempts,
        "event_log": event_log,
    }


@frappe.whitelist(allow_guest=True)
def confirm_identity_verification_code(reference: str, verification_code: str):
    if not reference or not verification_code:
        frappe.throw(_("Verification reference and code are required."))

    enforce_rate_limit(
        "otp_verify_ip",
        get_request_ip(),
        limit=OTP_VERIFY_IP_LIMIT,
        window_seconds=OTP_VERIFY_IP_WINDOW,
        error_message=_("Too many verification attempts from this network. Please try again later."),
        event_type="OTP Verify IP Limit",
        severity="High",
        metadata={"reference": reference},
    )

    doc = frappe.get_doc("Complaint Identity Verification", reference)
    if doc.status == "Used":
        frappe.throw(_("This verification request has already been used."))
    if is_expired(doc):
        expire_request(doc)
        frappe.throw(_("Verification code has expired. Please request a new code."))
    if doc.status not in {"Pending", "Verified"}:
        frappe.throw(_("Verification request is no longer valid."))
    if doc.attempts >= (doc.max_attempts or 5):
        set_status_with_event(doc, "Failed", "Maximum verification attempts reached.")
        frappe.throw(_("Maximum verification attempts reached."))

    expected_hash = build_code_hash(code=verification_code.strip(), contact_value=doc.contact_value)
    if expected_hash != doc.verification_code_hash:
        attempts = (doc.attempts or 0) + 1
        updates = {"attempts": attempts}
        if attempts >= (doc.max_attempts or 5):
            updates["status"] = "Failed"
            append_event(doc, "failed", "Maximum verification attempts reached after invalid code.")
        else:
            append_event(doc, "invalid_attempt", f"Invalid verification code entered. Attempt {attempts}.")
        frappe.db.set_value("Complaint Identity Verification", doc.name, updates, update_modified=False)
        log_security_event(
            event_type="OTP Invalid Code",
            endpoint="confirm_identity_verification_code",
            scope="OTP:Verify",
            identifier=doc.contact_value,
            status="Observed",
            severity="Medium",
            message=f"Invalid verification code attempt #{attempts}.",
            metadata={"reference": doc.name, "attempts": attempts},
        )
        frappe.throw(_("Invalid verification code."))

    verification_token = frappe.generate_hash(length=32)
    verified_on = now_datetime()
    frappe.db.set_value(
        "Complaint Identity Verification",
        doc.name,
        {
            "status": VERIFIED_STATUS,
            "verified_on": verified_on,
            "verification_token": verification_token,
        },
        update_modified=False,
    )
    append_event(doc, "verified", "Identity verification completed successfully.")
    log_security_event(
        event_type="OTP Verified",
        endpoint="confirm_identity_verification_code",
        scope=f"OTP:{doc.channel}",
        identifier=doc.contact_value,
        status="Allowed",
        severity="Low",
        message="Identity verification completed successfully.",
        metadata={"reference": doc.name},
    )

    return {
        "reference": doc.name,
        "verification_token": verification_token,
        "verified_on": verified_on,
        "verified_contact": doc.contact_value,
        "channel": doc.channel,
        "attempts": doc.attempts or 0,
        "max_attempts": doc.max_attempts or 5,
        "event_log": load_event_log(doc),
    }


@frappe.whitelist(allow_guest=True)
def resend_identity_verification_code(reference: str):
    if not reference:
        frappe.throw(_("Verification reference is required."))
    enforce_rate_limit(
        "otp_resend_ip",
        get_request_ip(),
        limit=OTP_SEND_IP_LIMIT,
        window_seconds=OTP_SEND_IP_WINDOW,
        error_message=_("Too many resend attempts from this network. Please try again later."),
        event_type="OTP Resend IP Limit",
        severity="High",
        metadata={"reference": reference},
    )
    doc = frappe.get_doc("Complaint Identity Verification", reference)
    if doc.status == "Used":
        frappe.throw(_("This verification request has already been used."))

    settings = get_notification_settings()
    ensure_verification_enabled(settings)
    enforce_resend_cooldown(doc.channel, doc.contact_value, settings)

    verification_code = generate_numeric_code(cint(getattr(settings, "verification_code_length", 6) or 6))
    expires_on = add_to_date(now_datetime(), minutes=cint(getattr(settings, "verification_expiry_minutes", 10) or 10))
    frappe.db.set_value(
        "Complaint Identity Verification",
        doc.name,
        {
            "status": "Pending",
            "verification_code_hash": build_code_hash(code=verification_code, contact_value=doc.contact_value),
            "expires_on": expires_on,
            "last_sent_on": now_datetime(),
            "attempts": 0,
        },
        update_modified=False,
    )
    append_event(doc, "resent", "Verification code resent.")
    send_identity_verification_notification(channel=doc.channel, contact_value=doc.contact_value, verification_code=verification_code)
    log_security_event(
        event_type="OTP Resent",
        endpoint="resend_identity_verification_code",
        scope=f"OTP:{doc.channel}",
        identifier=doc.contact_value,
        status="Allowed",
        severity="Low",
        message="Verification code resent.",
        metadata={"reference": doc.name},
    )
    return {
        "reference": doc.name,
        "expires_on": expires_on,
        "masked_contact": mask_contact(doc.channel, doc.contact_value),
        "attempts": 0,
        "max_attempts": doc.max_attempts or 5,
        "event_log": load_event_log(doc),
    }


@frappe.whitelist(allow_guest=True)
def get_identity_verification_status(reference: str):
    if not reference:
        frappe.throw(_("Verification reference is required."))

    enforce_rate_limit(
        "otp_status_ip",
        get_request_ip(),
        limit=OTP_STATUS_IP_LIMIT,
        window_seconds=OTP_STATUS_IP_WINDOW,
        error_message=_("Too many verification status checks from this network. Please try again later."),
        event_type="OTP Status IP Limit",
        severity="Medium",
        metadata={"reference": reference},
    )

    doc = frappe.get_doc("Complaint Identity Verification", reference)
    if is_expired(doc) and doc.status == "Pending":
        expire_request(doc)
        doc.status = "Expired"

    return {
        "reference": doc.name,
        "status": doc.status,
        "channel": doc.channel,
        "masked_contact": mask_contact(doc.channel, doc.contact_value),
        "attempts": doc.attempts or 0,
        "max_attempts": doc.max_attempts or 5,
        "expires_on": doc.expires_on,
        "verified_on": doc.verified_on,
        "last_sent_on": doc.last_sent_on,
        "event_log": load_event_log(doc),
    }



def ensure_verification_enabled(settings):
    if not settings or not cint(getattr(settings, "enforce_identity_verification", 0)):
        frappe.throw(_("Identity verification is not enabled in Complaint Notification Settings."))



def normalize_channel(channel: str) -> str:
    channel = (channel or "").strip()
    if channel not in {"Email", "SMS", "WhatsApp", "Telegram"}:
        frappe.throw(_("Unsupported verification channel."))
    return channel



def normalize_contact_for_channel(channel: str, contact_value: str, settings) -> str:
    if channel == "Email":
        return contact_value.strip().lower()
    if channel in {"SMS", "WhatsApp"}:
        return normalize_mobile(contact_value, getattr(settings, "default_country_code", None))
    return contact_value.strip()



def ensure_channel_contact_consistency(channel: str, normalized_contact: str, email: str, mobile_number: str, telegram_id: str, settings):
    if channel == "Email" and email and normalized_contact != email.strip().lower():
        frappe.throw(_("Selected verification channel does not match the email field."))
    if channel in {"SMS", "WhatsApp"}:
        normalized_mobile = normalize_mobile(mobile_number or normalized_contact, getattr(settings, "default_country_code", None))
        if normalized_contact != normalized_mobile:
            frappe.throw(_("Selected verification channel does not match the mobile number field."))
    if channel == "Telegram" and telegram_id and normalized_contact != telegram_id.strip():
        frappe.throw(_("Selected verification channel does not match the Telegram ID field."))



def enforce_resend_cooldown(channel: str, contact_value: str, settings):
    cooldown = cint(getattr(settings, "verification_resend_cooldown_seconds", 60) or 60)
    if cooldown <= 0:
        return

    latest = frappe.get_all(
        "Complaint Identity Verification",
        filters={"channel": channel, "contact_value": contact_value},
        fields=["name", "creation"],
        order_by="creation desc",
        limit=1,
    )
    if not latest:
        return

    last_created = get_datetime(latest[0].creation)
    if now_datetime() < last_created + timedelta(seconds=cooldown):
        frappe.throw(_("Please wait before requesting another verification code."))



def build_code_hash(*, code: str, contact_value: str) -> str:
    payload = f"{code.strip()}::{contact_value.strip().lower()}::yemen-complaints-verification"
    return hashlib.sha256(payload.encode()).hexdigest()



def generate_numeric_code(length: int) -> str:
    length = max(4, min(length or 6, 10))
    return "".join(str(random.randint(0, 9)) for _ in range(length))



def is_expired(doc) -> bool:
    return bool(doc.expires_on and get_datetime(doc.expires_on) < now_datetime())



def expire_request(doc):
    frappe.db.set_value("Complaint Identity Verification", doc.name, "status", "Expired", update_modified=False)
    append_event(doc, "expired", "Verification request expired.")



def mask_contact(channel: str, value: str) -> str:
    if not value:
        return value
    if channel == "Email":
        parts = value.split("@")
        if len(parts) == 2:
            name = parts[0]
            masked_name = name[:2] + "***" if len(name) > 2 else "***"
            return f"{masked_name}@{parts[1]}"
    if len(value) <= 4:
        return "***"
    return value[:2] + "***" + value[-2:]



def should_require_identity_verification(doc) -> bool:
    settings = get_notification_settings()
    if not settings or not cint(getattr(settings, "enforce_identity_verification", 0)):
        return False

    roles = set(frappe.get_roles())
    staff_roles = {ROLE_MAP["advisor"], ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]}
    is_staff = bool(roles.intersection(staff_roles)) or frappe.session.user == "Administrator"
    return not is_staff and (doc.channel == "Web Form" or frappe.session.user == "Guest" or ROLE_MAP["citizen"] in roles)



def validate_complaint_identity_verification(doc):
    if not should_require_identity_verification(doc):
        return

    if doc.identity_verification_status != VERIFIED_STATUS:
        frappe.throw(_("Citizen identity must be verified before complaint submission."))

    if not doc.identity_verification_reference or not doc.identity_verification_token:
        frappe.throw(_("Verification reference and token are required."))

    verification = frappe.get_doc("Complaint Identity Verification", doc.identity_verification_reference)
    if verification.status != VERIFIED_STATUS:
        frappe.throw(_("Identity verification request is not in verified status."))
    if verification.verification_token != doc.identity_verification_token:
        frappe.throw(_("Identity verification token mismatch."))
    if verification.used_on:
        frappe.throw(_("Identity verification token has already been used."))
    if is_expired(verification):
        expire_request(verification)
        frappe.throw(_("Identity verification request has expired."))

    expected_contact = verification.contact_value
    if verification.channel == "Email":
        actual = (doc.email or "").strip().lower()
    elif verification.channel in {"SMS", "WhatsApp"}:
        settings = get_notification_settings()
        actual = normalize_mobile(doc.mobile_number or "", getattr(settings, "default_country_code", None))
    else:
        actual = (doc.telegram_id or "").strip()

    if actual != expected_contact:
        frappe.throw(_("The verified contact does not match the submitted complaint contact details."))

    doc.verified_contact = expected_contact
    doc.identity_verification_channel = verification.channel
    doc.identity_verified_on = verification.verified_on



def mark_verification_as_used(doc):
    if not doc.identity_verification_reference:
        return
    if not frappe.db.exists("Complaint Identity Verification", doc.identity_verification_reference):
        return
    verification = frappe.get_doc("Complaint Identity Verification", doc.identity_verification_reference)
    if verification.status != VERIFIED_STATUS or verification.used_on:
        return
    frappe.db.set_value(
        "Complaint Identity Verification",
        verification.name,
        {
            "status": "Used",
            "used_on": now_datetime(),
            "used_for_doctype": doc.doctype,
            "used_for_docname": doc.name,
        },
        update_modified=False,
    )
    append_event(verification, "used", f"Verification linked to {doc.doctype} {doc.name}.")



def make_event(event_type: str, message: str) -> dict:
    return {
        "event_type": event_type,
        "message": message,
        "timestamp": now_datetime().isoformat(),
    }



def load_event_log(doc) -> list[dict]:
    raw = doc.get("event_log_json") or "[]"
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []



def append_event(doc, event_type: str, message: str):
    log = load_event_log(doc)
    log.append(make_event(event_type, message))
    frappe.db.set_value(
        "Complaint Identity Verification",
        doc.name,
        "event_log_json",
        json.dumps(log, ensure_ascii=False, indent=2),
        update_modified=False,
    )



def set_status_with_event(doc, status: str, message: str):
    frappe.db.set_value("Complaint Identity Verification", doc.name, "status", status, update_modified=False)
    append_event(doc, status.lower(), message)
