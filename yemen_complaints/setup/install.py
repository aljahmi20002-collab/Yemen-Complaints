from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.exceptions import DoesNotExistError

from yemen_complaints.utils import ROLE_MAP

ROOT = Path(__file__).resolve().parents[1]
PRINT_DIR = ROOT / "templates" / "print_formats"
DATA_DIR = ROOT / "data"

ROLE_NAMES = list(ROLE_MAP.values())

DEFAULT_CATEGORIES = [
    {
        "name": "Administrative Services",
        "category_name_ar": "الخدمات الإدارية",
        "category_name_en": "Administrative Services",
        "default_priority": "Medium",
        "sla_first_response_hours": 24,
        "sla_resolution_days": 7,
        "description": "شكاوى الخدمات والإجراءات الإدارية.",
        "allows_appeal": 1,
        "is_active": 1,
    },
    {
        "name": "Financial Rights",
        "category_name_ar": "الحقوق المالية",
        "category_name_en": "Financial Rights",
        "default_priority": "High",
        "sla_first_response_hours": 12,
        "sla_resolution_days": 10,
        "description": "المستحقات والتأخير المالي والرواتب والمكافآت.",
        "allows_appeal": 1,
        "is_active": 1,
    },
    {
        "name": "Consular Services",
        "category_name_ar": "الخدمات القنصلية",
        "category_name_en": "Consular Services",
        "default_priority": "Medium",
        "sla_first_response_hours": 24,
        "sla_resolution_days": 5,
        "description": "شكاوى مرتبطة بالسفارات والقنصليات.",
        "allows_appeal": 1,
        "is_active": 1,
    },
]

DEFAULT_ENTITIES = [
    {
        "name": "Prime Ministry Office",
        "entity_name_ar": "رئاسة مجلس الوزراء",
        "entity_name_en": "Prime Ministry Office",
        "entity_code": "PMO",
        "entity_type": "Ministry",
        "active": 1,
    },
    {
        "name": "Ministry of Foreign Affairs",
        "entity_name_ar": "وزارة الخارجية وشؤون المغتربين",
        "entity_name_en": "Ministry of Foreign Affairs",
        "entity_code": "MOFA",
        "entity_type": "Ministry",
        "active": 1,
    },
    {
        "name": "Ministry of Civil Service",
        "entity_name_ar": "وزارة الخدمة المدنية",
        "entity_name_en": "Ministry of Civil Service",
        "entity_code": "MCS",
        "entity_type": "Ministry",
        "active": 1,
    },
]

WEB_FORM_CSS = """
:root {
  --brand: #9b1c1c;
  --brand-soft: #fef2f2;
  --ink: #1f2937;
  --border: #e5e7eb;
}
.web-form-container {
  max-width: 960px;
  margin: 0 auto;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 18px 60px rgba(0,0,0,.08);
  overflow: hidden;
}
.layout-main-section {
  background: linear-gradient(180deg, #fff 0%, #fcfcfc 100%);
  padding: 1.25rem;
}
.form-page {
  direction: rtl;
  color: var(--ink);
  font-family: 'DroidArabicKufi', Tahoma, Arial, sans-serif;
}
.form-page .page-header {
  background: linear-gradient(135deg, var(--brand), #c2410c);
  color: #fff;
  padding: 1.75rem;
  border-radius: 18px;
  margin-bottom: 1rem;
}
.form-column .frappe-control {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .75rem .75rem .25rem;
  margin-bottom: .85rem;
  background: #fff;
}
.btn.btn-primary {
  background: var(--brand);
  border-color: var(--brand);
  border-radius: 999px;
  padding: .75rem 1.25rem;
  font-weight: 700;
}
.alert-success {
  border-radius: 16px;
}
"""

