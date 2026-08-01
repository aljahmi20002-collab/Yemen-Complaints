from __future__ import annotations

import json
import re
from typing import Any

import frappe
import requests
from frappe import _
from frappe.utils import cint, flt, now_datetime, strip_html

from yemen_complaints.security import (
    AI_APPLY_USER_LIMIT,
    AI_APPLY_USER_WINDOW,
    AI_ASSISTANT_USER_LIMIT,
    AI_ASSISTANT_USER_WINDOW,
    AI_TEXT_USER_LIMIT,
    AI_TEXT_USER_WINDOW,
    enforce_rate_limit,
    log_security_event,
)
from yemen_complaints.utils import ROLE_MAP

TEXT_FIELD_TYPES = {"Data", "Small Text", "Text", "Text Editor", "Code", "Long Text"}

AI_ACTIONS = {
    "translate": {
        "label": "ترجمة نص",
        "instruction": "Translate the text accurately while preserving intent, tone, names, and important factual details. Output only the translated text.",
    },
    "summarize": {
        "label": "تلخيص نص",
        "instruction": "Summarize the text clearly and concisely. Output only the summary.",
    },
    "improve_writing": {
        "label": "تحسين الكتابة",
        "instruction": "Improve clarity, coherence, structure, and professional quality while preserving meaning. Output only the improved text.",
    },
    "fix_grammar": {
        "label": "إصلاح الإملاء والنحو",
        "instruction": "Correct spelling, grammar, punctuation, and phrasing errors while preserving meaning. Output only the corrected text.",
    },
    "analyze": {
        "label": "تحليل نص",
        "instruction": "Analyze the text and provide key observations, issues, risks, tone, and implications in a structured bullet list.",
    },
    "suggest_reply": {
        "label": "اقترح رد",
        "instruction": "Draft a suitable response to the text as if replying professionally in an official complaints-handling context. Output only the suggested reply.",
    },
    "draft_message": {
        "label": "صياغة رسالة",
        "instruction": "Rewrite the text as a polished message suitable for sending to a citizen or stakeholder. Output only the message body.",
    },
    "classify_subject": {
        "label": "تصنيف الموضوع",
        "instruction": "Classify the subject matter into concise categories or labels relevant to public complaints handling. Output only the classification result.",
    },
    "extract_elements": {
        "label": "ابحث عن عناصر النص",
        "instruction": "Extract the important entities and elements from the text such as names, dates, places, organizations, references, demands, and issues. Use a structured bullet list.",
    },
    "shorten": {
        "label": "اختصر",
        "instruction": "Shorten the text significantly while preserving the main meaning and crucial facts. Output only the shortened text.",
    },
    "expand": {
        "label": "اكتب بالتفصيل",
        "instruction": "Expand the text into a more detailed, complete, and organized version while keeping the original meaning. Output only the expanded text.",
    },
    "simplify": {
        "label": "تبسيط اللغة",
        "instruction": "Rewrite the text in simpler, easier, plain language without losing the key meaning. Output only the simplified text.",
    },
    "make_formal": {
        "label": "اجعل النص رسمي",
        "instruction": "Rewrite the text in a formal official tone suitable for institutions, public administration, and grievance handling. Output only the rewritten text.",
    },
    "text_conclusion": {
        "label": "خلاصة نص",
        "instruction": "Write a final concise conclusion or takeaway from the text in 2-5 lines. Output only the conclusion.",
    },
}


