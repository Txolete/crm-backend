from sqlalchemy import Column, String, Text, ForeignKey
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class UserFeedback(Base):
    """
    Tabla: user_feedback
    Feedback enviado por los usuarios desde el widget in-app.
    """
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    message = Column(Text, nullable=False)
    view = Column(String, nullable=True)
    url = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")  # open | reviewed | done | discarded
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(UTCDateTime(), nullable=True)
    reviewed_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    admin_note = Column(Text, nullable=True)
