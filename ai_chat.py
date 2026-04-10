"""
AI Knowledge Base Assistant — Frappe API for Helpdesk.
Uses Google Gemini to answer questions based on HD Article content (RAG).
"""

import json
import re

import frappe
from frappe import _

# ── Constants ─────────────────────────────────────────────────

GOOGLE_API_KEY = "AIzaSyCA9c-nV5i6oC-jGwJs8FEZZVzDPMqnwJQ"
AI_MODEL = "gemini-2.5-flash"

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
9. Prefer answering over asking for clarification."""

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
    """Lazy-load the Gemini client."""
    try:
        from google import genai

        return genai.Client(api_key=GOOGLE_API_KEY)
    except ImportError:
        frappe.throw(
            _("google-genai package is not installed. Run: pip install google-genai")
        )


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


def _search_articles(query: str, limit: int = 8) -> list[dict]:
    """
    Search published HD Articles by keyword matching on title and content.
    Returns list of dicts with name, title, category_name, content.
    """
    QBArticle = frappe.qb.DocType("HD Article")
    QBCategory = frappe.qb.DocType("HD Article Category")

    q = (
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

    # Simple keyword search: match any word in title or content
    words = [w.strip() for w in query.split() if len(w.strip()) > 2]
    if words:
        from pypika import Criterion

        conditions = []
        for word in words[:10]:  # Cap to prevent abuse
            like_pattern = f"%{word}%"
            conditions.append(QBArticle.title.like(like_pattern))
            conditions.append(QBArticle.content.like(like_pattern))
        q = q.where(Criterion.any(conditions))

    articles = q.limit(limit).run(as_dict=True)

    # If keyword search returns nothing, fall back to returning all published articles
    if not articles:
        articles = (
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
            .limit(limit)
            .run(as_dict=True)
        )

    return articles


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
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=AI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=RAG_SYSTEM_PROMPT,
                max_output_tokens=1500,
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

    # Extract cited articles (those whose title appears in the answer)
    cited = []
    for title, info in article_map.items():
        if title in answer_text:
            cited.append(info)

    # If no explicit citations found, include top articles as context
    if not cited:
        cited = list(article_map.values())[:3]

    # Generate follow-up questions
    suggested_questions = []
    try:
        followup_prompt = (
            f"Original question: {question}\n\n"
            f"Answer: {answer_text[:600]}\n\n"
            f"Generate 3 follow-up questions."
        )
        followup_response = client.models.generate_content(
            model=AI_MODEL,
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