@frappe.whitelist()
def perform_text_action(
    doctype: str,
    docname: str,
    source_field: str,
    action_key: str,
    target_field: str | None = None,
    extra_instruction: str | None = None,
):
    enforce_rate_limit(
        "ai_text_user",
        frappe.session.user,
        limit=AI_TEXT_USER_LIMIT,
        window_seconds=AI_TEXT_USER_WINDOW,
        error_message=_("AI text tools usage limit reached. Please try again later."),
        event_type="AI Text Limit",
        severity="High",
        metadata={"action_key": action_key, "doctype": doctype, "docname": docname},
    )
    settings = get_ai_settings(require_enabled=True)
    doc = frappe.get_doc(doctype, docname)
    ensure_text_field(doctype, source_field)
    if target_field:
        ensure_text_field(doctype, target_field)
        frappe.has_permission(doctype, "write", doc=doc, throw=True)
    else:
        frappe.has_permission(doctype, "read", doc=doc, throw=True)

    if action_key not in AI_ACTIONS:
        frappe.throw(_("Unsupported AI action."))

    source_value = normalize_text(doc.get(source_field))
    if not source_value:
        frappe.throw(_("Source field is empty."))

    meta = frappe.get_meta(doctype)
    source_label = meta.get_label(source_field)
    target_label = meta.get_label(target_field) if target_field else None
    action = AI_ACTIONS[action_key]

    prompt = build_text_action_prompt(
        doctype=doctype,
        docname=docname,
        source_label=source_label,
        source_text=source_value,
        action_instruction=action["instruction"],
        extra_instruction=extra_instruction,
        target_label=target_label,
    )

    provider_name = (getattr(settings, "default_provider", None) or "ChatGPT").strip()
    try:
        provider_name, result = generate_ai_text(settings=settings, prompt=prompt)
        payload = {
            "provider": provider_name,
            "action_key": action_key,
            "action_label": action["label"],
            "target_field": target_field,
            "result": result.strip(),
        }
        create_ai_log(
            provider=provider_name,
            action_key=action_key,
            action_label=action["label"],
            reference_doctype=doctype,
            reference_name=docname,
            source_field=source_field,
            target_field=target_field,
            prompt_excerpt=prompt,
            response_excerpt=result,
            metadata={"extra_instruction": extra_instruction},
            status="Success",
        )
        log_security_event(
            event_type="AI Text Action",
            endpoint="perform_text_action",
            scope="AI:Text",
            identifier=frappe.session.user,
            status="Allowed",
            severity="Low",
            message=f"AI action executed: {action_key}",
            metadata={"doctype": doctype, "docname": docname, "provider": provider_name},
        )
        return payload
    except Exception:
        create_ai_log(
            provider=provider_name,
            action_key=action_key,
            action_label=action["label"],
            reference_doctype=doctype,
            reference_name=docname,
            source_field=source_field,
            target_field=target_field,
            prompt_excerpt=prompt,
            response_excerpt="",
            metadata={"extra_instruction": extra_instruction},
            status="Error",
            error_message=frappe.get_traceback(),
        )
        raise


