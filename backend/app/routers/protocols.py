from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.protocol import Protocol, Criterion, CriterionType
from ..schemas import (
    ProtocolCreate, ProtocolUpdate, ProtocolResponse, ProtocolListItem,
    CriterionCreate, CriterionResponse,
)

router = APIRouter(prefix="/api/protocols", tags=["protocols"])


@router.get("", response_model=list[ProtocolListItem])
async def list_protocols(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Protocol).options(selectinload(Protocol.criteria)))
    protocols = result.scalars().all()
    return [
        ProtocolListItem(
            id=p.id,
            name=p.name,
            protocol_number=p.protocol_number,
            sponsor=p.sponsor,
            indication=p.indication,
            phase=p.phase,
            criteria_count=len(p.criteria),
        )
        for p in protocols
    ]


@router.post("", response_model=ProtocolResponse, status_code=201)
async def create_protocol(data: ProtocolCreate, db: AsyncSession = Depends(get_db)):
    protocol = Protocol(
        name=data.name,
        protocol_number=data.protocol_number,
        sponsor=data.sponsor,
        indication=data.indication,
        phase=data.phase,
        description=data.description,
    )
    db.add(protocol)
    await db.flush()

    for c in data.criteria:
        criterion = Criterion(
            protocol_id=protocol.id,
            criterion_type=CriterionType(c.criterion_type),
            number=c.number,
            description=c.description,
            keywords=c.keywords,
            category=c.category,
        )
        db.add(criterion)

    await db.commit()
    await db.refresh(protocol)

    result = await db.execute(
        select(Protocol).where(Protocol.id == protocol.id).options(selectinload(Protocol.criteria))
    )
    return result.scalar_one()


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(protocol_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Protocol).where(Protocol.id == protocol_id).options(selectinload(Protocol.criteria))
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.put("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(protocol_id: int, data: ProtocolUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Protocol).where(Protocol.id == protocol_id).options(selectinload(Protocol.criteria))
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(protocol, field, value)

    await db.commit()
    await db.refresh(protocol)
    return protocol


@router.delete("/{protocol_id}", status_code=204)
async def delete_protocol(protocol_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    await db.delete(protocol)
    await db.commit()


# --- Criteria sub-routes ---

@router.post("/{protocol_id}/criteria", response_model=CriterionResponse, status_code=201)
async def add_criterion(protocol_id: int, data: CriterionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Protocol not found")

    criterion = Criterion(
        protocol_id=protocol_id,
        criterion_type=CriterionType(data.criterion_type),
        number=data.number,
        description=data.description,
        keywords=data.keywords,
        category=data.category,
    )
    db.add(criterion)
    await db.commit()
    await db.refresh(criterion)
    return criterion


@router.put("/{protocol_id}/criteria/{criterion_id}", response_model=CriterionResponse)
async def update_criterion(protocol_id: int, criterion_id: int, data: CriterionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Criterion).where(Criterion.id == criterion_id, Criterion.protocol_id == protocol_id)
    )
    criterion = result.scalar_one_or_none()
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")

    criterion.criterion_type = CriterionType(data.criterion_type)
    criterion.number = data.number
    criterion.description = data.description
    criterion.keywords = data.keywords
    criterion.category = data.category

    await db.commit()
    await db.refresh(criterion)
    return criterion


@router.delete("/{protocol_id}/criteria/{criterion_id}", status_code=204)
async def delete_criterion(protocol_id: int, criterion_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Criterion).where(Criterion.id == criterion_id, Criterion.protocol_id == protocol_id)
    )
    criterion = result.scalar_one_or_none()
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    await db.delete(criterion)
    await db.commit()
