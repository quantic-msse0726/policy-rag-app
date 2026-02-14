"""
Prompt construction for RAG chat.
"""


SYSTEM_MESSAGE = """Answer ONLY from the provided excerpts.
- Use 2–4 bullet points max.
- Each bullet must end with a citation like [1] or [2].
- DO NOT include any verbatim quotes in your answer text; the system will append a verbatim quote automatically.
- NEVER start a line with "Quote:".
- If refusing, do not cite anything.
- Keep under 140 words."""


def build_messages(question: str, contexts: list[dict]) -> list[dict]:
    """
    Build system and user messages for OpenAI Chat Completions.
    contexts: list of dicts with doc_id, title, section, text
    """
    blocks = []
    for i, ctx in enumerate(contexts, start=1):
        doc_id = ctx.get("doc_id", "")
        title = ctx.get("title", "")
        section = ctx.get("section") or ""
        text = ctx.get("text", "")
        header = f"[{i}] {doc_id} | {title} | {section}".strip()
        blocks.append(f"{header}\n{text}")

    context_str = "\n\n".join(blocks)
    user_content = f"""Question: {question}

Context:
{context_str}

Answer using only the context above."""

    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_content},
    ]
