"""
Target model - Annual sales targets
"""
from sqlalchemy import Column, String, Integer, Float, DateTime
from datetime import datetime, timezone
from app.database import Base


class Target(Base):
    """Annual sales targets"""
    __tablename__ = "targets"

    id = Column(String, primary_key=True)
    year = Column(Integer, nullable=False, unique=True, index=True)
    target_pipeline_total = Column(Float, nullable=False)
    target_pipeline_weighted = Column(Float, nullable=False)
    target_closed = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
