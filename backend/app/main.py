"""FastAPI application entrypoint for PayGuard."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import payments
import os

app = FastAPI(title="PayGuard API", version="0.1.0")

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments.router, prefix="/api/payments", tags=["payments"])

@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint for local verification."""
    return {"status": "ok"}
