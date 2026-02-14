import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from rag.prompts import build_messages
from rag.retriever import retrieve, should_refuse

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


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    snippets: list[str]
    latency_ms: int


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
    contexts = retrieve(req.question, k=5)

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

    # Build citations and snippets from contexts
    citations = [
        Citation(
            doc_id=c["doc_id"],
            title=c["title"],
            section=c["section"] if c.get("section") else None,
            snippet=c["snippet"],
        )
        for c in contexts
    ]
    snippets = [c["snippet"] for c in contexts]

    latency_ms = int((time.perf_counter() - start) * 1000)

    return ChatResponse(
        answer=answer,
        citations=citations,
        snippets=snippets,
        latency_ms=latency_ms,
    )
