"""Blocked image domain model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class BlockedImageDomain(Base):
    """Model for blocked image domains."""

    __tablename__ = "blocked_image_domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, nullable=False, index=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
