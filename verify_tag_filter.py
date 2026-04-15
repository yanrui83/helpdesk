import frappe
import json

def run():
    from helpdesk.utils import get_customer
    users = ["2311@moldrup.com", "2310@iwt-project.com"]
    for u in users:
        customers = get_customer(u)
        print(f"{u} -> customers: {customers}")
        if customers:
            tags = frappe.get_all(
                "HD Customer Tag",
                filters={"customer": ["in", customers]},
                fields=["name", "customer", "tag_name"],
            )
            print(f"  visible tags: {[t.tag_name for t in tags]}")
        else:
            print("  no customer linked!")
