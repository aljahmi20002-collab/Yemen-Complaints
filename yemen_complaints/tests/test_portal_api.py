from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPortalAPI(FrappeTestCase):
    def setUp(self):
        self.user_email = "citizen.test@example.com"
        if not frappe.db.exists("User", self.user_email):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.user_email,
                    "first_name": "Citizen",
                    "last_name": "Tester",
                    "enabled": 1,
                    "new_password": "test123",
                    "roles": [{"role": "Citizen"}],
                }
            ).insert(ignore_permissions=True)

        category_name = frappe.get_all("Complaint Category", fields=["name"], limit=1)[0].name
        entity_name = frappe.get_all("Government Entity", fields=["name"], limit=1)[0].name

        self.case_name = frappe.get_doc(
            {
                "doctype": "Complaint Case",
                "case_type": "Complaint",
                "citizen_user": self.user_email,
                "citizen_full_name": "Portal Citizen",
                "mobile_number": "777123456",
                "email": self.user_email,
                "category": category_name,
                "government_entity": entity_name,
                "subject": "Portal API Test Case",
                "details": "Portal API details",
            }
        ).insert(ignore_permissions=True).name

    def test_get_my_cases(self):
        frappe.set_user(self.user_email)
        rows = frappe.get_attr("yemen_complaints.api.get_my_cases")()
        self.assertTrue(any(row.get("name") == self.case_name for row in rows))
        frappe.set_user("Administrator")
