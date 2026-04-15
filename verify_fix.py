import frappe

def run():
    meta = frappe.get_meta("HD Ticket")
    df = meta.get_field("customer_tag")
    print(f"customer_tag depends_on={repr(df.depends_on)}")
