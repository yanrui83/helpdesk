import frappe

def run():
    fields = frappe.get_all(
        "HD Ticket Template Field",
        filters={"parent": "Default"},
        fields=["fieldname", "hide_from_customer", "required"],
        order_by="idx",
    )
    for f in fields:
        print(f"{f.fieldname}: hide={f.hide_from_customer}, req={f.required}")

    # Also check if customer_tag depends_on in hd_ticket meta
    meta = frappe.get_meta("HD Ticket")
    for field in ["customer", "customer_tag", "ticket_type"]:
        df = meta.get_field(field)
        if df:
            print(f"\nHD Ticket.{field}: depends_on={df.depends_on}, hidden={df.hidden}, options={df.options}")
