import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

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
