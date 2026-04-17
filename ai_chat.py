"""
AI Knowledge Base Assistant — Frappe API for Helpdesk.
Uses Google Gemini to answer questions based on HD Article content (RAG).
"""

import json
import re

import frappe
from frappe import _

# ── Constants ─────────────────────────────────────────────────

DEFAULT_AI_MODEL = "gemini-2.5-flash"

RAG_SYSTEM_PROMPT = """You are a helpful knowledge base assistant for a helpdesk system.

Answer questions using the provided knowledge base articles. Follow these rules:

1. Always try your BEST to give a helpful answer based on the articles provided.
2. For broad or general questions (e.g. "what is helpdesk", "understand about X"),
   summarize the relevant information from the available articles.
3. Cite the article you draw information from using [Article: "Title"] notation.
4. If the answer spans multiple articles, cite each relevant one.
5. ONLY say "This information is not available in the knowledge base" if the provided
   articles contain absolutely NO relevant information to the question.
6. If articles are provided, there is almost always something useful to say about them.
7. Do NOT hallucinate or add information beyond the provided articles.
8. Be concise but complete. Use markdown formatting.
9. Prefer answering over asking for clarification.
10. If the information is not available, end your response with exactly:
    Can't find what you're looking for? [Create a ticket →]({ticket_url})"""

RAG_USER_TEMPLATE = """Question: {question}

{conversation_history}Knowledge Base Articles:
{context}

Answer the question using the above articles. If the question is broad or general,
summarize the key information from the articles. Always try to provide a helpful response."""

FOLLOWUP_PROMPT = """Given a Q&A exchange, generate exactly 3 short follow-up questions.
Rules:
- Each must be a complete sentence ending with ?
- Keep each under 12 words
- Must be relevant to the answer
- Do NOT repeat the original question
- Output exactly 3 lines, one question per line, no numbering or bullets"""


def _get_gemini_client():
    """Lazy-load the Gemini client, reading the API key from HD Settings."""
    try:
        from google import genai
    except ImportError:
        frappe.throw(
            _("google-genai package is not installed. Run: pip install google-genai")
        )

    from frappe.utils.password import get_decrypted_password

    api_key = get_decrypted_password(
        "HD Settings", "HD Settings", "ai_assistant_api_key"
    )
    if not api_key:
        frappe.throw(
            _("AI Assistant API key is not configured. Go to Settings > General to add it.")
        )

    return genai.Client(api_key=api_key)


def _is_portal_user() -> bool:
    """Check if the current user is a customer portal user (not an agent)."""
    user_roles = frappe.get_roles(frappe.session.user)
    return "Agent" not in user_roles and "System Manager" not in user_roles


def _get_ticket_url() -> str:
    """Return the correct ticket creation URL based on user role."""
    return "/helpdesk/my-tickets/new" if _is_portal_user() else "/helpdesk/tickets/new"


def _get_kb_prefix() -> str:
    """Return 'kb-public' for portal users, 'kb' for agents."""
    return "kb-public" if _is_portal_user() else "kb"


def _get_ai_model() -> str:
    """Read AI model name from HD Settings, falling back to default."""
    try:
        model = frappe.db.get_single_value("HD Settings", "ai_assistant_model")
        if model and model.strip():
            return model.strip()
    except Exception:
        pass
    return DEFAULT_AI_MODEL


def _strip_html(html: str) -> str:
    """Remove HTML tags, inline styles, and decode entities for plain-text context."""
    if not html:
        return ""
    from html import unescape

    # Remove style attributes entirely
    text = re.sub(r'\s*style="[^"]*"', "", html)
    # Remove class attributes
    text = re.sub(r'\s*class="[^"]*"', "", html)
    # Convert <br>, <p>, <li> to newlines for readability
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"<li[^>]*>", "- ", text)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    # Collapse multiple spaces but preserve newlines
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _get_accessible_categories() -> list[str] | None:
    """Return list of category IDs the current user may access, or None if no
    filtering is needed (agents / Administrator see everything).

    Access rules (matches _filter_categories_by_access in kb_custom.py):
      - Categories with NO HD Category Access entries are public.
      - Categories WITH entries are restricted to the listed users.
      - Agents and Administrator bypass all restrictions.
    """
    from helpdesk.utils import is_agent

    user = frappe.session.user
    if user == "Administrator" or is_agent():
        return None  # no filtering — full access

    # All categories
    all_cats = frappe.get_all("HD Article Category", pluck="name")
    if not all_cats:
        return []

    # Restricted entries
    restricted = frappe.get_all(
        "HD Category Access", fields=["category", "user"]
    )
    if not restricted:
        return None  # nothing restricted anywhere

    access_map: dict[str, set[str]] = {}
    for r in restricted:
        access_map.setdefault(r["category"], set()).add(r["user"])

    accessible = []
    for cat in all_cats:
        allowed = access_map.get(cat)
        if allowed is None:
            accessible.append(cat)        # public category
        elif user in allowed:
            accessible.append(cat)        # user explicitly listed

    return accessible


