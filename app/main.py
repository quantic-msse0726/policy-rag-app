import time

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator

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
    answer = f"Stub: RAG not enabled yet. Your question was: {req.question}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    return ChatResponse(
        answer=answer,
        citations=[],
        snippets=[],
        latency_ms=latency_ms,
    )
