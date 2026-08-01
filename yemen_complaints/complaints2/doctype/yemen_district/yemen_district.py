from __future__ import annotations

from frappe.model.document import Document
from frappe.model.naming import make_autoname


class YemenDistrict(Document):
    def autoname(self):
        if self.name and not str(self.name).startswith("New "):
            return
        base_name = (self.reference_name or self.district_name_en or self.district_name_ar or "").strip()
        if self.governorate and base_name:
            self.name = f"{self.governorate}-{base_name}"
        else:
            self.name = base_name or make_autoname("YDIST-.#####")
