#!/bin/bash
python - <<'PY'
import imaplib
import email

user = 'xu.yanrui1983@gmail.com'
pwd = 'xmosascblvdmouzf'

imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
imap.login(user, pwd)

# Try common Sent folder names
folders_to_try = ['"[Gmail]/Sent Mail"', '"Sent"', '"INBOX.Sent"']
selected = None
for f in folders_to_try:
    try:
        status, _ = imap.select(f)
        if status == 'OK':
            selected = f
            break
    except Exception:
        pass

if not selected:
    print('Could not open Sent folder')
    imap.logout()
    raise SystemExit(1)

print('Using sent folder:', selected)

status, data = imap.search(None, 'ALL')
ids = data[0].split() if data and data[0] else []
print('Total sent messages:', len(ids))

# Fetch last 10 subjects
for msg_id in ids[-10:]:
    status, msg_data = imap.fetch(msg_id, '(RFC822.HEADER)')
    if status != 'OK':
        continue
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    subj = msg.get('Subject', '(no subject)')
    to = msg.get('To', '')
    dt = msg.get('Date', '')
    print(f'Subject: {subj} | To: {to} | Date: {dt}')

imap.logout()
PY
