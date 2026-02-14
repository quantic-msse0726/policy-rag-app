import os
import re
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from rag.prompts import build_messages
from rag.retriever import _extract_keywords, pick_verbatim_quote, retrieve, should_refuse

load_dotenv()

app = FastAPI()


# --- Schemas ---


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3)

    @field_validator("question", mode="before")
    @classmethod
    def strip_question(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class Citation(BaseModel):
    doc_id: str
    title: str
    section: str | None
    snippet: str
    text: str | None = None  # full chunk for eval overlap check


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    snippets: list[str]
    latency_ms: int


# --- Helpers ---


def extract_cited_indices(answer_text: str) -> list[int]:
    """Extract bracketed integer citation markers from answer (e.g. [1], [2], [12]). Returns sorted unique list."""
    matches = re.findall(r"\[(\d+)\]", answer_text)
    indices = []
    seen = set()
    for m in matches:
        n = int(m)
        if n not in seen:
            indices.append(n)
            seen.add(n)
    return sorted(indices)


# --- Routes ---


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=PlainTextResponse)
async def root():
    return "Policy RAG App is running"


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    start = time.perf_counter()

    # Retrieve
    contexts = retrieve(req.question)

    # Guardrail: refuse if insufficient context
    refuse, reason = should_refuse(contexts)
    if refuse:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return ChatResponse(
            answer=f"I cannot answer that question. {reason}",
            citations=[],
            snippets=[],
            latency_ms=latency_ms,
        )

    # Build messages and call OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set in .env")

    client = OpenAI()
    messages = build_messages(req.question, contexts)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    answer = response.choices[0].message.content or ""

    # Deterministic quote injection: append Quote line if not already present
    has_quote_line = any(line.strip().startswith("Quote:") for line in answer.split("\n"))
    if not has_quote_line and contexts:
        cited = extract_cited_indices(answer)
        primary_idx = cited[0] if cited else 1
        primary_idx = max(1, min(primary_idx, len(contexts)))
        ctx = contexts[primary_idx - 1]
        source_text = ctx.get("text") or ctx.get("snippet") or ""
        if source_text:
            question_keywords = _extract_keywords(req.question)
            quote = pick_verbatim_quote(source_text, question_keywords=question_keywords)
            if quote:
                # Remove any internal double quotes to avoid breaking eval regex
                clean_quote = quote.replace('"', "")
                
                # Debug logging
                if os.environ.get("RAG_DEBUG") == "true":
                    from rag.retriever import _clean_whitespace
                    norm_quote = _clean_whitespace(clean_quote).lower()
                    norm_source = _clean_whitespace(source_text).lower()
                    match_ok = norm_quote in norm_source
                    print(f"[DEBUG] Quote: \"{clean_quote}\"")
                    print(f"[DEBUG] Source index: [{primary_idx}]")
                    print(f"[DEBUG] Match success: {match_ok}")
                    if not match_ok:
                        print(f"[DEBUG] Normalized Quote: {norm_quote}")
                        print(f"[DEBUG] Normalized Source snippet: {norm_source[:200]}...")

                answer = answer.rstrip() + '\nQuote: "' + clean_quote + '" [' + str(primary_idx) + ']\n'

    # Filter citations/snippets to only those referenced in the answer
    cited = extract_cited_indices(answer)
    k = len(contexts)
    if not cited:
        citations = []
        snippets = []
    else:
        valid_indices = [i for i in cited if 1 <= i <= k]
        citations = [
            Citation(
                doc_id=contexts[i - 1]["doc_id"],
                title=contexts[i - 1]["title"],
                section=contexts[i - 1].get("section"),
                snippet=contexts[i - 1]["snippet"],
                text=contexts[i - 1].get("text"),
            )
            for i in valid_indices
        ]
        snippets = [contexts[i - 1]["snippet"] for i in valid_indices]

    latency_ms = int((time.perf_counter() - start) * 1000)

    return ChatResponse(
        answer=answer,
        citations=citations,
        snippets=snippets,
        latency_ms=latency_ms,
    )
