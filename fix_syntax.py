#!/usr/bin/env python3
"""Fix the duplicate { syntax error in KnowledgeBaseAgent.vue headerOptions."""

FILE = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue"

with open(FILE, "r") as f:
    content = f.read()

# Fix the duplicate { problem
# The bad pattern is: },\n  {\n  {\n    label: __("Sub-Category")
# Should be:          },\n  {\n    label: __("Sub-Category")
content = content.replace(
    """  },
  {
  {
    label: __("Sub-Category"),""",
    """  },
  {
    label: __("Sub-Category"),"""
)

with open(FILE, "w") as f:
    f.write(content)
print("Fixed duplicate brace syntax error")
