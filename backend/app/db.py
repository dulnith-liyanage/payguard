"""Database engine and session utilities for PayGuard."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Anchor database to backend directory consistently
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "payguard.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