@frappe.whitelist()
def run_intake_assistant(docname: str):
    enforce_rate_limit(
        "ai_assistant_user",
        frappe.session.user,
        limit=AI_ASSISTANT_USER_LIMIT,
        window_seconds=AI_ASSISTANT_USER_WINDOW,
        error_message=_("Smart Intake Assistant usage limit reached. Please try again later."),
        event_type="AI Intake Assistant Limit",
        severity="High",
        metadata={"docname": docname},
    )
    settings = get_ai_settings(require_enabled=True)
    if not cint(getattr(settings, "enable_intake_assistant", 0)):
        frappe.throw(_("Smart Intake Assistant is disabled in Complaint AI Settings."))
    if not has_advisor_access() and frappe.session.user != "Administrator":
        frappe.throw(_("Only advisors or system managers can run the Smart Intake Assistant."), frappe.PermissionError)

    doc = frappe.get_doc("Complaint Case", docname)
    frappe.has_permission("Complaint Case", "read", doc=doc, throw=True)

    categories = frappe.get_all(
        "Complaint Category",
        fields=["name", "category_name_ar", "category_name_en", "default_priority"],
        filters={"is_active": 1},
        order_by="category_name_ar asc",
    )
    entities = frappe.get_all(
        "Government Entity",
        fields=["name", "entity_name_ar", "entity_name_en", "entity_type"],
        filters={"active": 1},
        order_by="entity_name_ar asc",
        limit=100,
    )

    context_payload = {
        "case_id": doc.name,
        "case_type": doc.case_type,
        "status": doc.status,
        "priority": doc.priority,
        "subject": normalize_text(doc.subject),
        "details": normalize_text(doc.details),
        "appeal_reason": normalize_text(doc.grievance_reason),
        "current_country": doc.current_country,
        "citizen_governorate": doc.citizen_governorate,
        "citizen_district": doc.citizen_district,
        "incident_governorate": doc.incident_governorate,
        "incident_district": doc.incident_district,
        "government_entity": doc.government_entity,
        "category": doc.category,
        "against_employee": doc.against_employee,
        "source_reference": doc.source_reference,
        "confidentiality_level": doc.confidentiality_level,
        "preferred_language": doc.preferred_language,
        "available_categories": categories,
        "available_entities": entities,
    }

    assistant_prompt = build_intake_assistant_prompt(settings, context_payload)
    provider_name = (getattr(settings, "default_provider", None) or "ChatGPT").strip()
    try:
        provider_name, raw_result = generate_ai_text(settings=settings, prompt=assistant_prompt, json_mode=True)
        parsed = parse_json_response(raw_result)

        response = {
            "provider": provider_name,
            "raw_result": raw_result,
            "summary": parsed.get("summary") or "",
            "classification": parsed.get("classification") or "",
            "suggested_priority": parsed.get("suggested_priority") or "",
            "suggested_category": parsed.get("suggested_category") or "",
            "suggested_entity": parsed.get("suggested_entity") or "",
            "key_elements": stringify_json_value(parsed.get("key_elements")),
            "risk_flags": stringify_json_value(parsed.get("risk_flags")),
            "recommended_actions": stringify_json_value(parsed.get("recommended_actions")),
            "suggested_reply": parsed.get("suggested_reply") or "",
            "citizen_message": parsed.get("citizen_message") or "",
            "reasoning": parsed.get("reasoning") or "",
        }
        create_ai_log(
            provider=provider_name,
            action_key="intake_assistant",
            action_label="Smart Intake Assistant",
            reference_doctype="Complaint Case",
            reference_name=docname,
            source_field="details",
            target_field="ai_analysis_json",
            prompt_excerpt=assistant_prompt,
            response_excerpt=raw_result,
            metadata=context_payload,
            status="Success",
        )
        log_security_event(
            event_type="AI Intake Assistant",
            endpoint="run_intake_assistant",
            scope="AI:IntakeAssistant",
            identifier=frappe.session.user,
            status="Allowed",
            severity="Low",
            message="Smart Intake Assistant executed successfully.",
            metadata={"docname": docname, "provider": provider_name},
        )
        return response
    except Exception:
        create_ai_log(
            provider=provider_name,
            action_key="intake_assistant",
            action_label="Smart Intake Assistant",
            reference_doctype="Complaint Case",
            reference_name=docname,
            source_field="details",
            target_field="ai_analysis_json",
            prompt_excerpt=assistant_prompt,
            response_excerpt="",
            metadata=context_payload,
            status="Error",
            error_message=frappe.get_traceback(),
        )
        raise


@frappe.whitelist()
def apply_intake_assistant_recommendations(docname: str):
    enforce_rate_limit(
        "ai_apply_user",
        frappe.session.user,
        limit=AI_APPLY_USER_LIMIT,
        window_seconds=AI_APPLY_USER_WINDOW,
        error_message=_("AI recommendation apply limit reached. Please try again later."),
        event_type="AI Apply Limit",
        severity="Medium",
        metadata={"docname": docname},
    )
    if not has_advisor_access() and frappe.session.user != "Administrator":
        frappe.throw(_("Only advisors or system managers can apply AI recommendations."), frappe.PermissionError)

    doc = frappe.get_doc("Complaint Case", docname)
    frappe.has_permission("Complaint Case", "write", doc=doc, throw=True)

    updates = {}
    if doc.ai_suggested_priority in {"Low", "Medium", "High", "Critical"}:
        updates["priority"] = doc.ai_suggested_priority

    category_name = resolve_category_name(doc.ai_suggested_category)
    if category_name:
        updates["category"] = category_name

    entity_name = resolve_entity_name(doc.ai_suggested_entity)
    if entity_name:
        updates["government_entity"] = entity_name

    if not updates:
        frappe.throw(_("No applicable AI recommendations were found to apply."))

    for key, value in updates.items():
        doc.set(key, value)
    doc.save(ignore_permissions=True)
    log_security_event(
        event_type="AI Recommendation Apply",
        endpoint="apply_intake_assistant_recommendations",
        scope="AI:Apply",
        identifier=frappe.session.user,
        status="Allowed",
        severity="Low",
        message="AI recommendations applied to complaint case.",
        metadata={"docname": docname, "updates": updates},
    )
    return updates


