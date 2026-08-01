from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class GovernmentEntity(Document):
    def autoname(self):
        if self.name and not str(self.name).startswith("New "):
            return
        self.name = ((self.entity_code or self.entity_name_en or self.entity_name_ar or "").strip() or make_autoname("GENT-.#####"))

    def validate(self):
        if self.district and not self.governorate:
            frappe.throw(_('District requires a governorate to be selected first.'))

        if self.district and self.governorate:
            district_governorate = frappe.db.get_value('Yemen District', self.district, 'governorate')
            if district_governorate and district_governorate != self.governorate:
                frappe.throw(_('Selected district does not belong to the selected governorate.'))
