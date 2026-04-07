"""Seed the database with a sample diabetes protocol for demo/testing."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, async_session
from app.models.protocol import Protocol, Criterion, CriterionType


SAMPLE_PROTOCOL = {
    "name": "Semaglutide vs Placebo in T2DM",
    "protocol_number": "DEMO-T2DM-001",
    "sponsor": "Demo Pharma",
    "indication": "Type 2 Diabetes Mellitus",
    "phase": "Phase 3",
    "description": "A randomized, double-blind, placebo-controlled trial evaluating semaglutide in adults with T2DM.",
}

SAMPLE_CRITERIA = [
    # Inclusion
    {"criterion_type": "inclusion", "number": 1, "category": "demographics",
     "description": "Male or female, age 18-75 years at time of screening",
     "keywords": "age, years old, year old, y/o"},
    {"criterion_type": "inclusion", "number": 2, "category": "diagnosis",
     "description": "Documented diagnosis of Type 2 Diabetes Mellitus for at least 6 months",
     "keywords": "diabetes, dm2, type 2 diabetes, t2dm, diabetes mellitus"},
    {"criterion_type": "inclusion", "number": 3, "category": "labs",
     "description": "HbA1c between 7.0% and 10.5% at screening",
     "keywords": "hba1c, a1c, hemoglobin a1c, glycated hemoglobin"},
    {"criterion_type": "inclusion", "number": 4, "category": "medications",
     "description": "On stable dose of metformin (>=1500 mg/day) for at least 3 months",
     "keywords": "metformin, glucophage"},
    {"criterion_type": "inclusion", "number": 5, "category": "labs",
     "description": "eGFR >= 30 mL/min/1.73m2",
     "keywords": "egfr, gfr, glomerular filtration rate, renal function"},

    # Exclusion
    {"criterion_type": "exclusion", "number": 1, "category": "diagnosis",
     "description": "Type 1 Diabetes Mellitus or history of diabetic ketoacidosis",
     "keywords": "type 1 diabetes, dm1, t1dm, dka, diabetic ketoacidosis, iddm"},
    {"criterion_type": "exclusion", "number": 2, "category": "history",
     "description": "History of pancreatitis",
     "keywords": "pancreatitis, pancreatic inflammation"},
    {"criterion_type": "exclusion", "number": 3, "category": "history",
     "description": "History of medullary thyroid carcinoma or MEN2 syndrome",
     "keywords": "medullary thyroid, mtc, men2, men 2, multiple endocrine neoplasia"},
    {"criterion_type": "exclusion", "number": 4, "category": "diagnosis",
     "description": "NYHA Class III-IV heart failure",
     "keywords": "heart failure, chf, nyha, class iii, class iv, systolic dysfunction"},
    {"criterion_type": "exclusion", "number": 5, "category": "diagnosis",
     "description": "Active or history of malignancy within past 5 years (except basal cell carcinoma)",
     "keywords": "cancer, malignancy, carcinoma, tumor, neoplasm, oncology"},
    {"criterion_type": "exclusion", "number": 6, "category": "diagnosis",
     "description": "Uncontrolled hypertension (SBP > 180 mmHg or DBP > 110 mmHg)",
     "keywords": "hypertension, htn, high blood pressure, uncontrolled bp"},
    {"criterion_type": "exclusion", "number": 7, "category": "other",
     "description": "Pregnant, nursing, or planning to become pregnant during the study",
     "keywords": "pregnant, pregnancy, nursing, breastfeeding, lactating"},
]


async def seed():
    await init_db()
    async with async_session() as session:
        protocol = Protocol(**SAMPLE_PROTOCOL)
        session.add(protocol)
        await session.flush()

        for c in SAMPLE_CRITERIA:
            session.add(Criterion(protocol_id=protocol.id, **c))

        await session.commit()
        print(f"Seeded protocol '{SAMPLE_PROTOCOL['protocol_number']}' with {len(SAMPLE_CRITERIA)} criteria.")


if __name__ == "__main__":
    asyncio.run(seed())