WEB_FORM_SCRIPT = """
frappe.ready(() => {
  document.body.classList.add('complaints-web-form');
});

window.ycIdentityVerification = {
  reference: null,
  verified: false,
  channel: null,
  contact: null,
};

function clearVerificationState(removeStorage = true) {
  window.ycIdentityVerification = {
    reference: null,
    verified: false,
    channel: null,
    contact: null,
  };
  frappe.web_form.set_value('identity_verification_status', '');
  frappe.web_form.set_value('identity_verification_reference', '');
  frappe.web_form.set_value('identity_verification_token', '');
  frappe.web_form.set_value('identity_verified_on', '');
  frappe.web_form.set_value('verified_contact', '');
  if (removeStorage) {
    localStorage.removeItem('yc_identity_verification');
  }
  const statusEl = document.getElementById('identity-verification-status');
  if (statusEl) {
    statusEl.innerHTML = '<span style="color:#92400e;font-weight:700;">لم يتم التحقق من الهوية بعد.</span>';
  }
}

function tryHydrateVerificationFromStorage() {
  try {
    const raw = localStorage.getItem('yc_identity_verification');
    if (!raw) return;
    const data = JSON.parse(raw);
    const current = getVerificationContact();
    const expectedContact = (data.verified_contact || '').trim();
    const currentContact = (current.contact || '').trim();
    if (!data.reference || !data.verification_token || !expectedContact) return;
    if (data.channel !== current.channel) return;
    if (!currentContact || currentContact !== expectedContact) return;

    window.ycIdentityVerification = {
      reference: data.reference,
      verified: true,
      channel: data.channel,
      contact: expectedContact,
    };
    frappe.web_form.set_value('identity_verification_status', 'Verified');
    frappe.web_form.set_value('identity_verification_reference', data.reference);
    frappe.web_form.set_value('identity_verification_token', data.verification_token);
    frappe.web_form.set_value('identity_verified_on', data.verified_on || '');
    frappe.web_form.set_value('verified_contact', expectedContact);
    const statusEl = document.getElementById('identity-verification-status');
    if (statusEl) {
      statusEl.innerHTML = '<span style="color:#166534;font-weight:700;">تم تحميل حالة تحقق ناجحة ويمكنك الآن إرسال الطلب.</span>';
    }
  } catch (e) {
    console.warn('Could not hydrate verification from storage', e);
  }
}

function getVerificationContact() {
  const channel = frappe.web_form.get_value('identity_verification_channel');
  let contact = '';
  if (channel === 'Email') {
    contact = frappe.web_form.get_value('email') || '';
  } else if (channel === 'SMS' || channel === 'WhatsApp') {
    contact = frappe.web_form.get_value('mobile_number') || '';
  } else if (channel === 'Telegram') {
    contact = frappe.web_form.get_value('telegram_id') || '';
  }
  return { channel, contact: (contact || '').trim() };
}

function bindLocationFilters() {
  frappe.web_form.set_query('citizen_district', () => {
    const governorate = frappe.web_form.get_value('citizen_governorate');
    return { filters: governorate ? { governorate } : {} };
  });

  frappe.web_form.set_query('incident_district', () => {
    const governorate = frappe.web_form.get_value('incident_governorate');
    return { filters: governorate ? { governorate } : {} };
  });

  frappe.web_form.on('citizen_governorate', () => {
    frappe.web_form.set_value('citizen_district', '');
  });

  frappe.web_form.on('incident_governorate', () => {
    frappe.web_form.set_value('incident_district', '');
  });
}

function bindVerificationWatchers() {
  ['email', 'mobile_number', 'telegram_id', 'identity_verification_channel', 'citizen_full_name'].forEach((fieldname) => {
    frappe.web_form.on(fieldname, () => {
      clearVerificationState();
      updateVerificationScreenLink();
      tryHydrateVerificationFromStorage();
    });
  });
}

function injectVerificationPanel() {
  if (document.getElementById('identity-verification-panel')) {
    return;
  }

  const container = document.querySelector('.layout-main-section');
  if (!container) return;

  const panel = document.createElement('div');
  panel.id = 'identity-verification-panel';
  panel.className = 'yc-card';
  panel.style.marginBottom = '14px';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
      <div>
        <div style="font-size:18px;font-weight:800;margin-bottom:6px;color:#9b1c1c;">التحقق من هوية مقدم الشكوى</div>
        <div style="font-size:13px;color:#4b5563;line-height:1.8;margin-bottom:10px;">قبل إرسال الطلب يجب التحقق من هوية مقدم الشكوى عبر البريد الإلكتروني أو الرسائل القصيرة أو واتساب أو تيليجرام بحسب القناة المختارة.</div>
      </div>
      <a id="identity-open-screen" class="btn btn-default" target="_blank" href="/verify-identity">فتح شاشة التحقق المستقلة</a>
    </div>
    <div style="display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:end;">
      <input id="identity-verification-code" class="form-control" placeholder="أدخل رمز التحقق">
      <button type="button" class="btn btn-default" id="identity-send-code">إرسال الرمز</button>
      <button type="button" class="btn btn-primary" id="identity-verify-code">تأكيد الرمز</button>
    </div>
    <div id="identity-verification-status" style="margin-top:10px;font-size:13px;"><span style="color:#92400e;font-weight:700;">لم يتم التحقق من الهوية بعد.</span></div>
  `;
  container.prepend(panel);

  document.getElementById('identity-send-code').addEventListener('click', sendVerificationCode);
  document.getElementById('identity-verify-code').addEventListener('click', confirmVerificationCode);
}

function updateVerificationScreenLink() {
  const link = document.getElementById('identity-open-screen');
  if (!link) return;
  const payload = getVerificationContact();
  const params = new URLSearchParams({
    channel: payload.channel || '',
    email: frappe.web_form.get_value('email') || '',
    mobile: frappe.web_form.get_value('mobile_number') || '',
    telegram_id: frappe.web_form.get_value('telegram_id') || '',
    full_name: frappe.web_form.get_value('citizen_full_name') || '',
    return_to: window.location.pathname,
  });
  link.href = `/verify-identity?${params.toString()}`;
}

function sendVerificationCode() {
  const payload = getVerificationContact();
  const fullName = frappe.web_form.get_value('citizen_full_name') || '';
  if (!payload.channel) {
    frappe.msgprint('يرجى اختيار قناة التحقق أولاً.');
    return;
  }
  if (!payload.contact) {
    frappe.msgprint('يرجى إدخال جهة الاتصال المناسبة للقناة المختارة.');
    return;
  }

  frappe.call({
    method: 'yemen_complaints.verification.send_identity_verification_code',
    freeze: true,
    freeze_message: 'جارٍ إرسال رمز التحقق...',
    args: {
      channel: payload.channel,
      contact_value: payload.contact,
      citizen_full_name: fullName,
      email: frappe.web_form.get_value('email') || '',
      mobile_number: frappe.web_form.get_value('mobile_number') || '',
      telegram_id: frappe.web_form.get_value('telegram_id') || '',
    },
    callback: (r) => {
      const message = r.message;
      window.ycIdentityVerification.reference = message.reference;
      window.ycIdentityVerification.channel = payload.channel;
      window.ycIdentityVerification.contact = payload.contact;
      document.getElementById('identity-verification-status').innerHTML = `<span style="color:#1d4ed8;font-weight:700;">تم إرسال الرمز إلى ${message.masked_contact}. أدخل الرمز لإكمال التحقق.</span>`;
    },
  });
}

function confirmVerificationCode() {
  const code = (document.getElementById('identity-verification-code')?.value || '').trim();
  if (!window.ycIdentityVerification.reference) {
    frappe.msgprint('يرجى طلب رمز التحقق أولاً.');
    return;
  }
  if (!code) {
    frappe.msgprint('يرجى إدخال رمز التحقق.');
    return;
  }

  frappe.call({
    method: 'yemen_complaints.verification.confirm_identity_verification_code',
    freeze: true,
    freeze_message: 'جارٍ التحقق من الرمز...',
    args: {
      reference: window.ycIdentityVerification.reference,
      verification_code: code,
    },
    callback: (r) => {
      const message = r.message;
      window.ycIdentityVerification.verified = true;
      frappe.web_form.set_value('identity_verification_status', 'Verified');
      frappe.web_form.set_value('identity_verification_reference', message.reference);
      frappe.web_form.set_value('identity_verification_token', message.verification_token);
      frappe.web_form.set_value('identity_verified_on', message.verified_on);
      frappe.web_form.set_value('verified_contact', message.verified_contact);
      document.getElementById('identity-verification-status').innerHTML = '<span style="color:#166534;font-weight:700;">تم التحقق من الهوية بنجاح ويمكنك الآن إرسال الطلب.</span>';
    },
  });
}

frappe.web_form.after_load = () => {
  const intro = document.querySelector('.page-header');
  if (intro && !document.querySelector('.complaints-form-badge')) {
    const badge = document.createElement('div');
    badge.className = 'complaints-form-badge';
    badge.innerHTML = '<div style="margin-top:12px;font-size:13px;opacity:.92">منصة مخصصة للمواطنين اليمنيين داخل اليمن وخارجها لتقديم الشكاوى والتظلمات ومتابعتها إلكترونياً.</div>';
    intro.appendChild(badge);
  }
  bindLocationFilters();
  bindVerificationWatchers();
  injectVerificationPanel();
  updateVerificationScreenLink();
  clearVerificationState(false);
  tryHydrateVerificationFromStorage();
};

frappe.web_form.validate = () => {
  const { channel, contact } = getVerificationContact();
  if (!channel) {
    frappe.msgprint('يرجى اختيار قناة التحقق من الهوية.');
    return false;
  }
  if (!contact) {
    frappe.msgprint('يرجى إدخال جهة الاتصال المناسبة للقناة المختارة لإكمال التحقق.');
    return false;
  }
  if (frappe.web_form.get_value('identity_verification_status') !== 'Verified') {
    frappe.msgprint('يجب التحقق من هوية مقدم الشكوى قبل إرسال الطلب.');
    return false;
  }
  return true;
};
"""


