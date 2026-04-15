"""
Setup mandatory ticket creation fields:
  1) customer     -> Link to HD Customer (dropdown, agents only)
  2) customer_tag -> Link to HD Customer Tag (filtered by customer)
  3) ticket_type  -> "Mechanical", "Electrical", "Software" (admin-editable)
  4) attachment   -> file upload (already built into the editor)

Creates/updates the Default ticket template to make these fields visible and required.
Also adds "Customer Tags" link to the Helpdesk workspace.
"""
import frappe

def run():
    _setup_ticket_types()
    _setup_default_template()
    _setup_workspace_link()
    frappe.db.commit()
    print("Done.")


def _setup_ticket_types():
    """Ensure default problem types exist (admin can add/remove from desk)."""
    desired_types = ["Mechanical", "Electrical", "Software"]
    for t in desired_types:
        if not frappe.db.exists("HD Ticket Type", t):
            doc = frappe.new_doc("HD Ticket Type")
            doc.name = t
            doc.insert(ignore_permissions=True)
            print(f"  Created HD Ticket Type: {t}")
        else:
            print(f"  HD Ticket Type already exists: {t}")


def _setup_default_template():
    """Configure the Default ticket template with mandatory fields."""
    template_name = "Default"
    if frappe.db.exists("HD Ticket Template", template_name):
        tmpl = frappe.get_doc("HD Ticket Template", template_name)
    else:
        tmpl = frappe.new_doc("HD Ticket Template")
        tmpl.template_name = template_name
        tmpl.insert(ignore_permissions=True)
        print(f"  Created template: {template_name}")

    # Fields to show in ticket creation form
    required_fields = [
        {"fieldname": "customer", "required": 1, "hide_from_customer": 1, "placeholder": "Select customer"},
        {"fieldname": "customer_tag", "required": 1, "hide_from_customer": 0, "placeholder": "Select tag name"},
        {"fieldname": "ticket_type", "required": 1, "hide_from_customer": 0, "placeholder": "Select type of problem"},
        {"fieldname": "plant_modification", "required": 1, "hide_from_customer": 0, "placeholder": ""},
        {"fieldname": "modification_details", "required": 0, "hide_from_customer": 0, "placeholder": "Describe modifications made"},
    ]

    existing_fieldnames = [f.fieldname for f in tmpl.fields]

    for rf in required_fields:
        if rf["fieldname"] not in existing_fieldnames:
            tmpl.append("fields", rf)
            print(f"  Added template field: {rf['fieldname']}")
        else:
            for f in tmpl.fields:
                if f.fieldname == rf["fieldname"]:
                    f.required = rf["required"]
                    f.hide_from_customer = rf.get("hide_from_customer", 0)
                    if rf.get("placeholder"):
                        f.placeholder = rf["placeholder"]
            print(f"  Updated template field: {rf['fieldname']}")

    tmpl.save(ignore_permissions=True)
    print("  Default template saved with mandatory fields.")


def _setup_workspace_link():
    """Add 'Customer Tags' link to the Helpdesk workspace under Ticket Configuration."""
    try:
        workspace = frappe.get_doc("Workspace", "Helpdesk")
    except frappe.DoesNotExistError:
        print("  Helpdesk workspace not found, skipping link")
        return

    # Check if link already exists
    for link in workspace.links:
        if getattr(link, "link_to", None) == "HD Customer Tag":
            print("  Customer Tags link already in workspace")
            return

    # Find the Ticket Configuration section and add after existing links
    insert_idx = None
    for i, link in enumerate(workspace.links):
        if getattr(link, "label", None) == "Ticket Configuration":
            # Find the last link in this section (before next header)
            for j in range(i + 1, len(workspace.links)):
                if getattr(workspace.links[j], "type", None) == "Card Break":
                    insert_idx = j
                    break
            if insert_idx is None:
                insert_idx = len(workspace.links)
            break

    if insert_idx is not None:
        workspace.append("links", {
            "type": "Link",
            "link_type": "DocType",
            "link_to": "HD Customer Tag",
            "label": "Customer Tags",
        })
        workspace.save(ignore_permissions=True)
        print("  Added Customer Tags link to Helpdesk workspace")
    else:
        print("  Could not find Ticket Configuration section, skipping workspace link")
