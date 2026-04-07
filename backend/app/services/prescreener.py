"""
Prescreening Engine — matches patient medical history against protocol criteria.

Uses keyword matching, clinical NLP pattern recognition, and scoring
to determine eligibility. Designed to run fast without external API calls.

Matching strategy:
1. Keyword match (fast, high recall) — checks if criterion keywords appear in text
2. Semantic phrase matching — expands clinical abbreviations and synonyms
3. Negation detection — handles "no history of", "denies", "negative for"
4. Scoring — each criterion gets a confidence score
"""

import re
from dataclasses import dataclass
from enum import Enum


class MatchStatus(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    UNCERTAIN = "uncertain"
    NOT_EVALUATED = "not_evaluated"


@dataclass
class CriterionResult:
    criterion_id: int
    criterion_type: str  # inclusion or exclusion
    criterion_number: int
    description: str
    status: MatchStatus
    confidence: float  # 0.0 to 1.0
    evidence: list[str]  # matching text snippets
    reasoning: str


@dataclass
class ScreeningOutput:
    overall_status: str  # eligible, not_eligible, needs_review
    results: list[CriterionResult]
    summary: str


# Common clinical negation patterns
_NEGATION_PATTERNS = [
    re.compile(r"\b(?:no|not|without|denies|denied|negative|neg|absent|never|none|rules?\s*out|r/o|free\s+of|lack\s+of|no\s+evidence\s+of|no\s+history\s+of|no\s+h/o)\b", re.IGNORECASE),
]

# Common clinical abbreviation expansions
CLINICAL_SYNONYMS: dict[str, list[str]] = {
    "hypertension": ["htn", "high blood pressure", "elevated bp", "elevated blood pressure"],
    "diabetes": ["dm", "dm2", "dm1", "diabetes mellitus", "type 2 diabetes", "type 1 diabetes", "t2dm", "t1dm", "diabetic"],
    "diabetes mellitus type 2": ["dm2", "t2dm", "type 2 diabetes", "type ii diabetes", "niddm"],
    "diabetes mellitus type 1": ["dm1", "t1dm", "type 1 diabetes", "type i diabetes", "iddm"],
    "coronary artery disease": ["cad", "coronary disease", "coronary heart disease", "chd", "ischemic heart disease"],
    "congestive heart failure": ["chf", "heart failure", "hf", "hfref", "hfpef", "systolic dysfunction"],
    "chronic kidney disease": ["ckd", "chronic renal disease", "renal insufficiency", "kidney disease"],
    "chronic obstructive pulmonary disease": ["copd", "chronic bronchitis", "emphysema"],
    "atrial fibrillation": ["afib", "a-fib", "af", "atrial fib"],
    "myocardial infarction": ["mi", "heart attack", "stemi", "nstemi"],
    "cerebrovascular accident": ["cva", "stroke", "cerebral infarction", "brain attack"],
    "transient ischemic attack": ["tia", "mini stroke", "mini-stroke"],
    "deep vein thrombosis": ["dvt", "deep venous thrombosis"],
    "pulmonary embolism": ["pe", "pulmonary embolus"],
    "body mass index": ["bmi"],
    "hemoglobin a1c": ["hba1c", "a1c", "glycated hemoglobin", "glycosylated hemoglobin"],
    "estimated glomerular filtration rate": ["egfr", "gfr"],
    "blood pressure": ["bp", "b/p"],
    "hepatitis b": ["hbv", "hep b"],
    "hepatitis c": ["hcv", "hep c"],
    "human immunodeficiency virus": ["hiv"],
    "cancer": ["malignancy", "neoplasm", "carcinoma", "tumor", "tumour", "oncologic"],
    "pregnancy": ["pregnant", "gravid", "gestating"],
    "liver disease": ["hepatic disease", "liver dysfunction", "hepatic impairment", "cirrhosis"],
    "renal impairment": ["kidney impairment", "renal dysfunction", "renal failure", "kidney failure"],
    "anemia": ["anaemia", "low hemoglobin", "low hgb"],
    "thrombocytopenia": ["low platelets", "low platelet count"],
    "neutropenia": ["low neutrophils", "low anc"],
    "hyperlipidemia": ["high cholesterol", "dyslipidemia", "hypercholesterolemia", "elevated lipids"],
    "depression": ["mdd", "major depressive disorder", "depressive disorder"],
    "anxiety": ["gad", "generalized anxiety", "anxiety disorder"],
    "asthma": ["reactive airway disease", "rad"],
    "rheumatoid arthritis": ["ra"],
    "systemic lupus erythematosus": ["sle", "lupus"],
    "inflammatory bowel disease": ["ibd", "crohn", "crohns", "crohn's", "ulcerative colitis", "uc"],
    "gastroesophageal reflux disease": ["gerd", "acid reflux", "reflux"],
    "benign prostatic hyperplasia": ["bph", "enlarged prostate"],
    "urinary tract infection": ["uti"],
    "sexually transmitted infection": ["sti", "std", "sexually transmitted disease"],
}


def _expand_keywords(keywords: list[str]) -> list[str]:
    """Expand a keyword list with known clinical synonyms."""
    expanded = set()
    for kw in keywords:
        kw_lower = kw.lower().strip()
        expanded.add(kw_lower)
        # Check if this keyword IS a synonym key
        if kw_lower in CLINICAL_SYNONYMS:
            expanded.update(CLINICAL_SYNONYMS[kw_lower])
        # Check if this keyword appears in any synonym list
        for canonical, synonyms in CLINICAL_SYNONYMS.items():
            if kw_lower in synonyms or kw_lower == canonical:
                expanded.add(canonical)
                expanded.update(synonyms)
    return list(expanded)


def _is_negated(text: str, match_start: int, window: int = 60) -> bool:
    """Check if a match is negated by looking at preceding context."""
    start = max(0, match_start - window)
    context = text[start:match_start].lower()
    for pattern in _NEGATION_PATTERNS:
        if pattern.search(context):
            return True
    return False


def _extract_evidence(text: str, match_start: int, match_end: int, context_chars: int = 80) -> str:
    """Extract a snippet of evidence text around a match."""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def _find_keyword_matches(text: str, keywords: list[str]) -> list[tuple[str, int, int, bool]]:
    """Find all keyword matches in text, returns (keyword, start, end, is_negated)."""
    text_lower = text.lower()
    matches = []
    for kw in keywords:
        pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
        for m in pattern.finditer(text_lower):
            negated = _is_negated(text_lower, m.start())
            matches.append((kw, m.start(), m.end(), negated))
    return matches


def _extract_numeric_value(text: str, keyword: str) -> float | None:
    """Try to extract a numeric value associated with a keyword (e.g., 'A1C 7.2')."""
    pattern = re.compile(
        r"\b" + re.escape(keyword) + r"[\s:=]*(\d+\.?\d*)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def prescreen_patient(
    medical_text: str,
    criteria: list[dict],
) -> ScreeningOutput:
    """
    Screen a patient's medical history against protocol criteria.

    Args:
        medical_text: The (preferably redacted) medical history text.
        criteria: List of criterion dicts with keys:
            id, criterion_type, number, description, keywords, category

    Returns:
        ScreeningOutput with per-criterion results and overall status.
    """
    text_lower = medical_text.lower()
    results: list[CriterionResult] = []

    for crit in criteria:
        crit_id = crit["id"]
        crit_type = crit["criterion_type"]
        crit_num = crit["number"]
        description = crit["description"]
        raw_keywords = [k.strip() for k in crit.get("keywords", "").split(",") if k.strip()]
        expanded_keywords = _expand_keywords(raw_keywords)

        if not expanded_keywords:
            results.append(CriterionResult(
                criterion_id=crit_id,
                criterion_type=crit_type,
                criterion_number=crit_num,
                description=description,
                status=MatchStatus.NOT_EVALUATED,
                confidence=0.0,
                evidence=[],
                reasoning="No keywords defined for this criterion — requires manual review.",
            ))
            continue

        # Find all keyword matches
        matches = _find_keyword_matches(medical_text, expanded_keywords)

        if not matches:
            # No keywords found at all
            status = MatchStatus.UNCERTAIN
            confidence = 0.3
            evidence_list = []
            reasoning = f"No mentions of [{', '.join(raw_keywords)}] found in medical history. Cannot confirm or deny."
        else:
            affirmed = [m for m in matches if not m[3]]
            negated = [m for m in matches if m[3]]

            evidence_list = []
            for kw, start, end, neg in matches:
                snippet = _extract_evidence(medical_text, start, end)
                prefix = "[NEGATED] " if neg else ""
                evidence_list.append(f"{prefix}{snippet}")

            if affirmed and not negated:
                status = MatchStatus.MET
                confidence = min(0.6 + 0.1 * len(affirmed), 0.95)
                reasoning = f"Found {len(affirmed)} affirmed mention(s) of related terms."
            elif negated and not affirmed:
                status = MatchStatus.NOT_MET
                confidence = min(0.6 + 0.1 * len(negated), 0.95)
                reasoning = f"Found {len(negated)} negated mention(s) — patient denies/does not have this condition."
            else:
                # Mixed — some affirmed, some negated
                status = MatchStatus.UNCERTAIN
                confidence = 0.4
                reasoning = f"Conflicting evidence: {len(affirmed)} affirmed and {len(negated)} negated mentions. Needs manual review."

        results.append(CriterionResult(
            criterion_id=crit_id,
            criterion_type=crit_type,
            criterion_number=crit_num,
            description=description,
            status=status,
            confidence=confidence,
            evidence=evidence_list[:5],  # cap evidence snippets
            reasoning=reasoning,
        ))

    # Determine overall status
    overall = _determine_overall_status(results)

    # Generate summary
    summary = _generate_summary(results, overall)

    return ScreeningOutput(
        overall_status=overall,
        results=results,
        summary=summary,
    )


def _determine_overall_status(results: list[CriterionResult]) -> str:
    """Determine overall eligibility based on individual criterion results."""
    inclusion_results = [r for r in results if r.criterion_type == "inclusion"]
    exclusion_results = [r for r in results if r.criterion_type == "exclusion"]

    # Check exclusion criteria — any MET exclusion = screen fail
    for r in exclusion_results:
        if r.status == MatchStatus.MET:
            return "not_eligible"

    # Check inclusion criteria — all must be MET
    inclusion_met = all(r.status == MatchStatus.MET for r in inclusion_results) if inclusion_results else True
    has_uncertain = any(r.status == MatchStatus.UNCERTAIN or r.status == MatchStatus.NOT_EVALUATED for r in results)

    # Any inclusion NOT_MET = screen fail
    for r in inclusion_results:
        if r.status == MatchStatus.NOT_MET:
            return "not_eligible"

    if inclusion_met and not has_uncertain:
        return "eligible"

    return "needs_review"


def _generate_summary(results: list[CriterionResult], overall: str) -> str:
    """Generate a human-readable summary."""
    met = sum(1 for r in results if r.status == MatchStatus.MET)
    not_met = sum(1 for r in results if r.status == MatchStatus.NOT_MET)
    uncertain = sum(1 for r in results if r.status in (MatchStatus.UNCERTAIN, MatchStatus.NOT_EVALUATED))
    total = len(results)

    status_label = {
        "eligible": "POTENTIALLY ELIGIBLE",
        "not_eligible": "SCREEN FAIL",
        "needs_review": "NEEDS REVIEW",
    }[overall]

    lines = [
        f"Overall: {status_label}",
        f"Criteria evaluated: {total} | Met: {met} | Not Met: {not_met} | Uncertain: {uncertain}",
    ]

    # Call out specific screen fail reasons
    for r in results:
        if r.criterion_type == "exclusion" and r.status == MatchStatus.MET:
            lines.append(f"  ⚠ EXCLUSION #{r.criterion_number} MET: {r.description[:80]}")
        elif r.criterion_type == "inclusion" and r.status == MatchStatus.NOT_MET:
            lines.append(f"  ⚠ INCLUSION #{r.criterion_number} NOT MET: {r.description[:80]}")

    return "\n".join(lines)
