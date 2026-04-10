#!/usr/bin/env python3
"""
Add a customer user to Frappe Helpdesk with a manually set password.

Usage (inside container):
    python /workspace/add_customer.py --email user@example.com --first-name John --last-name Doe --password secret123

Run from host:
    docker compose exec frappe python /workspace/add_customer.py --email user@example.com --first-name John --password secret123
"""

import argparse
import os
import sys

SITE = "helpdesk.localhost"
BENCH_PATH = "/home/frappe/frappe-bench"

sys.path.insert(0, os.path.join(BENCH_PATH, "apps", "frappe"))
os.chdir(BENCH_PATH)

import frappe
from frappe.utils.password import update_password


def add_customer(email: str, first_name: str, last_name: str, password: str) -> None:
    frappe.init(site=SITE, sites_path=os.path.join(BENCH_PATH, "sites"))
    frappe.connect()

    try:
        if frappe.db.exists("User", email):
            print(f"[ERROR] User '{email}' already exists.")
            sys.exit(1)

        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.send_welcome_email = 0
        user.enabled = 1
        user.append("roles", {"role": "Customer"})
        user.insert(ignore_permissions=True)

        # Set password separately — avoids hashing issues with new_password field
        update_password(email, password)

        frappe.db.commit()
        print(f"[OK] Customer '{first_name} {last_name}' ({email}) created successfully.")
        print(f"     Login at: http://localhost:8000/helpdesk")
    finally:
        frappe.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a customer to Frappe Helpdesk")
    parser.add_argument("--email",      required=True,  help="Customer email (used as login)")
    parser.add_argument("--first-name", required=True,  help="First name")
    parser.add_argument("--last-name",  default="",     help="Last name (optional)")
    parser.add_argument("--password",   required=True,  help="Password to assign")
    args = parser.parse_args()

    add_customer(args.email, args.first_name, args.last_name, args.password)