def _search_articles(query: str, limit: int = 8) -> list[dict]:
    """
    Search published HD Articles by keyword matching on title and content.
    Returns list of dicts with name, title, category_name, content.

    Respects HD Category Access permissions — customers only see articles in
    categories they are allowed to access.

    Strategy:
      1. Try matching ALL query words (narrow, most relevant)
      2. Try matching ANY query word (broader)
      3. Fall back to returning all published articles (ensures AI always has context)

    Results are scored so that title matches rank higher than content-only matches.
    """
    QBArticle = frappe.qb.DocType("HD Article")
    QBCategory = frappe.qb.DocType("HD Article Category")

    base_query = (
        frappe.qb.from_(QBArticle)
        .left_join(QBCategory)
        .on(QBArticle.category == QBCategory.name)
        .select(
            QBArticle.name,
            QBArticle.title,
            QBArticle.content,
            QBCategory.category_name,
        )
        .where(QBArticle.status == "Published")
    )

    # ── Apply category-level access control ───────────────────
    accessible_cats = _get_accessible_categories()
    if accessible_cats is not None:
        if not accessible_cats:
            return []  # user has access to zero categories
        base_query = base_query.where(QBArticle.category.isin(accessible_cats))

    words = [w.strip().lower() for w in query.split() if len(w.strip()) > 2]

    articles = []

    # Step 1: Try ALL words match (most relevant)
    if words:
        from pypika import Criterion

        all_conditions = []
        for word in words[:10]:
            like_pattern = f"%{word}%"
            all_conditions.append(
                Criterion.any([
                    QBArticle.title.like(like_pattern),
                    QBArticle.content.like(like_pattern),
                ])
            )
        q = base_query.where(Criterion.all(all_conditions)).limit(limit)
        articles = q.run(as_dict=True)

    # Step 2: If too few results, try ANY word match
    if len(articles) < 3 and words:
        from pypika import Criterion

        any_conditions = []
        for word in words[:10]:
            like_pattern = f"%{word}%"
            any_conditions.append(QBArticle.title.like(like_pattern))
            any_conditions.append(QBArticle.content.like(like_pattern))
        q = base_query.where(Criterion.any(any_conditions)).limit(limit)
        any_articles = q.run(as_dict=True)

        # Merge without duplicates, keeping order
        seen = {a.name for a in articles}
        for a in any_articles:
            if a.name not in seen:
                articles.append(a)
                seen.add(a.name)

    # Step 3: If still too few, pad with all accessible published articles
    if len(articles) < 3:
        fallback_q = (
            frappe.qb.from_(QBArticle)
            .left_join(QBCategory)
            .on(QBArticle.category == QBCategory.name)
            .select(
                QBArticle.name,
                QBArticle.title,
                QBArticle.content,
                QBCategory.category_name,
            )
            .where(QBArticle.status == "Published")
        )
        if accessible_cats is not None:
            fallback_q = fallback_q.where(QBArticle.category.isin(accessible_cats))
        all_articles = fallback_q.limit(limit).run(as_dict=True)
        seen = {a.name for a in articles}
        for a in all_articles:
            if a.name not in seen:
                articles.append(a)
                seen.add(a.name)

    # Score and sort: title matches rank higher than content-only matches
    if words:
        def _score(article):
            title_lower = (article.get("title") or "").lower()
            score = 0
            for w in words:
                if w in title_lower:
                    score += 10  # high weight for title match
            return score

        articles.sort(key=_score, reverse=True)

    return articles[:limit]