def after_install():
    create_roles()
    seed_yemen_admin_units()
    seed_categories()
    seed_entities()
    create_print_formats()
    create_web_forms()
    create_notification_settings()
    create_ai_settings()
    create_number_cards()
    create_workflow()


def after_migrate():
    after_install()


def create_roles():
    role_config = {
        ROLE_MAP["citizen"]: {"desk_access": 0},
        ROLE_MAP["advisor"]: {"desk_access": 1},
        ROLE_MAP["agency"]: {"desk_access": 1},
        ROLE_MAP["follow_up"]: {"desk_access": 1},
        ROLE_MAP["manager"]: {"desk_access": 1},
    }

    for role, config in role_config.items():
        if frappe.db.exists("Role", role):
            doc = frappe.get_doc("Role", role)
            doc.update(config)
            doc.save(ignore_permissions=True)
            continue

        doc = frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role,
                **config,
            }
        )
        doc.insert(ignore_permissions=True)


def seed_yemen_admin_units():
    data_path = DATA_DIR / "yemen_admin_units.json"
    if not data_path.exists():
        return

    data = json.loads(data_path.read_text(encoding="utf-8"))

    for row in data.get("governorates", []):
        values = {"doctype": "Yemen Governorate", **row}
        upsert_doc("Yemen Governorate", row["name"], values)

    # Ensure governorates are visible and resolvable before district link validation starts.
    frappe.db.commit()

    governorate_index = {
        row["name"]: row.get("governorate_name_ar") or row.get("governorate_name_en")
        for row in data.get("governorates", [])
    }

    for row in data.get("districts", []):
        governorate_name = row.get("governorate")
        if governorate_name and not frappe.db.exists("Yemen Governorate", governorate_name):
            fallback_name = governorate_index.get(governorate_name)
            if fallback_name and frappe.db.exists("Yemen Governorate", fallback_name):
                row["governorate"] = fallback_name
            else:
                frappe.throw(f"Governorate {governorate_name} not found while seeding Yemen District {row.get('name')}")

        values = {"doctype": "Yemen District", **row}
        values.pop("governorate_name_en", None)
        values.pop("governorate_name_ar", None)
        upsert_doc("Yemen District", row["name"], values, ignore_links=True)


