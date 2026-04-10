#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

ADMIN_EMAIL = 'xu.yanrui1983@gmail.com'
SENDER_ACCOUNT = 'xu.yanrui1983@gmail.com'


def upsert_notification(name, document_type, event, subject, message, condition=None):
    if frappe.db.exists('Notification', name):
        n = frappe.get_doc('Notification', name)
        n.recipients = []
        print(f'Updating: {name}')
    else:
        n = frappe.new_doc('Notification')
        n.name = name
        print(f'Creating: {name}')

    n.enabled = 1
    n.channel = 'Email'
    n.document_type = document_type
    n.event = event
    n.subject = subject
    n.message_type = 'HTML'
    n.message = message
    n.condition = condition or ''
    n.send_to_all_assignees = 0
    n.sender = SENDER_ACCOUNT
    n.sender_email = ADMIN_EMAIL

    # recipient by role so Administrator receives it as System Manager
    n.append('recipients', {
        'receiver_by_role': 'System Manager'
    })

    if n.is_new():
        n.insert(ignore_permissions=True)
    else:
        n.save(ignore_permissions=True)


# 1) New Ticket created
upsert_notification(
    name='HD New Ticket Email to Admin',
    document_type='HD Ticket',
    event='New',
    subject='[Helpdesk] New Ticket: {{ doc.subject }} (#{{ doc.name }})',
    message='''
<p>A new ticket was created.</p>
<p><b>Ticket:</b> #{{ doc.name }}</p>
<p><b>Subject:</b> {{ doc.subject }}</p>
<p><b>Status:</b> {{ doc.status }}</p>
<p><b>Created By:</b> {{ doc.owner }}</p>
''',
)

# 2) Agent reply on ticket (Communication sent against HD Ticket)
upsert_notification(
    name='HD Agent Reply Email to Admin',
    document_type='Communication',
    event='New',
    subject='[Helpdesk] Agent Reply on Ticket #{{ doc.reference_name }}',
    message='''
<p>An agent reply was posted on a ticket.</p>
<p><b>Ticket:</b> #{{ doc.reference_name }}</p>
<p><b>From:</b> {{ doc.sender }}</p>
<p><b>Subject:</b> {{ doc.subject }}</p>
<p><b>Type:</b> {{ doc.sent_or_received }}</p>
''',
    condition='doc.reference_doctype=="HD Ticket" and doc.sent_or_received=="Sent"',
)

frappe.db.commit()

print('\n=== Notification Summary ===')
rows = frappe.get_all('Notification', fields=['name','document_type','event','enabled','channel','sender_email'], filters={'name': ['in', ['HD New Ticket Email to Admin','HD Agent Reply Email to Admin']]})
for r in rows:
    print(r)

# show recipients child rows
for nname in ['HD New Ticket Email to Admin','HD Agent Reply Email to Admin']:
    n = frappe.get_doc('Notification', nname)
    print(f'\n{nname} recipients:')
    for rec in n.recipients:
        print('  role=', rec.receiver_by_role, 'field=', rec.receiver_by_document_field)

frappe.destroy()
PY
