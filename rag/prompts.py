"""
Prompt construction for RAG chat.
"""


SYSTEM_MESSAGE = """You answer questions using ONLY the provided policy excerpts.
- If the answer is not supported by the documents, say you cannot find it in the policy documents.
- Always include citations in your answer using the format [1], [2], etc. to reference the numbered context blocks.
- Keep your answer under 180 words."""


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

Answer the question using only the context above. Cite sources as [1], [2], etc."""

    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_content},
    ]
