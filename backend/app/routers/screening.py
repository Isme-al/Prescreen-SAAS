from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.protocol import Protocol
from ..models.screening import ScreeningResult
from ..schemas import ScreenRequest, ScreenResponse, RedactRequest, RedactResponse, CriterionMatchResult
from ..services.phi_redactor import redact_phi, redact_phi_enhanced
from ..services.prescreener import prescreen_patient

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.post("/redact", response_model=RedactResponse)
async def redact_text(data: RedactRequest):
    """Redact PHI from text without screening."""
    if data.use_enhanced:
        result = redact_phi_enhanced(data.text)
    else:
        result = redact_phi(data.text)
    return RedactResponse(
        redacted_text=result.redacted_text,
        entity_count=result.entity_count,
        entities_found=result.entities_found,
    )


@router.post("/screen", response_model=ScreenResponse)
async def screen_patient(data: ScreenRequest, db: AsyncSession = Depends(get_db)):
    """Screen a patient's medical history against a protocol's criteria."""
    # Fetch protocol with criteria
    result = await db.execute(
        select(Protocol).where(Protocol.id == data.protocol_id).options(selectinload(Protocol.criteria))
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    if not protocol.criteria:
        raise HTTPException(status_code=400, detail="Protocol has no criteria defined")

    # Step 1: Redact PHI
    if data.use_enhanced_redaction:
        redaction = redact_phi_enhanced(data.medical_text)
    else:
        redaction = redact_phi(data.medical_text)

    # Step 2: Prescreen against criteria
    criteria_dicts = [
        {
            "id": c.id,
            "criterion_type": c.criterion_type.value,
            "number": c.number,
            "description": c.description,
            "keywords": c.keywords,
            "category": c.category,
        }
        for c in protocol.criteria
    ]

    screening = prescreen_patient(redaction.redacted_text, criteria_dicts)

    # Step 3: Save result
    screening_record = ScreeningResult(
        protocol_id=data.protocol_id,
        redacted_text=redaction.redacted_text,
        results=[
            {
                "criterion_id": r.criterion_id,
                "criterion_type": r.criterion_type,
                "criterion_number": r.criterion_number,
                "description": r.description,
                "status": r.status.value,
                "confidence": r.confidence,
                "evidence": r.evidence,
                "reasoning": r.reasoning,
            }
            for r in screening.results
        ],
        overall_status=screening.overall_status,
    )
    db.add(screening_record)
    await db.commit()
    await db.refresh(screening_record)

    return ScreenResponse(
        id=screening_record.id,
        overall_status=screening.overall_status,
        summary=screening.summary,
        redacted_text=redaction.redacted_text,
        results=[
            CriterionMatchResult(
                criterion_id=r.criterion_id,
                criterion_type=r.criterion_type,
                criterion_number=r.criterion_number,
                description=r.description,
                status=r.status.value,
                confidence=r.confidence,
                evidence=r.evidence,
                reasoning=r.reasoning,
            )
            for r in screening.results
        ],
    )


@router.get("/history", response_model=list[dict])
async def get_screening_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get recent screening results."""
    result = await db.execute(
        select(ScreeningResult)
        .order_by(ScreeningResult.created_at.desc())
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "protocol_id": r.protocol_id,
            "overall_status": r.overall_status,
            "created_at": r.created_at.isoformat(),
            "result_count": len(r.results) if r.results else 0,
        }
        for r in records
    ]