def seed_categories():
    for row in DEFAULT_CATEGORIES:
        upsert_named_doc("Complaint Category", row["name"], row)


def seed_entities():
    for row in DEFAULT_ENTITIES:
        upsert_named_doc("Government Entity", row["name"], row)


def create_print_formats():
    formats = [
        ("Complaint Case Professional", "Complaint Case", "complaint_case.html"),
        ("Government Entity Professional", "Government Entity", "government_entity.html"),
        ("Complaint Category Professional", "Complaint Category", "complaint_category.html"),
    ]

    for name, doc_type, template_name in formats:
        html = (PRINT_DIR / template_name).read_text(encoding="utf-8")
        values = {
            "doctype": "Print Format",
            "name": name,
            "doc_type": doc_type,
            "module": "Complaints2",
            "print_format_type": "Jinja",
            "html": html,
            "disabled": 0,
            "standard": "Yes",
            "custom_format": 1,
            "raw_printing": 0,
            "show_section_headings": 1,
        }
        upsert_doc("Print Format", name, values)


def create_web_forms():
    common_fields = [
        {"fieldname": "case_type", "fieldtype": "Select", "label": "نوع الطلب", "reqd": 1, "hidden": 1},
        {"fieldname": "citizen_full_name", "fieldtype": "Data", "label": "الاسم الرباعي", "reqd": 1},
        {"fieldname": "citizen_national_id", "fieldtype": "Data", "label": "الرقم الوطني"},
        {"fieldname": "passport_number", "fieldtype": "Data", "label": "رقم الجواز"},
        {"fieldname": "mobile_number", "fieldtype": "Data", "label": "رقم الهاتف", "reqd": 1},
        {"fieldname": "email", "fieldtype": "Data", "label": "البريد الإلكتروني"},
        {"fieldname": "telegram_id", "fieldtype": "Data", "label": "معرّف تيليجرام"},
        {"fieldname": "identity_verification_channel", "fieldtype": "Select", "label": "قناة التحقق من الهوية", "options": "Email\nSMS\nWhatsApp\nTelegram", "default": "Email", "reqd": 1},
        {"fieldname": "identity_verification_status", "fieldtype": "Data", "label": "حالة التحقق", "hidden": 1},
        {"fieldname": "identity_verification_reference", "fieldtype": "Data", "label": "مرجع التحقق", "hidden": 1},
        {"fieldname": "identity_verification_token", "fieldtype": "Data", "label": "رمز تحقق الهوية", "hidden": 1},
        {"fieldname": "identity_verified_on", "fieldtype": "Datetime", "label": "تاريخ التحقق", "hidden": 1},
        {"fieldname": "verified_contact", "fieldtype": "Data", "label": "جهة الاتصال المتحقق منها", "hidden": 1},
        {"fieldname": "current_country", "fieldtype": "Data", "label": "الدولة الحالية", "reqd": 1},
        {"fieldname": "citizen_governorate", "fieldtype": "Link", "options": "Yemen Governorate", "label": "المحافظة"},
        {"fieldname": "citizen_district", "fieldtype": "Link", "options": "Yemen District", "label": "المديرية"},
        {"fieldname": "preferred_language", "fieldtype": "Select", "label": "اللغة المفضلة"},
        {"fieldname": "category", "fieldtype": "Link", "options": "Complaint Category", "label": "التصنيف", "reqd": 1},
        {"fieldname": "government_entity", "fieldtype": "Link", "options": "Government Entity", "label": "الجهة المعنية", "reqd": 1},
        {"fieldname": "confidentiality_level", "fieldtype": "Select", "label": "مستوى السرية"},
        {"fieldname": "subject", "fieldtype": "Data", "label": "عنوان مختصر", "reqd": 1},
        {"fieldname": "details", "fieldtype": "Text Editor", "label": "تفاصيل الشكوى أو التظلم", "reqd": 1},
        {"fieldname": "incident_date", "fieldtype": "Date", "label": "تاريخ الواقعة"},
        {"fieldname": "incident_governorate", "fieldtype": "Link", "options": "Yemen Governorate", "label": "محافظة الواقعة"},
        {"fieldname": "incident_district", "fieldtype": "Link", "options": "Yemen District", "label": "مديرية الواقعة"},
        {"fieldname": "against_employee", "fieldtype": "Data", "label": "الموظف أو الإدارة محل الشكوى"},
    ]

    form_definitions = [
        {
            "name": "Citizen Complaint Submission",
            "title": "تقديم شكوى",
            "route": "submit-complaint",
            "intro": "هذا النموذج مخصص لتقديم الشكاوى العامة. يرجى إدخال البيانات بدقة ورفع المرفقات الداعمة إن وجدت.",
            "case_type_default": "Complaint",
            "success_message": "تم استلام الشكوى بنجاح، وسيتم إشعارك برقم الحالة والمتابعة.",
            "fields": [*common_fields],
        },
        {
            "name": "Citizen Appeal Submission",
            "title": "تقديم تظلم",
            "route": "submit-appeal",
            "intro": "هذا النموذج مخصص للتظلمات والاعتراضات على قرار أو إجراء سابق. يرجى توضيح سبب التظلم والمرجع المرتبط به.",
            "case_type_default": "Appeal",
            "success_message": "تم استلام التظلم بنجاح، وسيتم مراجعته وإشعارك بالتحديثات.",
            "fields": [
                *common_fields,
                {"fieldname": "source_reference", "fieldtype": "Data", "label": "رقم المرجع السابق", "reqd": 1},
                {"fieldname": "grievance_reason", "fieldtype": "Small Text", "label": "سبب التظلم", "reqd": 1},
            ],
        },
    ]

    for form in form_definitions:
        values = {
            "doctype": "Web Form",
            "title": form["title"],
            "module": "Complaints2",
            "doc_type": "Complaint Case",
            "route": form["route"],
            "published": 1,
            "anonymous": 1,
            "login_required": 0,
            "show_sidebar": 0,
            "show_attachments": 1,
            "allow_incomplete": 0,
            "allow_multiple": 0,
            "allow_edit": 0,
            "allow_print": 1,
            "button_label": "إرسال الطلب",
            "success_title": "تم استلام طلبك بنجاح",
            "success_message": form["success_message"],
            "custom_css": WEB_FORM_CSS,
            "client_script": WEB_FORM_SCRIPT,
            "introduction_text": form["intro"],
        }

        fields = [dict(row) for row in form["fields"]]
        for row in fields:
            if row["fieldname"] == "case_type":
                row["default"] = form["case_type_default"]

        existing_name = frappe.db.get_value("Web Form", {"route": form["route"]}, "name") or frappe.db.get_value("Web Form", {"title": form["title"]}, "name")
        if existing_name:
            doc = frappe.get_doc("Web Form", existing_name)
            doc.update(values)
            doc.set("web_form_fields", [])
        else:
            doc = frappe.get_doc(values)

        for idx, row in enumerate(fields, start=1):
            row.update({"doctype": "Web Form Field", "idx": idx})
            doc.append("web_form_fields", row)

        doc.save(ignore_permissions=True)


