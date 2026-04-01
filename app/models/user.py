from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    """
    Tabla: users
    Usuarios del sistema con roles: admin, sales, viewer
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'sales', 'viewer')", name='check_role'),
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
