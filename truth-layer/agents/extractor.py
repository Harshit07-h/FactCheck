"""
Claim Extractor Agent
Uses OpenRouter (mistralai/mistral-7b-instruct:free) to extract verifiable factual claims from PDF text.
"""

import os
import json
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an expert fact-checking assistant. Your task is to extract ALL verifiable factual claims from the given text.

Focus on claims that can be verified, including:
- Statistics and percentages (e.g., "market grew by 35%")
- Financial figures (e.g., "revenue of $2.3 billion")
- Market size projections (e.g., "AI market will reach $1.8 trillion by 2030")
- Dates and timelines (e.g., "launched in 2022")
- Scientific/technical claims (e.g., "GPT-4 achieved 90% on benchmark X")
- Demographic data (e.g., "India has 500 million internet users")
- Rankings and comparisons
- Named product/company claims

DO NOT include:
- Opinions or subjective statements
- Vague generalisations without numbers
- Future predictions that are clearly labelled as estimates

For each claim, extract:
1. The exact claim text
2. Claim type (statistic, financial, date, technical, market_size, scientific, demographic, other)
3. The surrounding source text (for context)
4. The page number if visible (look for [PAGE N] markers)

Return ONLY valid JSON array, no preamble, no markdown fences:
[
  {
    "claim": "exact claim text",
    "type": "statistic",
    "source_text": "surrounding paragraph text",
    "page": 1
  }
]

Text to analyse:
"""


class ClaimExtractorAgent:
    """Extracts verifiable factual claims from text using OpenRouter LLM."""

    def __init__(self, provider: str = "openrouter", max_claims: int = 15):
        self.provider = provider  # kept for compatibility, always uses OpenRouter
        self.max_claims = max_claims

    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract factual claims from the given text."""
        truncated = text[:12000] if len(text) > 12000 else text

        try:
            raw = self._call_openrouter(truncated)
            claims = self._parse_json_response(raw)
            return claims[:self.max_claims]

        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            print(f"[EXTRACTOR ERROR] {type(e).__name__}: {e}")
            return self._fallback_extraction(text)

    def _call_openrouter(self, text: str) -> str:
        """Call OpenRouter API (OpenAI-compatible)."""
        from openai import OpenAI

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. "
                "Get a free key from https://openrouter.ai/keys "
                "and add to .streamlit/secrets.toml"
            )

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model="google/gemma-3-4b-it:free",  # primary free model
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert fact-checking assistant that extracts verifiable claims. Return ONLY valid JSON array, no markdown.",
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT + text,
                },
            ],
            temperature=0.1,
            max_tokens=4096,
            extra_headers={
                "HTTP-Referer": "https://truth-layer.streamlit.app",
                "X-Title": "Truth Layer Fact Checker",
            },
        )
        return response.choices[0].message.content

    def _parse_json_response(self, raw: str) -> List[Dict]:
        """Parse JSON from LLM response, stripping markdown fences."""
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().strip("`").strip()

        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")

        data = json.loads(cleaned[start:end])

        valid = []
        for item in data:
            if isinstance(item, dict) and item.get("claim"):
                valid.append({
                    "claim":       str(item.get("claim", "")).strip(),
                    "type":        str(item.get("type", "other")).lower().strip(),
                    "source_text": str(item.get("source_text", "")).strip()[:500],
                    "page":        item.get("page", "N/A"),
                })
        return valid

    def _fallback_extraction(self, text: str) -> List[Dict]:
        """Regex-based fallback when LLM fails."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        patterns = [
            r"\d+[\.,]?\d*\s*(%|percent|billion|million|trillion)",
            r"\b(19|20)\d{2}\b",
            r"\$\s*\d+",
            r"\d+\s*(million|billion|trillion)\s+(users|people|customers)",
        ]
        combined = re.compile("|".join(patterns), re.IGNORECASE)

        claims = []
        for sent in sentences:
            if combined.search(sent) and 20 < len(sent) < 500:
                claims.append({
                    "claim":       sent.strip(),
                    "type":        "statistic",
                    "source_text": sent.strip(),
                    "page":        "N/A",
                })
            if len(claims) >= 10:
                break

        return claims