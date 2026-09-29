from typing import List, Optional
from autorubric.contracts import Classification, Token, Proposition, CriticVerdict
from autorubric.contracts.grading import Candidate
from .rules import (
    CriticConfig, check_hidden_text, check_obfuscated_text,
    check_injection_phrase, check_label_name
)

def run_critic(
    classifications: List[Classification],
    tokens: List[Token],
    propositions: List[Proposition],
    candidates: Optional[List[Candidate]] = None,
    config: Optional[CriticConfig] = None
) -> List[CriticVerdict]:
    if config is None:
        config = CriticConfig()
        
    tokens_by_id = {t.id: t for t in tokens}
    props_by_id = {p.id: p for p in propositions}
    candidates_by_prop_crit = {}
    if candidates:
        for c in candidates:
            candidates_by_prop_crit[(c.prop_id, c.criterion_id)] = c

    # Keep track of criterion labels for CRITERION_CONFLICT
    crit_labels = {}
    for cls in classifications:
        if cls.criterion_id not in crit_labels:
            crit_labels[cls.criterion_id] = set()
        crit_labels[cls.criterion_id].add(cls.label.value)

    verdicts = []

    for cls in classifications:
        try:
            trusted = True
            flags = []
            reasons = []

            prop = props_by_id.get(cls.prop_id)
            if not prop:
                # If proposition doesn't exist, this is an error
                verdicts.append(CriticVerdict(
                    classification_id=cls.id,
                    trusted=False,
                    reason="Proposition not found",
                    flags=["CRITIC_ERROR"]
                ))
                continue
                
            text = prop.text

            # 1. Obfuscated Text
            res = check_obfuscated_text(text)
            if res:
                flags.append(res.flag)
                reasons.append(res.reason)
                if res.is_hard: trusted = False

            # 2. Hidden Text
            res = check_hidden_text(prop, tokens_by_id)
            if res:
                flags.append(res.flag)
                reasons.append(res.reason)
                if res.is_hard: trusted = False

            # 3. Injection Phrase
            res = check_injection_phrase(text)
            if res:
                flags.append(res.flag)
                reasons.append(res.reason)
                if res.is_hard: trusted = False

            # 4. Label Name
            res = check_label_name(text)
            if res:
                flags.append(res.flag)
                reasons.append(res.reason)
                if res.is_hard: trusted = False

            # 5. Low similarity, high confidence
            cand = candidates_by_prop_crit.get((cls.prop_id, cls.criterion_id))
            if cand and cand.similarity < config.low_similarity_threshold and cls.confidence > config.high_confidence_threshold:
                flags.append("LOW_SIMILARITY_HIGH_CONFIDENCE")
                reasons.append("High confidence but low retrieval similarity")
                # SOFT flag, trusted remains whatever it is

            # 6. Criterion Conflict
            if len(crit_labels.get(cls.criterion_id, set())) > 1:
                labels = crit_labels[cls.criterion_id]
                if "FULL_CREDIT" in labels and "MISCONCEPTION" in labels:
                    flags.append("CRITERION_CONFLICT")
                    reasons.append("Conflicting labels on the same criterion")
                    # SOFT flag

            verdicts.append(CriticVerdict(
                classification_id=cls.id,
                trusted=trusted,
                reason="; ".join(reasons) if reasons else "Looks standard.",
                flags=flags
            ))

        except Exception as e:
            verdicts.append(CriticVerdict(
                classification_id=cls.id,
                trusted=False,
                reason=f"Error evaluating rules: {str(e)[:80]}",
                flags=["CRITIC_ERROR"]
            ))

    return verdicts
