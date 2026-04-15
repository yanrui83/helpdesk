"""
Patch HD Ticket doctype JSON to add plant_modification and modification_details fields.
"""
import json
import sys

path = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json"

with open(path) as f:
    doc = json.load(f)

# Check if already patched
if any(f.get("fieldname") == "plant_modification" for f in doc["fields"]):
    print("plant_modification field already exists in HD Ticket, skipping")
    sys.exit(0)

# Find customer_tag position (insert after it)
fo = doc["field_order"]
if "customer_tag" in fo:
    idx = fo.index("customer_tag") + 1
elif "ticket_type" in fo:
    idx = fo.index("ticket_type") + 1
else:
    idx = len(fo)

fo.insert(idx, "plant_modification")
fo.insert(idx + 1, "modification_details")

# Add field definitions
new_fields = [
    {
        "fieldname": "plant_modification",
        "fieldtype": "Select",
        "label": "Any modification made prior to this issue?",
        "options": "\nYes\nNo"
    },
    {
        "fieldname": "modification_details",
        "fieldtype": "Text",
        "label": "Modification Details",
        "depends_on": "eval:doc.plant_modification==\"Yes\""
    }
]

# Insert after customer_tag in fields array
insert_after = "customer_tag" if any(f.get("fieldname") == "customer_tag" for f in doc["fields"]) else "ticket_type"
insert_idx = next(
    (i for i, f in enumerate(doc["fields"]) if f.get("fieldname") == insert_after),
    len(doc["fields"]) - 1
)

for i, field in enumerate(new_fields):
    doc["fields"].insert(insert_idx + 1 + i, field)

with open(path, "w") as f:
    json.dump(doc, f, indent=1, ensure_ascii=False)

print("plant_modification and modification_details fields added to HD Ticket")
