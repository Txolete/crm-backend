from sqlalchemy import Column, String, Integer, ForeignKey
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class TwoFactorCode(Base):
    """
    Tabla: two_factor_codes
    Codigos de un solo uso (OTP) enviados por email para el segundo factor de login.
    El codigo se guarda hasheado (nunca en claro) — igual que una contraseña.
    """
    __tablename__ = "two_factor_codes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(UTCDateTime(), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    used = Column(Integer, nullable=False, default=0)  # 0/1
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
