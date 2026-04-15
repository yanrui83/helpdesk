import json

path = "apps/helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json"
with open(path) as f:
    doc = json.load(f)

fo = doc["field_order"]
ci = fo.index("customer")
print("Fields around customer:", fo[max(0,ci-2):ci+5])

# Check if customer_tag already exists
has_tag = any(f.get("fieldname") == "customer_tag" for f in doc["fields"])
print("customer_tag exists:", has_tag)

# Show customer field details
for f in doc["fields"]:
    if f.get("fieldname") == "customer":
        print("customer field:", json.dumps(f, indent=2))