def create_notification_settings():
    if not frappe.db.exists("DocType", "Complaint Notification Settings"):
        return

    doc = frappe.get_single("Complaint Notification Settings")
    defaults = {
        "enable_email": 1,
        "enable_sms": 0,
        "enable_whatsapp": 0,
        "enable_telegram": 0,
        "default_country_code": "+967",
        "enforce_identity_verification": 1,
        "allow_email_verification": 1,
        "allow_sms_verification": 1,
        "allow_whatsapp_verification": 0,
        "allow_telegram_verification": 0,
        "verification_code_length": 6,
        "verification_expiry_minutes": 10,
        "verification_resend_cooldown_seconds": 60,
        "verification_max_attempts": 5,
        "verification_email_subject": "رمز التحقق لهوية مقدم الشكوى",
        "allow_citizen_sms": 0,
        "allow_citizen_whatsapp": 0,
        "allow_citizen_telegram": 0,
        "allow_staff_sms": 0,
        "allow_staff_whatsapp": 0,
        "allow_staff_telegram": 0,
        "sms_auth_header": "Authorization",
        "sms_timeout": 10,
        "whatsapp_auth_header": "Authorization",
        "whatsapp_timeout": 10,
        "telegram_auth_header": "Authorization",
        "telegram_timeout": 10,
    }
    changed = False
    for fieldname, value in defaults.items():
        if doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)
            changed = True
    if changed:
        doc.save(ignore_permissions=True)


