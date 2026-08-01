from __future__ import annotations

from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate, today


class ComplaintSecurityEvent(Document):
    def autoname(self):
        if self.name and not str(self.name).startswith("New "):
            return
        year = getdate(today()).year
        self.name = make_autoname(f"SEC-{year}-.#####")