@frappe.whitelist(allow_guest=True)
def ask(question: str, conversation_history: str = "[]"):
    """
    RAG endpoint: find relevant KB articles, send to Gemini, return AI answer.

    Args:
        question: The user's question
        conversation_history: JSON string of previous messages
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    Returns:
        dict with answer, cited_articles, suggested_questions
    """
    if not question or not question.strip():
        frappe.throw(_("Question cannot be empty"))

    question = question.strip()[:500]  # Cap length

    # Parse conversation history
    try:
        history = json.loads(conversation_history) if conversation_history else []
    except (json.JSONDecodeError, TypeError):
        history = []

    # Find relevant articles
    articles = _search_articles(question)

    if not articles:
        return {
            "answer": "There are no articles in the knowledge base yet. Please add some articles first.",
            "cited_articles": [],
            "suggested_questions": [],
        }

    # Build context from articles
    context_parts = []
    article_map = {}
    total_chars = 0
    char_budget = 24000  # ~6000 tokens

    for art in articles:
        plain_content = _strip_html(art.get("content", ""))
        if not plain_content:
            continue

        section_text = (
            f'[Article: "{art.title}" — Category: "{art.category_name or "General"}"]\n'
            f"{plain_content}\n"
        )

        if total_chars + len(section_text) > char_budget:
            remaining = char_budget - total_chars
            if remaining > 200:
                context_parts.append(section_text[:remaining] + "...[truncated]")
            break

        context_parts.append(section_text)
        total_chars += len(section_text)
        article_map[art.title] = {
            "name": art.name,
            "title": art.title,
            "category": art.category_name or "General",
        }

    context_str = "\n---\n".join(context_parts)

    # Add a preamble so the AI knows how many articles it has
    if context_parts:
        context_str = (
            f"[{len(context_parts)} article(s) found in the knowledge base]\n\n"
            + context_str
        )
    else:
        # Articles were found but all had empty content
        titles = [a.get("title", "Untitled") for a in articles]
        context_str = (
            f"The following articles exist but have minimal content:\n"
            + "\n".join(f'- "{t}"' for t in titles)
        )

    # Build conversation history string
    history_str = ""
    if history:
        history_lines = []
        for msg in history[-6:]:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = str(msg.get("content", ""))[:300]
            history_lines.append(f"{role}: {content}")
        if history_lines:
            history_str = (
                "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"
            )

    user_message = RAG_USER_TEMPLATE.format(
        question=question,
        context=context_str,
        conversation_history=history_str,
    )

    # Call Gemini
    client = _get_gemini_client()
    ai_model = _get_ai_model()
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=ai_model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=RAG_SYSTEM_PROMPT.format(ticket_url=_get_ticket_url()),
                max_output_tokens=8192,
            ),
        )
        answer_text = response.text.strip()
    except Exception as e:
        frappe.log_error(f"Gemini API error: {e}", "AI KB Assistant")
        return {
            "answer": "AI is temporarily unavailable. Please try again later.",
            "cited_articles": [],
            "suggested_questions": [],
        }

    # Append ticket link if the AI says information is not available
    _not_available_phrases = [
        "not available in the knowledge base",
        "no relevant information",
        "not covered in the knowledge base",
        "couldn't find",
        "could not find",
    ]
    answer_lower_check = answer_text.lower()
    if any(phrase in answer_lower_check for phrase in _not_available_phrases):
        if "create a ticket" not in answer_lower_check:
            answer_text += (
                "\n\nCan't find what you're looking for? "
                f"[Create a ticket \u2192]({_get_ticket_url()})"
            )

    # Extract cited articles — case-insensitive matching and partial title matching
    cited = []
    site_url = (frappe.utils.get_url() or "").rstrip("/")
    answer_lower = answer_text.lower()
    kb_prefix = _get_kb_prefix()
    for title, info in article_map.items():
        if title.lower() in answer_lower:
            info["url"] = f"{site_url}/helpdesk/{kb_prefix}/articles/{info['name']}"
            cited.append(info)

    # If no explicit citations found, include all articles that were sent as context
    if not cited:
        for info in list(article_map.values()):
            info["url"] = f"{site_url}/helpdesk/{kb_prefix}/articles/{info['name']}"
            cited.append(info)

    # Generate follow-up questions
    suggested_questions = []
    try:
        followup_prompt = (
            f"Original question: {question}\n\n"
            f"Answer: {answer_text[:600]}\n\n"
            f"Generate 3 follow-up questions."
        )
        followup_response = client.models.generate_content(
            model=ai_model,
            contents=followup_prompt,
            config=types.GenerateContentConfig(
                system_instruction=FOLLOWUP_PROMPT,
                max_output_tokens=300,
            ),
        )
        raw = followup_response.text.strip()
        lines = [
            ln.strip().lstrip("-•*0123456789.) ").strip("\"'")
            for ln in raw.splitlines()
            if ln.strip()
        ]
        suggested_questions = [q for q in lines if len(q) > 5 and q.endswith("?")][:3]
    except Exception:
        pass

    return {
        "answer": answer_text,
        "cited_articles": cited,
        "suggested_questions": suggested_questions,
    }
