"""
Fix workspace: Move Customer Tags link into Ticket Configuration card.
Fix template: Ensure customer_tag is visible in customer portal.
"""
import frappe
import json


def run():
    _fix_workspace()
    _fix_template()
    frappe.db.commit()
    print("Done.")


def _fix_workspace():
    """Move Customer Tags into the Ticket Configuration card section."""
    workspace = frappe.get_doc("Workspace", "Helpdesk")

    # Remove any existing Customer Tags link
    workspace.links = [
        link for link in workspace.links
        if getattr(link, "link_to", None) != "HD Customer Tag"
    ]

    # Find the Ticket Configuration card break, then find General Settings link
    ticket_config_idx = None
    general_settings_idx = None
    for i, link in enumerate(workspace.links):
        if getattr(link, "label", None) == "Ticket Configuration" and getattr(link, "type", None) == "Card Break":
            ticket_config_idx = i
        if getattr(link, "link_to", None) == "HD Settings":
            general_settings_idx = i

    if general_settings_idx is not None:
        # Insert after General Settings (last item in Ticket Configuration)
        insert_at = general_settings_idx + 1
    elif ticket_config_idx is not None:
        insert_at = ticket_config_idx + 1
    else:
        insert_at = len(workspace.links)

    # Insert the new link at the correct position
    new_link = workspace.append("links", {})
    # Move it from the end to the correct position
    workspace.links.pop()  # remove from end
    workspace.links.insert(insert_at, new_link)
    new_link.type = "Link"
    new_link.link_type = "DocType"
    new_link.link_to = "HD Customer Tag"
    new_link.label = "Customer Tags"

    workspace.save(ignore_permissions=True)
    print("  Moved Customer Tags link into Ticket Configuration card")


def _fix_template():
    """Ensure customer_tag field is visible in customer portal (not hidden)."""
    if not frappe.db.exists("HD Ticket Template", "Default"):
        print("  No Default template found")
        return

    tmpl = frappe.get_doc("HD Ticket Template", "Default")
    for f in tmpl.fields:
        if f.fieldname == "customer_tag":
            f.hide_from_customer = 0
            f.required = 1
            print(f"  customer_tag: hide_from_customer={f.hide_from_customer}, required={f.required}")
        if f.fieldname == "customer":
            # Customer should be hidden from customer portal (auto-detected)
            f.hide_from_customer = 1
            f.required = 1

    tmpl.save(ignore_permissions=True)
    print("  Default template updated")