def get_ai_settings(require_enabled: bool = False):
    if not frappe.db.exists("DocType", "Complaint AI Settings"):
        frappe.throw(_("Complaint AI Settings DocType is missing."))

    settings = frappe.get_single("Complaint AI Settings")
    if require_enabled and not cint(getattr(settings, "enable_ai", 0)):
        frappe.throw(_("AI is disabled. Please enable it from Complaint AI Settings."))
    return settings


def ensure_text_field(doctype: str, fieldname: str):
    meta = frappe.get_meta(doctype)
    df = meta.get_field(fieldname)
    if not df:
        frappe.throw(_("Invalid field: {0}").format(fieldname))
    if df.fieldtype not in TEXT_FIELD_TYPES:
        frappe.throw(_("Field {0} is not a supported text field.").format(fieldname))


def normalize_text(value: Any) -> str:
    text = strip_html(frappe.as_unicode(value or ""))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def build_text_action_prompt(
    *,
    doctype: str,
    docname: str,
    source_label: str,
    source_text: str,
    action_instruction: str,
    extra_instruction: str | None,
    target_label: str | None,
) -> str:
    parts = [
        "You are an Arabic-first public-sector writing assistant working inside a Frappe complaints platform.",
        action_instruction,
        f"Document Type: {doctype}",
        f"Document ID: {docname}",
        f"Source Field: {source_label}",
    ]
    if target_label:
        parts.append(f"Target Field: {target_label}")
    if extra_instruction:
        parts.append(f"Additional Instruction: {extra_instruction}")
    parts.append("Text:")
    parts.append(source_text)
    return "\n".join(parts)


def build_intake_assistant_prompt(settings, context_payload: dict) -> str:
    default_prompt = (
        "You are a smart intake advisor for Yemeni citizen complaints and appeals. "
        "Analyze the complaint carefully, classify it, identify urgency, suggest the best category and government entity, "
        "extract the important facts, and draft a professional advisory reply. Return JSON only."
    )
    system_prompt = normalize_text(getattr(settings, "assistant_system_prompt", None) or default_prompt)
    schema = {
        "summary": "string",
        "classification": "string",
        "suggested_priority": "Low | Medium | High | Critical",
        "suggested_category": "string",
        "suggested_entity": "string",
        "key_elements": ["array of key facts and entities"],
        "risk_flags": ["array of risks, red flags, urgency indicators"],
        "recommended_actions": ["array of recommended advisor next steps"],
        "suggested_reply": "string",
        "citizen_message": "string",
        "reasoning": "string"
    }
    return "\n\n".join(
        [
            system_prompt,
            "Return valid JSON only using this schema:",
            json.dumps(schema, ensure_ascii=False, indent=2),
            "Complaint intake payload:",
            json.dumps(context_payload, ensure_ascii=False, indent=2),
        ]
    )


def generate_ai_text(*, settings, prompt: str, json_mode: bool = False) -> tuple[str, str]:
    provider = (getattr(settings, "default_provider", None) or "ChatGPT").strip()
    temperature = flt(getattr(settings, "temperature", 0.2) or 0.2)
    timeout = cint(getattr(settings, "request_timeout", 60) or 60)

    if provider == "ChatGPT":
        return provider, call_openai_compatible(
            endpoint=getattr(settings, "openai_endpoint", None) or "https://api.openai.com/v1/chat/completions",
            api_key=get_password_value(settings, "openai_api_key"),
            model=getattr(settings, "openai_model", None) or "gpt-4o-mini",
            prompt=prompt,
            temperature=temperature,
            timeout=timeout,
            json_mode=json_mode,
        )
    if provider == "DeepSeek":
        return provider, call_openai_compatible(
            endpoint=getattr(settings, "deepseek_endpoint", None) or "https://api.deepseek.com/chat/completions",
            api_key=get_password_value(settings, "deepseek_api_key"),
            model=getattr(settings, "deepseek_model", None) or "deepseek-chat",
            prompt=prompt,
            temperature=temperature,
            timeout=timeout,
            json_mode=json_mode,
        )
    if provider == "Gemini":
        return provider, call_gemini(
            endpoint=getattr(settings, "gemini_endpoint", None) or "https://generativelanguage.googleapis.com/v1beta/models",
            api_key=get_password_value(settings, "gemini_api_key"),
            model=getattr(settings, "gemini_model", None) or "gemini-2.5-flash",
            prompt=prompt,
            temperature=temperature,
            timeout=timeout,
            json_mode=json_mode,
        )

    frappe.throw(_("Unsupported AI provider: {0}").format(provider))


