import frappe
from frappe.model.document import Document


class HDEquipment(Document):
    def after_insert(self):
        self._make_model_file_public()

    def on_update(self):
        self._make_model_file_public()

    def _make_model_file_public(self):
        """Ensure the uploaded 3D model file is stored as a public file so the viewer can load it."""
        if not self.model_file:
            return
        # Only process Frappe-uploaded private files (not static asset paths)
        if not self.model_file.startswith("/private/files/"):
            return
        try:
            file_doc = frappe.get_doc("File", {"file_url": self.model_file, "is_private": 1})
            file_doc.is_private = 0
            file_doc.save(ignore_permissions=True)
            # Update our record to use the public URL
            public_url = self.model_file.replace("/private/files/", "/files/")
            frappe.db.set_value("HD Equipment", self.name, "model_file", public_url)
            frappe.db.commit()
        except frappe.DoesNotExistError:
            pass
