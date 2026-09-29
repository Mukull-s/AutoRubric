import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CriticConfig:
    low_similarity_threshold: float = 0.5
    high_confidence_threshold: float = 0.8

@dataclass
class RuleResult:
    flag: str
    is_hard: bool
    reason: str

INJECTION_PATTERNS = [
    {
        "id": "ignore_instructions",
        "regex": re.compile(r"(ignore|disregard|override)\s+(all\s+)?(previous\s+)?(instructions|rules|prompts)", re.IGNORECASE),
        "description": "Attempt to override instructions"
    },
    {
        "id": "address_grader",
        "regex": re.compile(r"(note|attention|dear)\s+(to\s+)?(the\s+)?(grader|examiner|evaluator|ai|assistant|system)", re.IGNORECASE),
        "description": "Addressing the grader/system directly"
    },
    {
        "id": "request_score",
        "regex": re.compile(r"(give|award|assign)\s+(me\s+)?(full\s+(marks|credit)|10/10|a\s+perfect\s+score)", re.IGNORECASE),
        "description": "Direct request for score"
    },
    {
        "id": "impersonation",
        "regex": re.compile(r"(you\s+are\s+now|act\s+as)\s+(a\s+)?(grader|teacher)", re.IGNORECASE),
        "description": "Impersonating system prompt"
    }
]

def normalize_text(text: str) -> str:
    """Normalize text to detect injections hiding in weird casing or spacing."""
    # Unicode NFKC normalization
    text = unicodedata.normalize('NFKC', text)
    # Strip zero-width chars
    text = re.sub(r'[\u200B-\u200F\uFEFF]', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    # Lowercase
    return text.lower().strip()

def check_hidden_text(prop, tokens_by_id) -> Optional[RuleResult]:
    if prop.from_hidden_text:
        return RuleResult("HIDDEN_TEXT", True, "Proposition flagged as from_hidden_text")
    for tid in prop.token_ids:
        token = tokens_by_id.get(tid)
        if token and token.is_hidden:
            return RuleResult("HIDDEN_TEXT", True, f"Token {tid} is hidden")
    return None

def check_obfuscated_text(text: str) -> Optional[RuleResult]:
    if re.search(r'[\u200B-\u200F\u202A-\u202E\u2066-\u2069]', text):
        return RuleResult("OBFUSCATED_TEXT", True, "Found zero-width or bidirectional controls")
    return None

def check_injection_phrase(text: str) -> Optional[RuleResult]:
    norm_text = normalize_text(text)
    for pattern in INJECTION_PATTERNS:
        match = pattern["regex"].search(norm_text)
        if match:
            fragment = match.group(0)[:80]
            return RuleResult("INJECTION_PHRASE", True, f"Matched '{fragment}'")
    return None

def check_label_name(text: str) -> Optional[RuleResult]:
    norm_text = normalize_text(text)
    labels = ["full_credit", "partial_credit", "no_credit", "misconception"]
    for label in labels:
        if label.replace("_", " ") in norm_text or label in norm_text:
            return RuleResult("LABEL_NAME_IN_TEXT", True, f"Found label '{label}' in text")
    return None
