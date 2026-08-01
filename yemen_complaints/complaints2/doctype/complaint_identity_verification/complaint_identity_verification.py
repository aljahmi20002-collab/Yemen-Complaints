from __future__ import annotations

from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, today


class ComplaintIdentityVerification(Document):
    def autoname(self):
        year = getdate(today()).year
        self.name = make_autoname(f"CIV-{year}-.#####")
