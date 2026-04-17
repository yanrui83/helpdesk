import frappe, os, re
os.chdir("/home/frappe/frappe-bench/sites")
frappe.init(site="helpdesk.localhost")
frappe.connect()

# Read the file
filepath = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/ai_chat.py"
with open(filepath, "r") as f:
    content = f.read()

# 1. Fix the system prompt: use a placeholder that gets replaced at runtime
old_prompt_line = '    Can\'t find what you\'re looking for? [Create a ticket \u2192](/helpdesk/tickets/new)"""'
new_prompt_line = '    Can\'t find what you\'re looking for? [Create a ticket \u2192]({ticket_url})"""'
content = content.replace(old_prompt_line, new_prompt_line)

# 2. Find where RAG_SYSTEM_PROMPT is used and add .format(ticket_url=...)
# Look for the system_instruction=RAG_SYSTEM_PROMPT usage
old_system = 'system_instruction=RAG_SYSTEM_PROMPT,'
new_system = 'system_instruction=RAG_SYSTEM_PROMPT.format(ticket_url=_get_ticket_url()),'
content = content.replace(old_system, new_system)

# 3. Fix the post-processing hardcoded URL
old_post = '"[Create a ticket \\u2192](/helpdesk/tickets/new)"'
new_post = 'f"[Create a ticket \\u2192]({_get_ticket_url()})"'
content = content.replace(old_post, new_post)

# 4. Add _get_ticket_url helper after the existing helper functions
# Find a good place - after _get_ai_model function
old_helper = '\ndef _get_ai_model():'
new_helper = '''
def _get_ticket_url():
    """Return the correct ticket creation URL based on user role."""
    user_roles = frappe.get_roles(frappe.session.user)
    if "Agent" in user_roles or "System Manager" in user_roles:
        return "/helpdesk/tickets/new"
    return "/helpdesk/my-tickets/new"


def _get_ai_model():'''
content = content.replace(old_helper, new_helper)

# 5. Also fix the article URLs in cited_articles
old_cite = 'info["url"] = f"{site_url}/helpdesk/kb/articles/{info[\'name\']}"'
new_cite = '''kb_prefix = "kb" if "Agent" in frappe.get_roles(frappe.session.user) else "kb-public"
            info["url"] = f"{site_url}/helpdesk/{kb_prefix}/articles/{info['name']}"'''
content = content.replace(old_cite, new_cite, 1)

# The second occurrence (fallback)
old_cite2 = '            info["url"] = f"{site_url}/helpdesk/kb/articles/{info[\'name\']}"'
new_cite2 = '''            kb_prefix = "kb" if "Agent" in frappe.get_roles(frappe.session.user) else "kb-public"
            info["url"] = f"{site_url}/helpdesk/{kb_prefix}/articles/{info[\'name\']}"'''
# Count occurrences
count = content.count(old_cite2)
print(f"Found {count} remaining occurrences of old cite pattern")

if count > 0:
    content = content.replace(old_cite2, new_cite2, 1)

with open(filepath, "w") as f:
    f.write(content)

print("ai_chat.py updated successfully")
frappe.destroy()
