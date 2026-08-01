from __future__ import annotations

from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ComplaintCategory(Document):
    def autoname(self):
        if self.name and not str(self.name).startswith("New "):
            return
        self.name = ((self.category_name_en or self.category_name_ar or "").strip() or make_autoname("CCAT-.#####"))
