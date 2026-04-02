import os
from sqlalchemy import create_engine, event, TypeDecorator, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from app.config import get_settings


class UTCDateTime(TypeDecorator):
    """
    Cross-dialect DateTime column that handles timezone-aware datetimes.

    - PostgreSQL: native DateTime(timezone=True) — stored as TIMESTAMPTZ
    - SQLite: stored as VARCHAR ISO-8601 string; handles legacy 'Z'-suffix values
      that Python 3.10's fromisoformat() cannot parse via the C-extension.
    """
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(DateTime(timezone=True))
        # SQLite: store as plain string to bypass the C str_to_datetime extension
        return dialect.type_descriptor(String(50))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # Ensure timezone-aware before handing to psycopg2
            if isinstance(value, datetime) and value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value
        # SQLite: serialise to ISO string
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # PostgreSQL returns a real datetime object
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        # SQLite returns a string — fix legacy 'Z' suffix Python 3.10 can't parse
        if isinstance(value, str):
            value = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return value

settings = get_settings()

# Auto-detect database type
DATABASE_URL = os.getenv("DATABASE_URL") or settings.database_url

# Railway provides DATABASE_URL with postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine if using PostgreSQL or SQLite
is_postgres = DATABASE_URL.startswith("postgresql://")

# Create engine with appropriate settings
if is_postgres:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Disable SQL logging in production
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10
    )
else:
    # SQLite settings (development)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=True  # Log SQL queries for debugging
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    # Import all models to register them with Base
    from app.models import (
        User, CfgRegion, CfgCustomerType, CfgLeadSource, CfgContactRole,
        CfgTaskTemplate, CfgStage, CfgStageProbability, Account, Contact,
        ContactChannel, Opportunity, Task, Activity, Target, AuditLog, AppVersion
    )
    Base.metadata.create_all(bind=engine)
    
    # Log database type
    db_type = "PostgreSQL" if is_postgres else "SQLite"
    print(f"✅ Database initialized: {db_type}")
