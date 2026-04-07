from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    redacted_text = Column(Text, nullable=False)
    results = Column(JSON, nullable=False)  # list of criterion match results
    overall_status = Column(String(50), nullable=False)  # eligible, not_eligible, needs_review
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    protocol = relationship("Protocol")
