"""
Equipment 3D Viewer API — Frappe endpoints for HD Equipment.
Manages equipment records, 3D model configs, and spare part orders.
"""

import json

import frappe
from frappe import _


def _is_agent() -> bool:
    user_roles = frappe.get_roles(frappe.session.user)
    return "Agent" in user_roles or "System Manager" in user_roles or frappe.session.user == "Administrator"


def _get_customer_for_user() -> str | None:
    """Get the HD Customer linked to the current portal user via Contact email."""
    user = frappe.session.user
    if user == "Administrator" or user == "Guest":
        return None

    contact = frappe.db.get_value("Contact", {"user": user}, "name")
    if not contact:
        return None

    links = frappe.get_all(
        "Dynamic Link",
        filters={"parent": contact, "parenttype": "Contact", "link_doctype": "HD Customer"},
        fields=["link_name"],
        limit=1,
    )
    return links[0].link_name if links else None


@frappe.whitelist(allow_guest=False)
def has_equipment():
    """Check if the current portal user has any active equipment assigned."""
    if _is_agent():
        return True
    customer = _get_customer_for_user()
    if not customer:
        return False
    return frappe.db.exists("HD Equipment", {"customer": customer, "is_active": 1}) is not None


@frappe.whitelist()
def get_equipment_list():
    """List equipment. Agents see all; customers see only their own."""
    filters = {"is_active": 1}

    if not _is_agent():
        customer = _get_customer_for_user()
        if not customer:
            return []
        filters["customer"] = customer

    equipment = frappe.get_all(
        "HD Equipment",
        filters=filters,
        fields=["name", "equipment_name", "customer", "model_file", "is_active", "modified"],
        order_by="modified desc",
    )

    for eq in equipment:
        # Get customer name for display
        eq["customer_name"] = frappe.db.get_value("HD Customer", eq["customer"], "customer_name") or eq["customer"]

    return equipment


@frappe.whitelist()
def get_equipment(equipment_id: str):
    """Get single equipment with config and model URL."""
    if not equipment_id:
        frappe.throw(_("Equipment ID is required"))

    doc = frappe.get_doc("HD Equipment", equipment_id)

    # Permission check: customers can only see their own equipment
    if not _is_agent():
        customer = _get_customer_for_user()
        if not customer or doc.customer != customer:
            frappe.throw(_("You do not have access to this equipment"), frappe.PermissionError)

    return {
        "name": doc.name,
        "equipment_name": doc.equipment_name,
        "customer": doc.customer,
        "customer_name": frappe.db.get_value("HD Customer", doc.customer, "customer_name") or doc.customer,
        "model_file": doc.model_file,
        "config": doc.config or "",
        "is_active": doc.is_active,
    }


@frappe.whitelist()
def save_equipment_config(equipment_id: str, config: str):
    """Save editor config changes. Agent only."""
    if not _is_agent():
        frappe.throw(_("Only agents can edit equipment configurations"), frappe.PermissionError)

    if not equipment_id:
        frappe.throw(_("Equipment ID is required"))

    # Validate JSON
    try:
        parsed = json.loads(config)
    except (json.JSONDecodeError, TypeError):
        frappe.throw(_("Invalid JSON configuration"))

    doc = frappe.get_doc("HD Equipment", equipment_id)
    doc.config = json.dumps(parsed)
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "ok", "message": "Configuration saved"}


@frappe.whitelist()
def submit_spare_part_order(equipment_id: str, cart_items: str):
    """Submit a spare part order — creates an HD Ticket with order details."""
    if not equipment_id or not cart_items:
        frappe.throw(_("Equipment ID and cart items are required"))

    try:
        items = json.loads(cart_items)
    except (json.JSONDecodeError, TypeError):
        frappe.throw(_("Invalid cart data"))

    if not items:
        frappe.throw(_("Cart is empty"))

    doc = frappe.get_doc("HD Equipment", equipment_id)

    # Permission check
    if not _is_agent():
        customer = _get_customer_for_user()
        if not customer or doc.customer != customer:
            frappe.throw(_("You do not have access to this equipment"), frappe.PermissionError)

    # Build order description
    total = 0
    lines = [f"**Spare Part Order — {doc.equipment_name}**\n"]
    lines.append("| Part | SKU | Qty | Unit Price | Total |")
    lines.append("|------|-----|-----|-----------|-------|")

    for item in items:
        name = item.get("name", "Unknown")
        sku = item.get("sku", "")
        qty = int(item.get("qty", 1))
        price = float(item.get("price", 0))
        line_total = qty * price
        total += line_total
        lines.append(f"| {name} | {sku} | {qty} | ${price:,.2f} | ${line_total:,.2f} |")

    lines.append(f"\n**Order Total: ${total:,.2f}**")
    lines.append(f"\nEquipment: {doc.equipment_name} ({doc.name})")

    description = "\n".join(lines)

    # Create ticket
    ticket = frappe.get_doc({
        "doctype": "HD Ticket",
        "subject": f"Spare Part Order — {doc.equipment_name}",
        "description": description,
        "raised_by": frappe.session.user,
    })
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "ok",
        "ticket_id": ticket.name,
        "message": f"Order submitted as ticket {ticket.name}",
    }
