#!/usr/bin/env python3
"""
Patch doc.py: get_list_data → get_options
When building group_by labels, check for parent_category field and prefix
sub-category labels with their parent's name ("Automation > HMI").
"""
import re

FILE = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/doc.py"

with open(FILE, "r") as f:
    content = f.read()

# The original block that builds options from label_doc:
OLD = '''                options = [
                    {
                        "label": frappe.db.get_value(
                            label_doc if label_doc else doctype,
                            option,
                            label_field if label_field else group_by_field,
                        ),
                        "value": option,
                    }
                    for option in options
                    if option
                ]'''

NEW = '''                raw_options = []
                for option in options:
                    if not option:
                        continue
                    lbl = frappe.db.get_value(
                        label_doc if label_doc else doctype,
                        option,
                        label_field if label_field else group_by_field,
                    )
                    raw_options.append({"label": lbl or option, "value": option})

                # Hierarchy support: prefix sub-category labels with parent name
                if label_doc:
                    _meta = frappe.get_meta(label_doc)
                    if _meta.has_field("parent_category"):
                        for _opt in raw_options:
                            _pc = frappe.db.get_value(label_doc, _opt["value"], "parent_category")
                            if _pc:
                                _plbl = frappe.db.get_value(
                                    label_doc, _pc,
                                    label_field if label_field else "name",
                                )
                                if _plbl:
                                    _opt["label"] = _plbl + " > " + (_opt["label"] or "")

                options = raw_options'''

if "raw_options" in content:
    print("doc.py: Already patched (has raw_options)")
elif OLD in content:
    content = content.replace(OLD, NEW)
    with open(FILE, "w") as f:
        f.write(content)
    print("doc.py: Patched get_options for hierarchy labels")
else:
    print("doc.py: ERROR - Could not find OLD block to patch!")
    print("Searching for partial match...")
    if "label_doc if label_doc else doctype" in content:
        print("  Found label_doc reference — block format may differ")
    else:
        print("  No label_doc reference found at all")
