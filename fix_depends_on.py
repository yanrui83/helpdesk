import frappe
import json

def run():
    """Remove depends_on from customer_tag field so it shows in customer portal.
    Also set link_filters on the template field to filter by customer."""
    
    # 1. Remove depends_on from customer_tag in HD Ticket doctype
    _fix_depends_on()
    
    # 2. Set link_filters on template field for customer_tag
    _fix_template_link_filters()
    
    frappe.db.commit()
    print("Done.")


def _fix_depends_on():
    """Remove depends_on from customer_tag field in hd_ticket.json"""
    meta = frappe.get_meta("HD Ticket")
    df = meta.get_field("customer_tag")
    if not df:
        print("customer_tag field not found in HD Ticket")
        return
    
    # Check if it's a Custom Field
    if frappe.db.exists("Custom Field", {"dt": "HD Ticket", "fieldname": "customer_tag"}):
        cf = frappe.get_doc("Custom Field", {"dt": "HD Ticket", "fieldname": "customer_tag"})
        cf.depends_on = ""
        cf.save()
        print(f"Custom Field customer_tag: cleared depends_on")
    else:
        # It's a DocField - update via JSON
        json_path = frappe.get_app_path("helpdesk", "helpdesk", "doctype", "hd_ticket", "hd_ticket.json")
        with open(json_path, "r") as f:
            doctype_json = json.load(f)
        
        for field in doctype_json.get("fields", []):
            if field.get("fieldname") == "customer_tag":
                field["depends_on"] = ""
                print(f"DocField customer_tag: cleared depends_on in JSON")
                break
        
        with open(json_path, "w") as f:
            json.dump(doctype_json, f, indent=1, sort_keys=True)
        
        # Also clear via Property Setter if it exists
        ps_name = "HD Ticket-customer_tag-depends_on"
        if frappe.db.exists("Property Setter", ps_name):
            frappe.delete_doc("Property Setter", ps_name)
            print(f"Deleted Property Setter: {ps_name}")


def _fix_template_link_filters():
    """Set link_filters on customer_tag template field to filter by customer."""
    template_fields = frappe.get_all(
        "HD Ticket Template Field",
        filters={"parent": "Default", "fieldname": "customer_tag"},
        fields=["name", "link_filters"]
    )
    
    if not template_fields:
        print("customer_tag not found in Default template")
        return
    
    tf = frappe.get_doc("HD Ticket Template Field", template_fields[0].name)
    # Filter customer tags by the selected customer
    tf.link_filters = json.dumps([["HD Customer Tag", "customer", "=", ""]])
    tf.save()
    print(f"Set link_filters on template field customer_tag")
