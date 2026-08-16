"""FastAPI application entrypoint for PayGuard."""

from fastapi import FastAPI

app = FastAPI(title="PayGuard API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint for local verification."""
    return {"status": "ok"}
