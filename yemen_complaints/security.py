from __future__ import annotations

import json
import time
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now_datetime


OTP_SEND_CONTACT_LIMIT = 3
OTP_SEND_CONTACT_WINDOW = 15 * 60
OTP_SEND_IP_LIMIT = 10
OTP_SEND_IP_WINDOW = 15 * 60
OTP_VERIFY_IP_LIMIT = 20
OTP_VERIFY_IP_WINDOW = 15 * 60
OTP_STATUS_IP_LIMIT = 60
OTP_STATUS_IP_WINDOW = 10 * 60
PUBLIC_TRACK_IP_LIMIT = 20
PUBLIC_TRACK_IP_WINDOW = 10 * 60
AI_TEXT_USER_LIMIT = 60
AI_TEXT_USER_WINDOW = 60 * 60
AI_ASSISTANT_USER_LIMIT = 20
AI_ASSISTANT_USER_WINDOW = 60 * 60
AI_APPLY_USER_LIMIT = 40
AI_APPLY_USER_WINDOW = 60 * 60


def get_request_ip() -> str:
    request = getattr(frappe.local, "request", None)
    if request:
        forwarded = request.headers.get("X-Forwarded-For") if hasattr(request, "headers") else None
        if forwarded:
            return forwarded.split(",")[0].strip()
        remote_addr = request.environ.get("REMOTE_ADDR") if hasattr(request, "environ") else None
        if remote_addr:
            return remote_addr
    return getattr(frappe.local, "request_ip", None) or "unknown"



def enforce_rate_limit(
    namespace: str,
    identifier: str,
    *,
    limit: int,
    window_seconds: int,
    error_message: str,
    event_type: str,
    severity: str = "Medium",
    metadata: dict[str, Any] | None = None,
):
    identifier = (identifier or "unknown").strip() or "unknown"
    key = f"yc:rl:{namespace}:{identifier}"
    now_ts = int(time.time())
    timestamps = _get_cached_timestamps(key)
    timestamps = [ts for ts in timestamps if ts > now_ts - window_seconds]

    if len(timestamps) >= limit:
        log_security_event(
            event_type=event_type,
            endpoint=namespace,
            scope=namespace,
            identifier=identifier,
            status="Blocked",
            severity=severity,
            message=error_message,
            metadata={"limit": limit, "window_seconds": window_seconds, **(metadata or {})},
        )
        frappe.throw(error_message)

    timestamps.append(now_ts)
    _set_cached_timestamps(key, timestamps, window_seconds)



def log_security_event(
    *,
    event_type: str,
    endpoint: str,
    scope: str,
    identifier: str,
    status: str,
    severity: str,
    message: str,
    metadata: dict[str, Any] | None = None,
):
    if not frappe.db.exists("DocType", "Complaint Security Event"):
        return

    try:
        frappe.get_doc(
            {
                "doctype": "Complaint Security Event",
                "event_type": event_type,
                "severity": severity,
                "status": status,
                "endpoint": endpoint,
                "scope": scope,
                "identifier": identifier,
                "ip_address": get_request_ip(),
                "user": None if frappe.session.user == "Guest" else frappe.session.user,
                "occurred_on": now_datetime(),
                "message": message,
                "metadata_json": json.dumps(metadata or {}, ensure_ascii=False, indent=2),
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Complaint Security Event Logging Failure"))



def _get_cached_timestamps(key: str) -> list[int]:
    try:
        raw = frappe.cache().get_value(key)
    except Exception:
        return []

    if not raw:
        return []
    if isinstance(raw, bytes):
        raw = raw.decode()
    if isinstance(raw, list):
        return [cint(x) for x in raw]
    try:
        parsed = json.loads(raw)
        return [cint(x) for x in parsed if cint(x)]
    except Exception:
        return []



def _set_cached_timestamps(key: str, timestamps: list[int], window_seconds: int):
    try:
        frappe.cache().set_value(key, json.dumps(timestamps), expires_in_sec=window_seconds)
    except Exception:
        pass
