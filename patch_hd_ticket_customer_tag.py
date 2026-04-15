"""
Patch HD Ticket doctype JSON to add customer_tag field after the customer field.
"""
import json
import sys

path = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json"

with open(path) as f:
    doc = json.load(f)

# Check if already patched
if any(f.get("fieldname") == "customer_tag" for f in doc["fields"]):
    print("customer_tag field already exists in HD Ticket, skipping")
    sys.exit(0)

# Add to field_order after 'customer'
fo = doc["field_order"]
if "customer" in fo:
    idx = fo.index("customer") + 1
    fo.insert(idx, "customer_tag")
else:
    fo.append("customer_tag")

# Add field definition after customer in the fields array
new_field = {
    "fieldname": "customer_tag",
    "fieldtype": "Link",
    "label": "Tag Name",
    "options": "HD Customer Tag"
}

customer_idx = next(
    (i for i, f in enumerate(doc["fields"]) if f.get("fieldname") == "customer"),
    len(doc["fields"])
)
doc["fields"].insert(customer_idx + 1, new_field)

with open(path, "w") as f:
    json.dump(doc, f, indent=1, ensure_ascii=False)

print("customer_tag field added to HD Ticket")
