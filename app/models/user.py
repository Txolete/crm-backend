from sqlalchemy import Column, String, Integer, CheckConstraint
from app.database import Base
from datetime import datetime


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
    last_login_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'sales', 'viewer')", name='check_role'),
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
