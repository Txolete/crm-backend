"""
Shared pytest fixtures for the CRM test suite.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# Database fixtures — in-memory SQLite for fast, isolated tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine shared across the test session."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables once
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def db_session(engine):
    """Provide a transactional database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB session overridden to use the test DB."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
