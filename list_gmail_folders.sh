#!/bin/bash
python - <<'PY'
import imaplib

user = 'xu.yanrui1983@gmail.com'
pwd = 'xmosascblvdmouzf'

imap = imaplib.IMAP4_SSL('imap.gmail.com', 993)
imap.login(user, pwd)
status, boxes = imap.list()
print('LIST status:', status)
for b in boxes or []:
    print(b.decode(errors='ignore'))
imap.logout()
PY
