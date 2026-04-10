#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import imaplib
import email
import frappe
from frappe.utils import now_datetime

USER = 'xu.yanrui1983@gmail.com'
PWD = 'xmosascblvdmouzf'

# 1) Send unique email from Frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')
subject = f'Helpdesk Trace {now_datetime()}'
try:
    frappe.sendmail(
        recipients=[USER],
        sender=USER,
        subject=subject,
        message='<p>Trace test message.</p>',
        now=True,
    )
    print('Frappe sendmail completed:', subject)
except Exception as e:
    print('Frappe sendmail error:', e)
frappe.destroy()

# 2) Check IMAP folder counts + search for subject in All Mail
imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
imap.login(USER, PWD)

folders = ['INBOX', '"[Gmail]/All Mail"', '"[Gmail]/Sent Mail"', '"[Gmail]/Spam"']
print('\nFolder counts:')
for f in folders:
    st, data = imap.select(f, readonly=True)
    if st == 'OK':
        total = int(data[0]) if data and data[0] else 0
        print(f'  {f}: {total}')
    else:
        print(f'  {f}: select failed')

imap.select('"[Gmail]/All Mail"', readonly=True)
st, data = imap.search(None, 'SUBJECT', f'"{subject}"')
ids = data[0].split() if st == 'OK' and data and data[0] else []
print('\nTrace subject found in All Mail:', len(ids))
if ids:
    mid = ids[-1]
    st, msg_data = imap.fetch(mid, '(RFC822.HEADER)')
    if st == 'OK' and msg_data and msg_data[0]:
        msg = email.message_from_bytes(msg_data[0][1])
        print('Matched message headers:')
        print('  Subject:', msg.get('Subject'))
        print('  From:', msg.get('From'))
        print('  To:', msg.get('To'))
        print('  Date:', msg.get('Date'))

imap.logout()
PY
