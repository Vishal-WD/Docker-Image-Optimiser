import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    """Attempt connecting to PostgreSQL; fallback to SQLite for local tests if unreachable."""
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 3} if "postgresql" in settings.DATABASE_URL else {}
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info("Successfully connected to primary database (PostgreSQL).")
        return engine, "PostgreSQL"
    except Exception as exc:
        if settings.USE_SQLITE_FALLBACK:
            logger.warning(
                f"PostgreSQL connection failed ({exc}). Falling back to SQLite ({settings.SQLITE_URL}) for standalone/test execution."
            )
            fallback_engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine, "SQLite (Fallback)"
        raise exc


engine, active_db_type = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

