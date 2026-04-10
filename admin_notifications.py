import frappe
from frappe import _


def _get_admin_email() -> str:
    email = frappe.db.get_value("User", "Administrator", "email")
    return (email or "").strip()


def _send_now(subject: str, message: str):
    admin_email = _get_admin_email()
    if not admin_email:
        frappe.logger().warning("Admin notification skipped: Administrator email not set")
        return

    try:
        frappe.sendmail(
            recipients=[admin_email],
            subject=subject,
            message=message,
            now=True,
        )
        # In this Docker setup, queue workers can be delayed; force immediate flush.
        from frappe.email.queue import flush

        flush()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Admin notification send failed")


def notify_admin_new_ticket(doc, method=None):
    """Immediate email to Administrator when a new HD Ticket is created."""
    try:
        subject = f"[Helpdesk] New Ticket: {doc.subject} (#{doc.name})"
        message = f"""
<p>A new ticket was created.</p>
<p><b>Ticket:</b> #{doc.name}</p>
<p><b>Subject:</b> {doc.subject or ''}</p>
<p><b>Status:</b> {doc.status or ''}</p>
<p><b>Raised By:</b> {doc.raised_by or doc.owner or ''}</p>
"""
        _send_now(subject, message)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "notify_admin_new_ticket failed")


def notify_admin_agent_reply(doc, method=None):
    """Immediate email to Administrator when an agent sends a reply on HD Ticket."""
    try:
        if doc.reference_doctype != "HD Ticket":
            return
        if doc.sent_or_received != "Sent":
            return

        subject = f"[Helpdesk] Agent Reply on Ticket #{doc.reference_name}"
        message = f"""
<p>An agent reply was posted on a ticket.</p>
<p><b>Ticket:</b> #{doc.reference_name or ''}</p>
<p><b>From:</b> {doc.sender or ''}</p>
<p><b>Subject:</b> {doc.subject or ''}</p>
"""
        _send_now(subject, message)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "notify_admin_agent_reply failed")
