from pydantic import BaseModel
from datetime import datetime


# --- Protocol Schemas ---

class CriterionCreate(BaseModel):
    criterion_type: str  # "inclusion" or "exclusion"
    number: int
    description: str
    keywords: str = ""  # comma-separated
    category: str = ""


class CriterionResponse(CriterionCreate):
    id: int

    class Config:
        from_attributes = True


class ProtocolCreate(BaseModel):
    name: str
    protocol_number: str
    sponsor: str = ""
    indication: str = ""
    phase: str = ""
    description: str = ""
    criteria: list[CriterionCreate] = []


class ProtocolUpdate(BaseModel):
    name: str | None = None
    protocol_number: str | None = None
    sponsor: str | None = None
    indication: str | None = None
    phase: str | None = None
    description: str | None = None


class ProtocolResponse(BaseModel):
    id: int
    name: str
    protocol_number: str
    sponsor: str
    indication: str
    phase: str
    description: str
    created_at: datetime
    criteria: list[CriterionResponse] = []

    class Config:
        from_attributes = True


class ProtocolListItem(BaseModel):
    id: int
    name: str
    protocol_number: str
    sponsor: str
    indication: str
    phase: str
    criteria_count: int

    class Config:
        from_attributes = True


# --- Screening Schemas ---

class ScreenRequest(BaseModel):
    medical_text: str
    protocol_id: int
    use_enhanced_redaction: bool = False


class RedactRequest(BaseModel):
    text: str
    use_enhanced: bool = False


class RedactResponse(BaseModel):
    redacted_text: str
    entity_count: int
    entities_found: list[dict]


class CriterionMatchResult(BaseModel):
    criterion_id: int
    criterion_type: str
    criterion_number: int
    description: str
    status: str
    confidence: float
    evidence: list[str]
    reasoning: str


class ScreenResponse(BaseModel):
    id: int | None = None
    overall_status: str
    summary: str
    redacted_text: str
    results: list[CriterionMatchResult]
