import frappe

def run():
    import json
    print('site_config:', json.load(open('/home/frappe/frappe-bench/sites/helpdesk.localhost/site_config.json')))
    users = ['2310@iwt-project.com','2311@moldrup.com']
    for u in users:
        try:
            doc = frappe.get_doc('User', u)
            print('\nUSER', u)
            print(' enabled:', doc.enabled)
            print(' user_type:', doc.user_type)
            print(' username attr:', getattr(doc, 'username', None))
            print(' user_name attr:', getattr(doc, 'user_name', None))
            print(' roles:', [r.role for r in doc.roles])
        except Exception as e:
            print('Error for', u, e)
