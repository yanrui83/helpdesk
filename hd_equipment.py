import os
import shutil
import frappe
from frappe.model.document import Document


class HDEquipment(Document):
    def before_save(self):
        """Delete the old file from disk when the model is replaced."""
        if not self.is_new():
            old_url = frappe.db.get_value("HD Equipment", self.name, "model_file")
            if old_url and old_url != self.model_file:
                self._delete_model_file(old_url)

    def after_insert(self):
        self._make_model_file_public()

    def on_update(self):
        self._make_model_file_public()

    def _delete_model_file(self, file_url):
        """Remove the old File doc and physical file so re-upload of same name works."""
        if not file_url:
            return
        try:
            file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
            if file_name:
                frappe.delete_doc("File", file_name, ignore_permissions=True)
        except Exception:
            pass
        # Also remove the physical file
        try:
            site_path = frappe.get_site_path()
            if file_url.startswith("/files/"):
                phys = os.path.join(site_path, "public", "files", os.path.basename(file_url))
            elif file_url.startswith("/private/files/"):
                phys = os.path.join(site_path, "private", "files", os.path.basename(file_url))
            else:
                return
            if os.path.exists(phys):
                os.remove(phys)
        except Exception:
            pass

    def _make_model_file_public(self):
        """Move uploaded private GLB to public/files so the 3D viewer can load it."""
        if not self.model_file or not self.model_file.startswith("/private/files/"):
            return
        try:
            fname = os.path.basename(self.model_file)
            site_path = frappe.get_site_path()
            src = os.path.join(site_path, "private", "files", fname)
            dst_dir = os.path.join(site_path, "public", "files")
            dst = os.path.join(dst_dir, fname)
            os.makedirs(dst_dir, exist_ok=True)
            if os.path.exists(src):
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
            public_url = "/files/" + fname
            # Update the File doc
            file_doc_name = frappe.db.get_value("File", {"file_url": self.model_file}, "name")
            if file_doc_name:
                frappe.db.set_value("File", file_doc_name, {"is_private": 0, "file_url": public_url})
            # Update our own record
            frappe.db.set_value("HD Equipment", self.name, "model_file", public_url)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(str(e), "HD Equipment make_public")
