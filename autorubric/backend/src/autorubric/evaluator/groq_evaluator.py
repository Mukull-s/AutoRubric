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

def get_endpoint_and_models(key: str) -> tuple[str, list[str]]:
    """Determine API endpoint and priority model list based on key format."""
    if key.startswith("xai-"):
        endpoint = os.environ.get("GROK_ENDPOINT", "https://api.x.ai/v1/chat/completions")
        models = [
            os.environ.get("GROQ_MODEL") or os.environ.get("GROK_MODEL") or "grok-2-latest",
            "grok-beta",
            "grok-2",
        ]
        return endpoint, [m for m in models if m]

    endpoint = os.environ.get("GROQ_ENDPOINT", "https://api.groq.com/openai/v1/chat/completions")
    custom_model = os.environ.get("GROQ_MODEL")
    default_models = [
        custom_model,
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    seen = set()
    models = []
    for m in default_models:
        if m and m not in seen:
            seen.add(m)
            models.append(m)
    return endpoint, models


def get_groq_api_key() -> str:
    return (
        os.environ.get("GROQ_API_KEY")
        or os.environ.get("GROK_API_KEY")
        or config.GROQ_API_KEY
        or ""
    )


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
        "You are an expert academic evaluator and grading auditor specializing in evaluating student exam papers, "
        "including scanned documents and handwritten submissions transcribed via OCR.\n\n"
        "IMPORTANT OCR CONTEXT:\n"
        "Submissions may be extracted via Optical Character Recognition (OCR) from handwritten notes, scanned photos, or PDFs. "
        "Handwritten mathematics and formulas frequently produce OCR noise, typos, character substitutions, and broken mathematical symbols. "
        "For example:\n"
        "- '(x0 + x1)/2' or midpoint may appear as 'mial-point x?+x1 2' or 'x?+x1'\n"
        "- 'f(a)*f(b) < 0' may appear as 'fhy+f?ax??.5?x?<0'\n"
        "- 'Bisection' or 'Regula Falsi' may appear as 'Bisection Methocl Bruckefing' or 'Regu(afalsr)'\n"
        "- 'Always converges' may appear as 'Alcvays conrerges'\n"
        "- Euler's theorem, partial derivatives du/dx, and homogeneous functions may appear as 'degeen,Hhen fu=FM', 'utam,shha', 'Nolen', '+2xy2u', 'x?4+2xy41+y-u=0'\n\n"
        "GRADING PRINCIPLES:\n"
        "1. DO NOT penalize the student for OCR noise, mangled characters, or handwriting transcription errors.\n"
        "2. If the student clearly demonstrated or attempted the required method, formula, step, or concept (even if partially garbled by OCR), award FULL_CREDIT (or PARTIAL_CREDIT if only an initial step is shown).\n"
        "3. Flexible mathematical matching: Rubrics may describe a standard problem variation (e.g. u = arctan(y/x) or homogeneous functions of degree n, bisection/secant methods). If the student solved or attempted an equivalent or related textbook variation of the problem (e.g. u = arctan((x^3+y^3)/(x-y)) with degree n, or stated first/second order Euler equations, midpoints, or interval checks), award corresponding credit for each step addressed.\n"
        "4. Only award NO_CREDIT if a criterion is completely unaddressed or absent in the student's submission.\n\n"
        "Allowed labels:\n"
        "- FULL_CREDIT: Complete or substantially correct fulfillment of the criterion (accounting for OCR noise).\n"
        "- PARTIAL_CREDIT: Incomplete explanation or only partial components present.\n"
        "- MISCONCEPTION: Contains an explicit factual error, contradiction, or fundamental scientific misconception.\n"
        "- NO_CREDIT: Completely absent or unaddressed.\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "evaluations": [\n'
        "    {\n"
        '      "criterion_id": "criterion id from rubric",\n'
        '      "label": "FULL_CREDIT" | "PARTIAL_CREDIT" | "MISCONCEPTION" | "NO_CREDIT",\n'
        '      "confidence": 0.95,\n'
        '      "evidence_quote": "relevant verbatim excerpt or phrase from the student submission, or empty string",\n'
        '      "reasoning": "brief 1-sentence justification acknowledging OCR context"\n'
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

    endpoint, candidate_models = get_endpoint_and_models(key)

    payload = {
        "model": candidate_models[0] if candidate_models else "llama-3.3-70b-versatile",
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
            resp = None
            for model_name in candidate_models:
                payload["model"] = model_name
                try:
                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        break
                    logger.warning(f"LLM API {resp.status_code} with model {model_name}: {resp.text}")
                except Exception as ex:
                    logger.warning(f"Request failed with model {model_name}: {ex}")

            if not resp or resp.status_code != 200:
                logger.error("All candidate LLM models failed. Falling back to heuristic.")
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
