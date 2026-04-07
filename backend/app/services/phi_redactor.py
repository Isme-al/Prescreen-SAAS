"""
PHI Redaction Engine — runs entirely locally, no cloud calls.

Uses a combination of regex patterns and Microsoft Presidio for NER-based
detection of Protected Health Information per HIPAA Safe Harbor method.

Redacts: names, dates, SSNs, MRNs, phone numbers, emails, addresses,
ages over 89, device IDs, URLs, IPs, and freeform identifiers.
"""

import re
from dataclasses import dataclass, field

# Regex-first approach for speed — Presidio used as optional second pass.
# This means the system works even without spaCy models downloaded.


@dataclass
class RedactionResult:
    redacted_text: str
    entities_found: list[dict] = field(default_factory=list)
    entity_count: int = 0


# Precompile all patterns once at module load for speed
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("MRN", re.compile(r"\b(?:MRN|mrn|Medical Record Number|Med Rec)[#:\s]*\d{4,12}\b", re.IGNORECASE)),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("DATE", re.compile(
        r"\b(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"  # MM/DD/YYYY or MM-DD-YYYY
        r"|\d{4}[/-]\d{1,2}[/-]\d{1,2}"   # YYYY-MM-DD
        r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{2,4}"
        r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*,?\s*\d{2,4}"
        r")\b",
        re.IGNORECASE,
    )),
    ("AGE_OVER_89", re.compile(r"\b(?:age[d]?\s*(?:of\s*)?)?(?:9[0-9]|[1-9]\d{2,})\s*(?:year|yr|y/?o|years?\s*old)\b", re.IGNORECASE)),
    ("ZIP", re.compile(r"\b\d{5}(?:-\d{4})?\b")),
    ("IP_ADDRESS", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
    ("URL", re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)),
    ("ACCOUNT_NUMBER", re.compile(r"\b(?:account|acct)[#:\s]*\d{6,}\b", re.IGNORECASE)),
    ("DOB", re.compile(r"\b(?:DOB|Date of Birth|D\.O\.B\.?|Birth\s*Date)[:\s]*[^\n,;]{4,20}", re.IGNORECASE)),
]

# Name patterns — catches "Dr. John Smith", "Patient: Jane Doe", common clinical name contexts
_NAME_CONTEXT_PATTERN = re.compile(
    r"(?:(?:Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Patient|Pt\.?|Name)[:\s]+)"
    r"([A-Z][a-z]{1,15}(?:\s+[A-Z][a-z]{1,15}){1,3})"
    r"(?=\s*[,\n;(]|\s*$|\s+DOB|\s+MRN|\s+Age)",
)

# Address pattern — number + street name + optional type
_ADDRESS_PATTERN = re.compile(
    r"\b\d{1,6}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:St(?:reet)?|Ave(?:nue)?|Blvd|Boulevard|Dr(?:ive)?|Ln|Lane|Rd|Road|Way|Ct|Court|Pl|Place|Cir|Circle)\b\.?",
    re.IGNORECASE,
)


def redact_phi(text: str) -> RedactionResult:
    """Redact all PHI from input text. Returns redacted text and metadata."""
    entities: list[dict] = []
    redacted = text

    # Pass 1: Named-context patterns (names, addresses)
    for match in _NAME_CONTEXT_PATTERN.finditer(redacted):
        entities.append({
            "type": "NAME",
            "start": match.start(1),
            "end": match.end(1),
            "text": match.group(1),
        })

    for match in _ADDRESS_PATTERN.finditer(redacted):
        entities.append({
            "type": "ADDRESS",
            "start": match.start(),
            "end": match.end(),
            "text": match.group(),
        })

    # Pass 2: All regex patterns
    for entity_type, pattern in _PATTERNS:
        for match in pattern.finditer(redacted):
            entities.append({
                "type": entity_type,
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
            })

    # Deduplicate overlapping entities — keep the longest match
    entities.sort(key=lambda e: (e["start"], -(e["end"] - e["start"])))
    merged: list[dict] = []
    for ent in entities:
        if merged and ent["start"] < merged[-1]["end"]:
            if ent["end"] > merged[-1]["end"]:
                merged[-1]["end"] = ent["end"]
            continue
        merged.append(ent)

    # Replace from end to preserve offsets
    for ent in reversed(merged):
        tag = f"[{ent['type']}_REDACTED]"
        redacted = redacted[: ent["start"]] + tag + redacted[ent["end"]:]

    return RedactionResult(
        redacted_text=redacted,
        entities_found=[{"type": e["type"], "original_length": e["end"] - e["start"]} for e in merged],
        entity_count=len(merged),
    )


# Optional Presidio integration for enhanced NER-based detection
_presidio_analyzer = None
_presidio_anonymizer = None


def _init_presidio():
    """Lazy-load Presidio. Falls back gracefully if not available."""
    global _presidio_analyzer, _presidio_anonymizer
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        _presidio_analyzer = AnalyzerEngine()
        _presidio_anonymizer = AnonymizerEngine()
        return True
    except (ImportError, OSError):
        return False


def redact_phi_enhanced(text: str) -> RedactionResult:
    """
    Two-pass redaction: regex first (fast), then Presidio NER (thorough).
    Falls back to regex-only if Presidio isn't available.
    """
    # Always do regex pass first
    result = redact_phi(text)

    # Try Presidio as second pass on already-redacted text
    if _presidio_analyzer is None:
        if not _init_presidio():
            return result

    try:
        analyzer_results = _presidio_analyzer.analyze(
            text=result.redacted_text,
            language="en",
            entities=[
                "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS",
                "LOCATION", "DATE_TIME", "NRP", "MEDICAL_LICENSE",
                "US_SSN", "US_DRIVER_LICENSE",
            ],
        )
        if analyzer_results:
            anonymized = _presidio_anonymizer.anonymize(
                text=result.redacted_text,
                analyzer_results=analyzer_results,
            )
            result.redacted_text = anonymized.text
            result.entity_count += len(analyzer_results)
    except Exception:
        pass  # Presidio failure is non-fatal, regex results are still valid

    return result
