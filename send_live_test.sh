#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

subject = f'Helpdesk Real Send {now_datetime()}'
print('Sending subject:', subject)

frappe.sendmail(
    recipients=['xu.yanrui1983@gmail.com'],
    sender='xu.yanrui1983@gmail.com',
    subject=subject,
    message='<p>Real send test after unmuting emails.</p>',
    now=True,
)
print('sendmail done')

rows = frappe.get_all('Email Queue', fields=['name','status','sender','creation'], order_by='creation desc', limit=5)
print('Recent queue rows:', rows)

frappe.destroy()
PY
