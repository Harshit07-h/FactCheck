"""
Search Agent
Retrieves live web evidence for each claim.
"""

import logging
from typing import List, Dict

from utils.web_search import search_web

logger = logging.getLogger(__name__)

# Credibility tiers for source scoring
HIGH_CREDIBILITY_DOMAINS = [
    "gov", "edu", "who.int", "worldbank.org", "imf.org",
    "statista.com", "gartner.com", "mckinsey.com", "forbes.com",
    "reuters.com", "bloomberg.com", "nature.com", "sciencedirect.com",
    "wikipedia.org", "techcrunch.com", "wired.com",
]


class SearchAgent:
    """Searches the web to gather evidence for claim verification."""

    def __init__(self, provider: str = "duckduckgo", max_results: int = 5):
        self.provider = provider
        self.max_results = max_results

    def search(self, claim: str) -> List[Dict[str, str]]:
        """
        Search for evidence related to the given claim.
        Returns list of {source, url, snippet, credibility_score}.
        """
        # Build targeted query
        query = self._build_query(claim)

        try:
            raw_results = search_web(
                query=query,
                provider=self.provider,
                max_results=self.max_results,
            )
            # Score credibility
            scored = [self._score_result(r) for r in raw_results]
            # Sort by credibility (highest first)
            scored.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
            return scored

        except Exception as e:
            logger.error(f"Search failed for claim '{claim[:50]}': {e}")
            return []

    def _build_query(self, claim: str) -> str:
        """Build an optimised search query from the claim."""
        # Trim and clean
        claim = claim.strip()[:200]
        # Remove hedge words that make bad queries
        stop_phrases = ["according to", "it is said", "reportedly", "allegedly"]
        for phrase in stop_phrases:
            claim = claim.replace(phrase, "").strip()
        # Add 'fact check' or 'statistics' context
        return f"{claim} statistics fact"

    def _score_result(self, result: Dict) -> Dict:
        """Add credibility score based on source domain."""
        url = result.get("url", "").lower()
        score = 50  # default

        for domain in HIGH_CREDIBILITY_DOMAINS:
            if domain in url:
                score = 90
                break

        # Penalise clearly low-quality sources
        low_quality = ["reddit.com", "quora.com", "yahoo.com/answers"]
        for domain in low_quality:
            if domain in url:
                score = 30
                break

        result["credibility_score"] = score
        return result