def call_openai_compatible(*, endpoint: str, api_key: str | None, model: str, prompt: str, temperature: float, timeout: int, json_mode: bool) -> str:
    if not api_key:
        frappe.throw(_("API key is missing for the selected AI provider."))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": "You are a high-quality Arabic writing and analysis assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    handle_http_error(response)
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        frappe.throw(_("Unexpected AI response format: {0}").format(frappe.as_unicode(exc)))


def call_gemini(*, endpoint: str, api_key: str | None, model: str, prompt: str, temperature: float, timeout: int, json_mode: bool) -> str:
    if not api_key:
        frappe.throw(_("API key is missing for Gemini."))

    url = f"{endpoint.rstrip('/')}/{model}:generateContent?key={api_key}"
    payload: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)
    handle_http_error(response)
    data = response.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except Exception as exc:
        frappe.throw(_("Unexpected Gemini response format: {0}").format(frappe.as_unicode(exc)))


def handle_http_error(response):
    try:
        response.raise_for_status()
    except Exception:
        details = response.text[:2000] if getattr(response, "text", None) else ""
        frappe.throw(_("AI provider request failed. Details: {0}").format(details))


def get_password_value(doc, fieldname: str) -> str | None:
    try:
        value = doc.get_password(fieldname)
    except Exception:
        value = doc.get(fieldname)
    return value or None


def parse_json_response(raw_result: str) -> dict:
    text = (raw_result or "").strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        frappe.throw(_("The AI provider returned an invalid JSON response."))


def stringify_json_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(f"- {frappe.as_unicode(item)}" for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return frappe.as_unicode(value)


def create_ai_log(
    *,
    provider: str,
    action_key: str,
    action_label: str,
    reference_doctype: str,
    reference_name: str,
    source_field: str | None,
    target_field: str | None,
    prompt_excerpt: str,
    response_excerpt: str,
    metadata: dict | None,
    status: str,
    error_message: str | None = None,
):
    if not frappe.db.exists("DocType", "Complaint AI Log"):
        return
    try:
        frappe.get_doc(
            {
                "doctype": "Complaint AI Log",
                "provider": provider,
                "action_key": action_key,
                "action_label": action_label,
                "reference_doctype": reference_doctype,
                "reference_name": reference_name,
                "source_field": source_field,
                "target_field": target_field,
                "status": status,
                "user": frappe.session.user,
                "executed_on": now_datetime(),
                "prompt_excerpt": truncate_text(prompt_excerpt, 1000),
                "response_excerpt": truncate_text(response_excerpt, 1000),
                "error_message": truncate_text(error_message or "", 1000),
                "metadata_json": json.dumps(metadata or {}, ensure_ascii=False, indent=2),
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), _("Complaint AI Log Creation Failure"))



def resolve_category_name(candidate: str | None) -> str | None:
    candidate = normalize_text(candidate)
    if not candidate:
        return None
    if frappe.db.exists("Complaint Category", candidate):
        return candidate
    for field in ["category_name_ar", "category_name_en"]:
        name = frappe.db.get_value("Complaint Category", {field: candidate}, "name")
        if name:
            return name
    return None



def resolve_entity_name(candidate: str | None) -> str | None:
    candidate = normalize_text(candidate)
    if not candidate:
        return None
    if frappe.db.exists("Government Entity", candidate):
        return candidate
    for field in ["entity_name_ar", "entity_name_en"]:
        name = frappe.db.get_value("Government Entity", {field: candidate}, "name")
        if name:
            return name
    return None



def truncate_text(value: str, limit: int) -> str:
    value = frappe.as_unicode(value or "")
    return value[:limit]



def has_advisor_access() -> bool:
    roles = set(frappe.get_roles())
    return bool(roles.intersection({ROLE_MAP["advisor"], ROLE_MAP["manager"]}))
