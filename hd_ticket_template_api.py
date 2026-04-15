from typing import Literal
import json

import frappe

# from frappe import _
from pypika import JoinType

from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.utils import check_permissions, get_customer, is_agent

DOCTYPE_TEMPLATE = "HD Ticket Template"
DOCTYPE_TEMPLATE_FIELD = "HD Ticket Template Field"
DOCTYPE_TICKET = "HD Ticket"


@frappe.whitelist()
def get_one(name: str):
    check_permissions(DOCTYPE_TEMPLATE, None)
    found, about, description_template = frappe.get_value(
        DOCTYPE_TEMPLATE, name, ["name", "about", "description_template"]
    ) or [None, None, None]
    if not found:
        return {"about": None, "fields": []}

    fields = get_fields_meta(name)
    _inject_customer_tag_filter(fields)

    return {
        "about": about,
        "fields": fields,
        "description_template": description_template,
        "_form_script": get_form_script(
            "HD Ticket", apply_on_new_page=True, is_customer_portal=False
        ),
    }


def _inject_customer_tag_filter(fields):
    """For portal users, restrict the Tag Name dropdown to their own customer's tags only."""
    user = frappe.session.user
    # Skip for agents, Administrator, and Guest (unauthenticated)
    if is_agent() or user in ("Administrator", "Guest"):
        return
    customers = get_customer(user)
    if not customers:
        return
    for field in fields:
        if field.get("fieldname") == "customer_tag":
            field["link_filters"] = json.dumps(
                [["HD Customer Tag", "customer", "in", customers]]
            )
            break


def get_fields_meta(template: str):
    fields = get_fields(template, "DocField")
    fields.extend(get_fields(template, "Custom Field"))
    fields = sorted(fields, key=lambda x: x.idx)
    return fields


def get_fields(template: str, fetch: Literal["Custom Field", "DocField"]):
    QBField = frappe.qb.DocType(DOCTYPE_TEMPLATE_FIELD)
    QBFetch = frappe.qb.DocType(fetch)
    fields = (
        frappe.qb.from_(QBField)
        .select(QBField.star)
        .where(QBField.parent == template)
        .where(QBField.parentfield == "fields")
        .where(QBField.parenttype == DOCTYPE_TEMPLATE)
    )
    where_parent = QBFetch.parent == DOCTYPE_TICKET
    if fetch == "Custom Field":
        where_parent = QBFetch.dt == DOCTYPE_TICKET
    result = (
        frappe.qb.from_(fields)
        .select(
            QBFetch.description,
            QBFetch.fieldtype,
            QBFetch.label,
            QBFetch.options,
            QBFetch.link_filters,
            QBFetch.depends_on,
            QBFetch.mandatory_depends_on,
            fields.fieldname,
            fields.hide_from_customer,
            fields.required,
            fields.url_method,
            fields.placeholder,
            fields.idx,
        )
        .join(QBFetch, JoinType.inner)
        .on(QBFetch.fieldname == fields.fieldname)
        .where(where_parent)
        .orderby(fields.idx)
        .run(as_dict=True)
    )
    docfields = ["link_filters", "depends_on", "mandatory_depends_on"]

    for df in docfields:
        for field in result:
            property_setter_id = "HD Ticket" + "-" + field.fieldname + "-" + df
            if frappe.db.exists("Property Setter", property_setter_id):
                field[df] = frappe.get_value(
                    "Property Setter", property_setter_id, "value"
                )
    return result
