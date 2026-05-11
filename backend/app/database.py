from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# connect_args necessário apenas para SQLite (desativa o check de thread único)
connect_args = (
    {"check_same_thread": False, "timeout": 10}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_wal_mode(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA journal_mode=WAL")
        dbapi_connection.execute("PRAGMA busy_timeout=5000")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa compartilhada por todos os modelos
Base = declarative_base()


def get_db():
    """Generator para dependency injection do FastAPI. Garante fechamento da sessão."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
