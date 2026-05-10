"""
High-Accuracy Verifier Agent — OpenRouter Edition
Uses OpenRouter API (openrouter.ai) with free model: mistralai/mistral-7b-instruct
OpenRouter is OpenAI-compatible, so we use the openai SDK pointed at OpenRouter.

Setup:
1. Go to https://openrouter.ai/keys → create free API key
2. Add to .streamlit/secrets.toml:
   OPENROUTER_API_KEY = "sk-or-..."
"""

import os
import re
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS = [
    "wikipedia.org", "reuters.com", "forbes.com", "statista.com",
    "worldbank.org", "imf.org", "mckinsey.com", "openai.com",
    "who.int", "un.org", ".gov", ".edu",
]

PROMPT = """You are a professional forensic fact-checking AI.

Verify the claim using the web evidence below AND your own knowledge.

STRICT RULES:
- status = "VERIFIED"   if claim is factually correct
- status = "INACCURATE" if core idea is right but numbers/dates are wrong
- status = "FALSE"      if claim is clearly wrong or fabricated
- corrected_fact = exact correct info when FALSE or INACCURATE (NEVER leave empty)
- corrected_fact = "" only when VERIFIED
- Return ONLY valid JSON, no markdown, no explanation

CLAIM: "{claim}"

WEB EVIDENCE:
{evidence_text}

Return JSON ONLY:
{{"status":"VERIFIED","confidence":90,"corrected_fact":""}}"""

KNOWLEDGE_PROMPT = """You are a professional forensic fact-checking AI.
No web evidence available. Use your own knowledge.

STRICT RULES:
- status = "VERIFIED"   if claim is factually correct
- status = "INACCURATE" if core idea is right but numbers/dates are wrong
- status = "FALSE"      if claim is clearly wrong
- corrected_fact = exact correct info when FALSE or INACCURATE (NEVER leave empty)
- corrected_fact = "" only when VERIFIED
- Return ONLY valid JSON, no markdown, no explanation

CLAIM: "{claim}"

Return JSON ONLY:
{{"status":"VERIFIED","confidence":75,"corrected_fact":""}}"""


def _is_trusted(source: str) -> bool:
    source = source.lower()
    return any(domain in source for domain in TRUSTED_DOMAINS)


def extract_numbers(text: str):
    return re.findall(r'\$?\d+(?:,\d+)*(?:\.\d+)?%?', text)


def extract_years(text: str):
    return re.findall(r'(?:19|20)\d{2}', text)


def _format_evidence(evidence: List[Dict]) -> str:
    if not evidence:
        return "No web evidence available."
    lines = []
    for i, ev in enumerate(evidence[:5], 1):
        snippet = ev.get("snippet", "").strip()[:700]
        src = ev.get("source", "Unknown")
        url = ev.get("url", "")
        if snippet:
            lines.append(f"[{i}]\nSOURCE: {src}\nURL: {url}\nEVIDENCE:\n{snippet}\n")
    return "\n".join(lines) if lines else "No useful snippets."


class VerifierAgent:

    def __init__(self, provider: str = "gemini"):
        # provider argument kept for compatibility — always uses OpenRouter now
        self.provider = "openrouter"

    def verify(self, claim: Dict[str, Any], evidence: List[Dict]) -> Dict[str, Any]:
        claim_text = claim.get("claim", "")
        claim_type = claim.get("type", "unknown")

        # Filter trusted sources
        trusted_evidence = [e for e in evidence if _is_trusted(e.get("source", ""))]
        working_evidence = trusted_evidence if trusted_evidence else evidence

        # No evidence → knowledge-only path
        if not working_evidence:
            try:
                raw = self._call(KNOWLEDGE_PROMPT.format(claim=claim_text))
                verdict = self._parse(raw)
            except Exception as e:
                print(f"[VERIFIER ERROR - knowledge path] {type(e).__name__}: {e}")
                verdict = {
                    "status": "FALSE",
                    "confidence": 20,
                    "corrected_fact": f"API Error: {str(e)[:200]}",
                }
            return self._finalize(claim_text, claim_type, verdict, [])

        # Numeric / year analysis
        claim_numbers = extract_numbers(claim_text)
        claim_years   = extract_years(claim_text)

        ev_numbers, ev_years = [], []
        for ev in working_evidence:
            ev_numbers.extend(extract_numbers(ev.get("snippet", "")))
            ev_years.extend(extract_years(ev.get("snippet", "")))

        number_match = (not claim_numbers) or any(n in ev_numbers for n in claim_numbers)
        year_match   = (not claim_years)   or any(y in ev_years   for y in claim_years)

        # LLM call with evidence
        prompt = PROMPT.format(
            claim=claim_text,
            evidence_text=_format_evidence(working_evidence),
        )
        try:
            raw = self._call(prompt)
            verdict = self._parse(raw)
        except Exception as e:
            print(f"[VERIFIER ERROR - evidence path] {type(e).__name__}: {e}")
            verdict = {
                "status": "FALSE",
                "confidence": 25,
                "corrected_fact": f"API Error: {str(e)[:200]}",
            }

        # Confidence engine
        conf = 50
        if len(trusted_evidence) >= 3:
            conf += 20
        elif len(trusted_evidence) >= 1:
            conf += 10
        conf += 15 if number_match else -20
        conf += 10 if year_match   else -15
        conf += 10 if verdict["status"] == "VERIFIED" else (-10 if verdict["status"] == "FALSE" else 0)
        conf = max(0, min(100, conf))

        # Force INACCURATE if numbers/years don't match
        if not number_match and verdict["status"] == "VERIFIED":
            verdict["status"] = "INACCURATE"
        if not year_match and verdict["status"] == "VERIFIED":
            verdict["status"] = "INACCURATE"

        verdict["confidence"] = conf
        return self._finalize(claim_text, claim_type, verdict, working_evidence[:5])

    def _finalize(self, claim_text, claim_type, verdict, evidence):
        corrected = verdict.get("corrected_fact", "").strip()
        if verdict["status"] in ("FALSE", "INACCURATE") and not corrected:
            corrected = "Correct information could not be confidently determined."
        if verdict["status"] == "VERIFIED":
            corrected = ""
        return {
            "claim":          claim_text,
            "type":           claim_type,
            "status":         verdict["status"],
            "confidence":     verdict.get("confidence", 50),
            "corrected_fact": corrected,
            "evidence":       evidence,
        }

    def _call(self, prompt: str) -> str:
        return self._openrouter(prompt)

    def _openrouter(self, prompt: str) -> str:
        from openai import OpenAI

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. "
                "Get a free key from https://openrouter.ai/keys "
                "and add it to .streamlit/secrets.toml"
            )

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        resp = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",   # free model, no billing needed
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict forensic fact-checking AI. Return ONLY valid JSON, no markdown, no explanation.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.0,
            max_tokens=512,
            extra_headers={
                "HTTP-Referer": "https://truth-layer.streamlit.app",  # required by OpenRouter
                "X-Title": "Truth Layer Fact Checker",
            },
        )
        return resp.choices[0].message.content

    def _parse(self, raw: str) -> Dict:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No valid JSON in response: {raw[:200]}")
        data = json.loads(cleaned[start:end])

        status = str(data.get("status", "FALSE")).upper().strip()
        if status not in ("VERIFIED", "INACCURATE", "FALSE"):
            status = "FALSE"

        try:
            confidence = max(0, min(100, int(data.get("confidence", 50))))
        except (TypeError, ValueError):
            confidence = 50

        return {
            "status":         status,
            "confidence":     confidence,
            "corrected_fact": str(data.get("corrected_fact", "")).strip(),
        }