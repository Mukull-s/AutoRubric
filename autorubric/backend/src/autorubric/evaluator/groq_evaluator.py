"""Groq-powered Evaluator Module for AutoRubric.

Evaluates student submission text against arbitrary rubrics with LLM speed and high accuracy.
Preserves existing contracts and provides robust fallback if the API is offline.
"""

from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

from autorubric.contracts import Label, Classification, Rubric, Criterion
from autorubric.core.config import config

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODEL = "qwen/qwen3.8-27b"


def get_groq_api_key() -> str:
    return os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY or ""


async def evaluate_submission_with_groq(
    pdf_text: str,
    rubric: Rubric,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Evaluates student text against rubric criteria using Groq.

    Returns a list of dicts:
    [
        {
            "criterion_id": str,
            "label": Label,
            "confidence": float,
            "evidence_quote": str,
            "reasoning": str
        },
        ...
    ]
    """
    key = api_key or get_groq_api_key()
    if not key:
        logger.warning("GROQ_API_KEY not found. Falling back to heuristic classification.")
        return _heuristic_evaluation(pdf_text, rubric)

    criteria_summary = "\n".join([
        f"- ID: {c.id} | Description: {c.description} | Weight: {c.weight}"
        for c in rubric.criteria
    ])

    system_prompt = (
        "You are an expert academic evaluator and grading auditor. "
        "Evaluate the provided student submission text against each rubric criterion objectively.\n\n"
        "Allowed labels:\n"
        "- FULL_CREDIT: Complete and accurate fulfillment of the criterion.\n"
        "- PARTIAL_CREDIT: Incomplete or partially correct explanation.\n"
        "- MISCONCEPTION: Contains an explicit factual error, contradiction, or scientific misconception.\n"
        "- NO_CREDIT: Not mentioned, completely unaddressed, or irrelevant.\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "evaluations": [\n'
        "    {\n"
        '      "criterion_id": "criterion id from rubric",\n'
        '      "label": "FULL_CREDIT" | "PARTIAL_CREDIT" | "MISCONCEPTION" | "NO_CREDIT",\n'
        '      "confidence": 0.95,\n'
        '      "evidence_quote": "exact verbatim excerpt from the student submission supporting this grade, or empty string",\n'
        '      "reasoning": "brief 1-sentence justification"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    user_content = (
        f"RUBRIC TITLE: {rubric.title}\n\n"
        f"RUBRIC CRITERIA:\n{criteria_summary}\n\n"
        f"STUDENT SUBMISSION TEXT:\n\"\"\"\n{pdf_text[:12000]}\n\"\"\"\n\n"
        "Evaluate every criterion listed above."
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GROQ_ENDPOINT, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning(f"Groq API {resp.status_code} with {DEFAULT_MODEL}, trying fallback model {FALLBACK_MODEL}...")
                payload["model"] = FALLBACK_MODEL
                resp = await client.post(GROQ_ENDPOINT, headers=headers, json=payload)
            
            if resp.status_code != 200:
                logger.error(f"Groq API Error {resp.status_code}: {resp.text}")
                return _heuristic_evaluation(pdf_text, rubric)

            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            evals = parsed.get("evaluations", [])

            results = []
            crit_ids = {c.id for c in rubric.criteria}
            seen_ids = set()

            for item in evals:
                cid = item.get("criterion_id")
                if cid in crit_ids and cid not in seen_ids:
                    seen_ids.add(cid)
                    lbl_str = item.get("label", "NO_CREDIT")
                    try:
                        lbl = Label(lbl_str)
                    except ValueError:
                        lbl = Label.NO_CREDIT

                    results.append({
                        "criterion_id": cid,
                        "label": lbl,
                        "confidence": float(item.get("confidence", 0.9)),
                        "evidence_quote": str(item.get("evidence_quote", "")),
                        "reasoning": str(item.get("reasoning", "")),
                    })

            # Ensure all criteria have an evaluation entry
            for c in rubric.criteria:
                if c.id not in seen_ids:
                    results.append({
                        "criterion_id": c.id,
                        "label": Label.NO_CREDIT,
                        "confidence": 0.8,
                        "evidence_quote": "",
                        "reasoning": "Criterion was not addressed in the submission.",
                    })

            return results

    except Exception as e:
        logger.error(f"Groq evaluation call failed: {e}. Falling back to heuristic.")
        return _heuristic_evaluation(pdf_text, rubric)


def _heuristic_evaluation(pdf_text: str, rubric: Rubric) -> List[Dict[str, Any]]:
    """Heuristic fallback if Groq API key is missing or network fails."""
    import re
    text_words = set(re.findall(r"\b\w+\b", pdf_text.lower()))
    results = []

    for c in rubric.criteria:
        c_words = set(re.findall(r"\b\w+\b", c.description.lower()))
        overlap = len(text_words.intersection(c_words)) / max(len(c_words), 1)

        if overlap >= 0.4:
            lbl = Label.FULL_CREDIT
            conf = min(0.95, 0.7 + overlap * 0.3)
        elif overlap >= 0.2:
            lbl = Label.PARTIAL_CREDIT
            conf = 0.65
        else:
            lbl = Label.NO_CREDIT
            conf = 0.8

        results.append({
            "criterion_id": c.id,
            "label": lbl,
            "confidence": round(conf, 2),
            "evidence_quote": "",
            "reasoning": f"Heuristic overlap score: {round(overlap, 2)}",
        })

    return results