def create_ai_settings():
    if not frappe.db.exists("DocType", "Complaint AI Settings"):
        return

    doc = frappe.get_single("Complaint AI Settings")
    defaults = {
        "enable_ai": 0,
        "default_provider": "ChatGPT",
        "request_timeout": 60,
        "temperature": 0.2,
        "openai_model": "gpt-4o-mini",
        "openai_endpoint": "https://api.openai.com/v1/chat/completions",
        "deepseek_model": "deepseek-chat",
        "deepseek_endpoint": "https://api.deepseek.com/chat/completions",
        "gemini_model": "gemini-2.5-flash",
        "gemini_endpoint": "https://generativelanguage.googleapis.com/v1beta/models",
        "enable_intake_assistant": 1,
        "assistant_system_prompt": (
            "You are a smart intake advisor for Yemeni citizen complaints and appeals. "
            "Analyze, classify, extract entities, suggest priority and routing, and draft a professional advisory response."
        ),
    }
    changed = False
    for fieldname, value in defaults.items():
        if doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)
            changed = True
    if changed:
        doc.save(ignore_permissions=True)


def create_number_cards():
    cards = [
        {
            "name": "Open Complaint Cases",
            "label": "الحالات المفتوحة",
            "filters_json": json.dumps([["Complaint Case", "status", "in", ["New", "Under Review", "Assigned", "In Progress", "Waiting Citizen", "Overdue"], False]]),
        },
        {
            "name": "New Intake Cases",
            "label": "حالات جديدة",
            "filters_json": json.dumps([["Complaint Case", "status", "=", "New", False]]),
        },
        {
            "name": "Under Review Cases",
            "label": "قيد المراجعة",
            "filters_json": json.dumps([["Complaint Case", "status", "=", "Under Review", False]]),
        },
        {
            "name": "Waiting Citizen Cases",
            "label": "بانتظار المواطن",
            "filters_json": json.dumps([["Complaint Case", "status", "=", "Waiting Citizen", False]]),
        },
        {
            "name": "Overdue Complaint Cases",
            "label": "الحالات المتأخرة",
            "filters_json": json.dumps([["Complaint Case", "status", "=", "Overdue", False]]),
        },
        {
            "name": "Resolved Complaint Cases",
            "label": "الحالات المحسومة",
            "filters_json": json.dumps([["Complaint Case", "status", "in", ["Resolved", "Closed"], False]]),
        },
        {
            "name": "High Priority Complaint Cases",
            "label": "الحالات عالية الأولوية",
            "filters_json": json.dumps([["Complaint Case", "priority", "in", ["High", "Critical"], False]]),
        },
        {
            "name": "Appeal Cases",
            "label": "طلبات التظلم",
            "filters_json": json.dumps([["Complaint Case", "case_type", "=", "Appeal", False]]),
        },
    ]

    for card in cards:
        values = {
            "doctype": "Number Card",
            "name": card["name"],
            "label": card["label"],
            "module": "Complaints2",
            "document_type": "Complaint Case",
            "function": "Count",
            "is_public": 1,
            "show_percentage_stats": 1,
            "stats_time_interval": "Monthly",
            "filters_json": card["filters_json"],
        }
        upsert_doc("Number Card", card["name"], values)


