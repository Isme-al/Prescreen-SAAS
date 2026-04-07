from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from ..database import Base


class CriterionType(str, enum.Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class Protocol(Base):
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    protocol_number = Column(String(100), unique=True, nullable=False)
    sponsor = Column(String(255), default="")
    indication = Column(String(255), default="")
    phase = Column(String(50), default="")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    criteria = relationship("Criterion", back_populates="protocol", cascade="all, delete-orphan")


class Criterion(Base):
    __tablename__ = "criteria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    criterion_type = Column(SAEnum(CriterionType), nullable=False)
    number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    keywords = Column(Text, default="")  # comma-separated keywords for fast matching
    category = Column(String(100), default="")  # e.g. "demographics", "labs", "diagnosis", "medications"

    protocol = relationship("Protocol", back_populates="criteria")
