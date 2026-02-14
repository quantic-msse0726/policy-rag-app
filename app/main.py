from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=PlainTextResponse)
async def root():
    return "Policy RAG App is running"
