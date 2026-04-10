#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

# Update the email account password with the App Password
email_account = 'xu.yanrui1983@gmail.com'
app_password = 'xmosascblvdmouzf'

doc = frappe.get_doc('Email Account', email_account)
doc.password = app_password
doc.flags.ignore_validate = True
doc.flags.ignore_permissions = True
doc.save(ignore_permissions=True)
frappe.db.commit()
print(f'Updated password for {email_account}')

# Now test outgoing (SMTP)
print()
print('=== Testing SMTP connection ===')
try:
    import smtplib
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login('xu.yanrui1983@gmail.com', app_password)
    print('SMTP login SUCCESS')
    server.quit()
except Exception as e:
    print(f'SMTP error: {e}')

# Test incoming (IMAP)
print()
print('=== Testing IMAP connection ===')
try:
    import imaplib
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login('xu.yanrui1983@gmail.com', app_password)
    print('IMAP login SUCCESS')
    status, folders = mail.list()
    print(f'Folders found: {len(folders)}')
    mail.logout()
except Exception as e:
    print(f'IMAP error: {e}')

# Test sending a test email via Frappe
print()
print('=== Sending test email via Frappe ===')
try:
    frappe.sendmail(
        recipients=['xu.yanrui1983@gmail.com'],
        subject='Helpdesk Email Test',
        message='<p>This is a test email from your Frappe Helpdesk to confirm email is working.</p>',
        now=True,
    )
    print('Test email SENT successfully!')
except Exception as e:
    print(f'Send error: {e}')

frappe.destroy()
"
