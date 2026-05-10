"""
RAG /ask endpoint: embed question → retrieve notes → Claude answers with citations.
"""

import anthropic

from .config import settings

_SYSTEM = """\
You are a personal knowledge assistant with access to the user's private knowledge base.
Answer the question using ONLY the notes provided below. Be specific and draw on the \
exact content — frameworks, examples, advice — from the notes. If the notes don't \
contain enough to answer well, say so briefly rather than speculating.

When you reference information, naturally attribute it (e.g. "According to the chapter \
on Managing Up…" or "The note on stakeholder communication suggests…"). Do not invent \
information not present in the notes.

Format your answer in clear markdown. Use bullet points or numbered lists where they \
help readability. Keep the answer focused and useful — aim for depth over breadth.\
"""

_CONTEXT_TEMPLATE = """\
<note index="{i}" title="{title}" path="{path}">
{body}
</note>"""

_MAX_BODY_CHARS = 3_000  # per note — keeps total context well within Claude's window


def build_context(raw_results: list[dict]) -> str:
    parts = []
    for i, r in enumerate(raw_results, 1):
        body = r["snippet"][:_MAX_BODY_CHARS]  # "snippet" is now the full cleaned body
        parts.append(
            _CONTEXT_TEMPLATE.format(
                i=i,
                title=r["metadata"].get("title", ""),
                path=r["metadata"].get("path", ""),
                body=body,
            )
        )
    return "\n\n".join(parts)


def answer(question: str, raw_results: list[dict]) -> str:
    """Call Claude with retrieved context and return the answer."""
    context = build_context(raw_results)

    user_message = f"""\
Here are the relevant notes from my knowledge base:

{context}

---

Question: {question}"""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )

    return msg.content[0].text