def ensure_chart_sources():
    """Legacy installer hook retained for backward compatibility.

    Dashboard charts are now maintained as file-based records under
    yemen_complaints/complaints2/dashboard_chart/ and should be synced using
    migrate/reload-doc rather than being generated from installer code.
    """
    return



def create_dashboard_charts():
    """Legacy installer hook retained for backward compatibility.

    Dashboard charts are file-based records and are no longer created from the
    installer script.
    """
    return



def ensure_workflow_reference_records(state_names: list[str], action_names: list[str]):
    state_styles = {
        "New": "Warning",
        "Under Review": "Primary",
        "Assigned": "Primary",
        "In Progress": "Info",
        "Waiting Citizen": "Warning",
        "Resolved": "Success",
        "Rejected": "Danger",
        "Closed": "Inverse",
        "Overdue": "Danger",
    }

    state_map = {name: name for name in state_names}
    action_map = {name: name for name in action_names}

    if frappe.db.exists("DocType", "Workflow State"):
        meta = frappe.get_meta("Workflow State")
        fieldnames = {df.fieldname for df in meta.fields}
        lookup_fields = [f for f in ["workflow_state_name", "title", "label"] if f in fieldnames]

        for state_name in state_names:
            actual_name = state_name if frappe.db.exists("Workflow State", state_name) else None
            if not actual_name:
                for fieldname in lookup_fields:
                    actual_name = frappe.db.get_value("Workflow State", {fieldname: state_name}, "name")
                    if actual_name:
                        break

            if actual_name:
                state_map[state_name] = actual_name
                continue

            payload = {"doctype": "Workflow State"}
            if "workflow_state_name" in fieldnames:
                payload["workflow_state_name"] = state_name
            if "style" in fieldnames:
                payload["style"] = state_styles.get(state_name, "Primary")
            if "icon" in fieldnames:
                payload["icon"] = ""

            doc = frappe.get_doc(payload)
            doc.insert(ignore_permissions=True, ignore_links=True)
            state_map[state_name] = doc.name

    action_doctype = None
    if frappe.db.exists("DocType", "Workflow Action Master"):
        action_doctype = "Workflow Action Master"
    elif frappe.db.exists("DocType", "Workflow Action"):
        action_doctype = "Workflow Action"

    if action_doctype:
        meta = frappe.get_meta(action_doctype)
        fieldnames = {df.fieldname for df in meta.fields}
        lookup_fields = [f for f in ["workflow_action_name", "action_name", "label", "title"] if f in fieldnames]

        for action_name in action_names:
            actual_name = action_name if frappe.db.exists(action_doctype, action_name) else None
            if not actual_name:
                for fieldname in lookup_fields:
                    actual_name = frappe.db.get_value(action_doctype, {fieldname: action_name}, "name")
                    if actual_name:
                        break

            if actual_name:
                action_map[action_name] = actual_name
                continue

            payload = {"doctype": action_doctype}
            for fieldname in lookup_fields:
                payload[fieldname] = action_name

            doc = frappe.get_doc(payload)
            doc.insert(ignore_permissions=True, ignore_links=True)
            action_map[action_name] = doc.name

    frappe.db.commit()
    return state_map, action_map


