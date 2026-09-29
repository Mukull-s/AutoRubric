from autorubric.contracts import ScoreResult, Classification, Rubric, CriticVerdict, CriterionResult, Label
from decimal import Decimal, ROUND_HALF_UP
from autorubric.core.errors import PermanentError
from .rules import DECIMAL_PLACES
import networkx as nx

SCORER_VERSION = "1.0.0"

def score(classifications: list[Classification], rubric: Rubric, verdicts: list[CriticVerdict]) -> ScoreResult:
    # 1. Trust filter (fail closed)
    trusted_verdicts = {v.classification_id: v for v in verdicts if v.trusted}
    untrusted_verdicts = {v.classification_id: v for v in verdicts if not v.trusted}
    
    # 8. Robustness
    class_ids = set()
    for c in classifications:
        if c.id in class_ids:
            raise PermanentError(f"Duplicate classification id: {c.id}")
        class_ids.add(c.id)
        
    crit_ids = {c.id: c for c in rubric.criteria}
    
    # Build DAG
    G = nx.DiGraph()
    for c in rubric.criteria:
        G.add_node(c.id)
        for dep in c.depends_on:
            G.add_edge(dep, c.id)
            
    if not nx.is_directed_acyclic_graph(G):
        raise PermanentError("Rubric is not a DAG")
        
    order = list(nx.topological_sort(G))
    
    per_criterion = {}
    needs_review = False
    
    for crit_id in order:
        criterion = crit_ids[crit_id]
        
        # Filter classifications for this criterion
        crit_classifications = [c for c in classifications if c.criterion_id == crit_id]
        
        # Check if any classification for this criterion is untrusted
        is_criterion_trusted = True
        for c in crit_classifications:
            if c.id not in trusted_verdicts:
                is_criterion_trusted = False
                needs_review = True
                break
                
        if not is_criterion_trusted:
            per_criterion[crit_id] = CriterionResult(
                criterion_id=crit_id,
                label=Label.NO_CREDIT,
                credit=0.0,
                marks=0.0,
                evidence_bboxes=[],
                trusted=False
            )
            continue
            
        # All classifications for this criterion are trusted
        # Pick the label with highest credit
        best_c = None
        best_credit = Decimal('-1')
        
        for c in crit_classifications:
            credit = Decimal(str(getattr(rubric.credit_map, c.label.name)))
            if credit > best_credit:
                best_credit = credit
                best_c = c
            elif credit == best_credit and best_c is not None:
                if c.confidence > best_c.confidence:
                    best_c = c
                elif c.confidence == best_c.confidence:
                    if c.id < best_c.id:
                        best_c = c
        
        if best_c is None:
            per_criterion[crit_id] = CriterionResult(
                criterion_id=crit_id,
                label=Label.NO_CREDIT,
                credit=0.0,
                marks=0.0,
                evidence_bboxes=[],
                trusted=True
            )
            continue
            
        final_credit = best_credit
        capped = False
        
        # 4. DAG dependency cap
        for dep in criterion.depends_on:
            if dep in per_criterion:
                dep_res = per_criterion[dep]
                if dep_res.label in (Label.NO_CREDIT, Label.MISCONCEPTION) or getattr(rubric.credit_map, dep_res.label.name) == getattr(rubric.credit_map, Label.NO_CREDIT.name):
                    partial_credit = Decimal(str(getattr(rubric.credit_map, Label.PARTIAL_CREDIT.name)))
                    if final_credit > partial_credit:
                        final_credit = partial_credit
                        capped = True
                        
        marks = (Decimal(str(criterion.weight)) * final_credit).quantize(Decimal(DECIMAL_PLACES), rounding=ROUND_HALF_UP)
        
        per_criterion[crit_id] = CriterionResult(
            criterion_id=crit_id,
            label=best_c.label,
            credit=float(final_credit),
            marks=float(marks),
            evidence_bboxes=[],
            trusted=True
        )
        
    total_marks = sum(Decimal(str(res.marks)) for res in per_criterion.values())
    max_total = sum(Decimal(str(c.weight)) for c in rubric.criteria)
    
    total_marks = total_marks.quantize(Decimal(DECIMAL_PLACES), rounding=ROUND_HALF_UP)
    max_total = max_total.quantize(Decimal(DECIMAL_PLACES), rounding=ROUND_HALF_UP)
    
    return ScoreResult(
        doc_id="unknown",
        rubric_id=rubric.id,
        per_criterion=list(per_criterion.values()),
        total=float(total_marks),
        max_total=float(max_total),
        needs_review=needs_review
    )
