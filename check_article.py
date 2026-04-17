import frappe, os
os.chdir("/home/frappe/frappe-bench/sites")
frappe.init(site="helpdesk.localhost")
frappe.connect()
articles = frappe.get_all("HD Article", filters={"title": ["like", "%SCADA%"]}, fields=["name", "title", "category"], limit=5)
print("Found:", len(articles))
for a in articles:
    print(f"name={a.name}, title={a.title}, category={a.category}")
if not articles:
    articles = frappe.get_all("HD Article", fields=["name", "title"], limit=10)
    print("All articles (first 10):")
    for a in articles:
        print(f"  name={a.name}, title={a.title}")
frappe.destroy()