def create_workflow():
    workflow_name = "Complaint Case Workflow"
    values = {
        "doctype": "Workflow",
        "name": workflow_name,
        "workflow_name": workflow_name,
        "document_type": "Complaint Case",
        "workflow_state_field": "status",
        "is_active": 1,
        "send_email_alert": 0,
        "override_status": 1,
    }

    states = [
        {"state": "New", "doc_status": 0, "allow_edit": ROLE_MAP["advisor"], "update_field": "status", "update_value": "New"},
        {"state": "Under Review", "doc_status": 0, "allow_edit": ROLE_MAP["advisor"], "update_field": "status", "update_value": "Under Review"},
        {"state": "Assigned", "doc_status": 0, "allow_edit": ROLE_MAP["agency"], "update_field": "status", "update_value": "Assigned"},
        {"state": "In Progress", "doc_status": 0, "allow_edit": ROLE_MAP["agency"], "update_field": "status", "update_value": "In Progress"},
        {"state": "Waiting Citizen", "doc_status": 0, "allow_edit": ROLE_MAP["agency"], "update_field": "status", "update_value": "Waiting Citizen"},
        {"state": "Resolved", "doc_status": 0, "allow_edit": ROLE_MAP["follow_up"], "update_field": "status", "update_value": "Resolved"},
        {"state": "Rejected", "doc_status": 0, "allow_edit": ROLE_MAP["advisor"], "update_field": "status", "update_value": "Rejected"},
        {"state": "Closed", "doc_status": 0, "allow_edit": ROLE_MAP["manager"], "update_field": "status", "update_value": "Closed"},
        {"state": "Overdue", "doc_status": 0, "allow_edit": ROLE_MAP["agency"], "update_field": "status", "update_value": "Overdue"},
    ]

    transition_specs = [
        ("New", "Review", "Under Review", [ROLE_MAP["advisor"], ROLE_MAP["manager"]]),
        ("Under Review", "Assign", "Assigned", [ROLE_MAP["advisor"], ROLE_MAP["manager"]]),
        ("Under Review", "Reject", "Rejected", [ROLE_MAP["advisor"], ROLE_MAP["manager"]]),
        ("Assigned", "Start Processing", "In Progress", [ROLE_MAP["agency"], ROLE_MAP["manager"]]),
        ("Assigned", "Return to Review", "Under Review", [ROLE_MAP["advisor"], ROLE_MAP["manager"]]),
        ("In Progress", "Request Citizen Input", "Waiting Citizen", [ROLE_MAP["agency"], ROLE_MAP["manager"]]),
        ("In Progress", "Mark Resolved", "Resolved", [ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]]),
        ("Waiting Citizen", "Resume Processing", "In Progress", [ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]]),
        ("Waiting Citizen", "Reject", "Rejected", [ROLE_MAP["advisor"], ROLE_MAP["manager"]]),
        ("Resolved", "Close Case", "Closed", [ROLE_MAP["follow_up"], ROLE_MAP["manager"]]),
        ("Resolved", "Reopen for Processing", "In Progress", [ROLE_MAP["follow_up"], ROLE_MAP["manager"]]),
        ("Overdue", "Resume Work", "In Progress", [ROLE_MAP["agency"], ROLE_MAP["follow_up"], ROLE_MAP["manager"]]),
        ("Overdue", "Escalated Closure", "Closed", [ROLE_MAP["manager"]]),
        ("Rejected", "Reopen", "Under Review", [ROLE_MAP["manager"]]),
        ("Closed", "Reopen", "Under Review", [ROLE_MAP["manager"]]),
    ]

    state_map, action_map = ensure_workflow_reference_records(
        state_names=[row["state"] for row in states],
        action_names=sorted({action for _, action, _, _ in transition_specs}),
    )

    try:
        doc = frappe.get_doc("Workflow", workflow_name)
        doc.update(values)
        doc.set("states", [])
        doc.set("transitions", [])
    except DoesNotExistError:
        doc = frappe.new_doc("Workflow")
        doc.update(values)

    transitions = []
    for state, action, next_state, roles in transition_specs:
        for role in roles:
            transitions.append({
                "state": state_map.get(state, state),
                "action": action_map.get(action, action),
                "next_state": state_map.get(next_state, next_state),
                "allowed": role,
            })

    for idx, state in enumerate(states, start=1):
        state_row = dict(state)
        state_row["state"] = state_map.get(state_row["state"], state_row["state"])
        doc.append("states", {"doctype": "Workflow Document State", "idx": idx, **state_row})
    for idx, transition in enumerate(transitions, start=1):
        doc.append("transitions", {"doctype": "Workflow Transition", "idx": idx, **transition})

    doc.save(ignore_permissions=True)


def create_workspaces():
    """Legacy installer hook retained for backward compatibility.

    Workspaces are maintained as file-based records under
    yemen_complaints/complaints2/workspace/.
    """
    return



def create_command_center_workspace():
    """Legacy installer hook retained for backward compatibility.

    The command center workspace is defined as a file-based record.
    """
    return



def build_command_center_links():
    """Legacy installer hook retained for backward compatibility."""
    return []



def upsert_named_doc(doctype: str, name: str, values: dict):
    payload = {"doctype": doctype, **values}
    upsert_doc(doctype, name, payload)


def upsert_doc(doctype: str, name: str, values: dict, ignore_links: bool = False):
    if frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        if ignore_links:
            doc.flags.ignore_links = True
        doc.save(ignore_permissions=True, ignore_version=True)
        return doc

    doc = frappe.get_doc(values)
    if not doc.name:
        doc.name = name
    if ignore_links:
        doc.flags.ignore_links = True
    doc.insert(ignore_permissions=True, ignore_links=ignore_links)
    return doc
