from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.core.config import settings
import os

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure directory exists for sqlite file
    if db_url != "sqlite:///:memory:":
        db_path = db_url.replace("sqlite:///", "")
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=settings.SQL_DEBUG,
        poolclass=StaticPool if db_url == "sqlite:///:memory:" else None
    )
else:
    engine = create_engine(
        db_url,
        echo=settings.SQL_DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that provides a clean SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
