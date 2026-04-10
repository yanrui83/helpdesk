#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

email = 'xu.yanrui1983@gmail.com'
password = 'Yanrui_123!'

# Step 1: Update Administrator user email
admin = frappe.get_doc('User', 'Administrator')
# Check if email already in user_emails table
print('=== Step 1: Update Administrator email ===')

# Step 2: Create Email Account for helpdesk
print('=== Step 2: Create Email Account ===')

# Check if account already exists
existing = frappe.db.exists('Email Account', {'email_id': email})
if existing:
    print(f'Email account already exists: {existing}')
    doc = frappe.get_doc('Email Account', existing)
    # Update it
    doc.enable_incoming = 1
    doc.enable_outgoing = 1
    doc.default_outgoing = 1
    doc.default_incoming = 1
    doc.email_id = email
    doc.password = password
    doc.smtp_server = 'smtp.gmail.com'
    doc.smtp_port = 587
    doc.use_tls = 1
    doc.use_imap = 1
    doc.email_server = 'imap.gmail.com'
    doc.incoming_port = 993
    doc.use_ssl = 1
    doc.notify_if_unreplied = 1
    doc.send_notification_to = email
    doc.create_contact = 1
    doc.enable_auto_reply = 0
    doc.append_to = 'HD Ticket'
    doc.flags.ignore_validate = True
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    print(f'Updated existing email account: {doc.name}')
else:
    doc = frappe.new_doc('Email Account')
    doc.email_account_name = 'Helpdesk Support'
    doc.email_id = email
    doc.password = password
    doc.domain = 'GMail'

    # Outgoing (SMTP)
    doc.enable_outgoing = 1
    doc.default_outgoing = 1
    doc.smtp_server = 'smtp.gmail.com'
    doc.smtp_port = 587
    doc.use_tls = 1

    # Incoming (IMAP)
    doc.enable_incoming = 1
    doc.default_incoming = 1
    doc.use_imap = 1
    doc.email_server = 'imap.gmail.com'
    doc.incoming_port = 993
    doc.use_ssl = 1

    # Helpdesk settings
    doc.append_to = 'HD Ticket'
    doc.notify_if_unreplied = 1
    doc.send_notification_to = email
    doc.create_contact = 1
    doc.enable_auto_reply = 0

    doc.flags.ignore_validate = True
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    print(f'Created email account: {doc.name}')

# Step 3: Set outgoing email settings in site config
print('=== Step 3: Update Notification Settings ===')

# Set HD Settings to use this email for notifications
try:
    hd_settings = frappe.get_doc('HD Settings')
    # If there's an email field on HD Settings
    print(f'HD Settings loaded: {hd_settings.name}')
except Exception as e:
    print(f'HD Settings: {e}')

# Step 4: Set Administrator email
print('=== Step 4: Set Administrator email ===')
admin = frappe.get_doc('User', 'Administrator')
admin.email = email
admin.flags.ignore_validate = True
admin.flags.ignore_permissions = True
admin.save(ignore_permissions=True)
print(f'Administrator email set to: {email}')

# Step 5: Create/update Email Domain for Gmail
print('=== Step 5: Check Email Domain ===')
gmail_domain = frappe.db.exists('Email Domain', 'GMail')
if gmail_domain:
    print('GMail domain already exists')
else:
    print('Creating GMail domain...')
    domain = frappe.new_doc('Email Domain')
    domain.domain_name = 'GMail'
    domain.email_server = 'imap.gmail.com'
    domain.use_imap = 1
    domain.incoming_port = 993
    domain.use_ssl = 1
    domain.smtp_server = 'smtp.gmail.com'
    domain.smtp_port = 587
    domain.use_tls = 1
    domain.flags.ignore_validate = True
    domain.insert(ignore_permissions=True)
    print('GMail domain created')

frappe.db.commit()
print()
print('=== DONE ===')
print(f'Email Account: Helpdesk Support ({email})')
print('Default Outgoing: Yes')
print('Default Incoming: Yes')
print('Append To: HD Ticket')
print('All notifications will be sent from this email.')

frappe.destroy()
"
