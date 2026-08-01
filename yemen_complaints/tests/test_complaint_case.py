from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase


class TestComplaintCase(FrappeTestCase):
    def setUp(self):
        self.category_name = self.ensure_category()
        self.entity_name = self.ensure_entity()
        self.citizen_email = self.ensure_user("phase5.citizen@example.com", ["Citizen"])

    def tearDown(self):
        frappe.set_user("Administrator")

    def ensure_category(self):
        existing = frappe.db.get_value("Complaint Category", {"category_name_en": "Unit Test Category"}, "name")
        if existing:
            return existing

        return frappe.get_doc(
            {
                "doctype": "Complaint Category",
                "category_name_ar": "تصنيف اختباري",
                "category_name_en": "Unit Test Category",
                "default_priority": "High",
                "sla_first_response_hours": 12,
                "sla_resolution_days": 3,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True).name

    def ensure_entity(self):
        existing = frappe.db.get_value("Government Entity", {"entity_name_en": "Unit Test Entity"}, "name")
        if existing:
            return existing

        return frappe.get_doc(
            {
                "doctype": "Government Entity",
                "entity_name_ar": "جهة اختبارية",
                "entity_name_en": "Unit Test Entity",
                "entity_code": "UTE",
                "entity_type": "Other",
                "active": 1,
            }
        ).insert(ignore_permissions=True).name

    def ensure_user(self, email, roles):
        if not frappe.db.exists("User", email):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": email,
                    "first_name": email.split("@")[0],
                    "enabled": 1,
                    "new_password": "test123",
                    "roles": [{"role": role} for role in roles],
                }
            ).insert(ignore_permissions=True)
        return email

    def make_case(self, **overrides):
        payload = {
            "doctype": "Complaint Case",
            "case_type": "Complaint",
            "citizen_user": self.citizen_email,
            "citizen_full_name": "Test Citizen",
            "mobile_number": "777000111",
            "email": self.citizen_email,
            "category": self.category_name,
            "government_entity": self.entity_name,
            "subject": "اختبار حالة",
            "details": "تفاصيل اختبارية",
        }
        payload.update(overrides)
        return frappe.get_doc(payload)

    def test_case_gets_generated_name_and_defaults(self):
        doc = self.make_case()
        doc.insert(ignore_permissions=True)

        self.assertTrue(doc.name.startswith("CMP-"))
        self.assertEqual(doc.status, "New")
        self.assertIsNotNone(doc.target_resolution_date)

    def test_resolution_summary_required_for_resolved(self):
        doc = self.make_case()
        doc.insert(ignore_permissions=True)
        doc.status = "Resolved"

        with self.assertRaises(frappe.ValidationError):
            doc.save(ignore_permissions=True)

    def test_citizen_cannot_force_status_change(self):
        doc = self.make_case()
        doc.insert(ignore_permissions=True)

        frappe.set_user(self.citizen_email)
        doc = frappe.get_doc("Complaint Case", doc.name)
        doc.status = "Resolved"
        doc.resolution_summary = "Citizen should not be able to close this"

        with self.assertRaises(frappe.PermissionError):
            doc.save(ignore_permissions=True)
