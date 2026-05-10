"""
Web Search Utility
Supports Tavily, DuckDuckGo, and SerpAPI for live fact retrieval.
"""

import os
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# ── Cache (simple in-memory) ──────────────────────────────────────────────────
_search_cache: Dict[str, List[Dict]] = {}


def search_web(
    query: str,
    provider: str = "tavily",
    max_results: int = 5,
    use_cache: bool = True,
) -> List[Dict[str, str]]:
    """
    Search the web and return a list of evidence snippets.
    Each result: {"source": str, "url": str, "snippet": str}
    """
    cache_key = f"{provider}::{query}"
    if use_cache and cache_key in _search_cache:
        logger.debug(f"Cache hit for: {query[:50]}")
        return _search_cache[cache_key]

    results: List[Dict[str, str]] = []

    try:
        if provider == "tavily":
            results = _search_tavily(query, max_results)
        elif provider == "serpapi":
            results = _search_serpapi(query, max_results)
        else:
            results = _search_duckduckgo(query, max_results)
    except Exception as e:
        logger.warning(f"Search provider '{provider}' failed: {e}. Falling back to DuckDuckGo.")
        try:
            results = _search_duckduckgo(query, max_results)
        except Exception as fallback_err:
            logger.error(f"All search providers failed: {fallback_err}")
            results = []

    _search_cache[cache_key] = results
    return results


def _search_tavily(query: str, max_results: int) -> List[Dict[str, str]]:
    """Search using Tavily API."""
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set")

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "source": r.get("title", "Unknown"),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:500],
            })

        # Prepend Tavily's synthesised answer if available
        if response.get("answer"):
            results.insert(0, {
                "source": "Tavily Synthesis",
                "url": "https://tavily.com",
                "snippet": response["answer"][:500],
            })

        return results

    except ImportError:
        raise ImportError("tavily-python not installed. Run: pip install tavily-python")


def _search_duckduckgo(query: str, max_results: int) -> List[Dict[str, str]]:
    """Search using DuckDuckGo (no API key required)."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "source": r.get("title", "Unknown"),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:500],
                })
                time.sleep(0.1)  # be polite

        return results

    except ImportError:
        raise ImportError("duckduckgo-search not installed. Run: pip install duckduckgo-search")


def _search_serpapi(query: str, max_results: int) -> List[Dict[str, str]]:
    """Search using SerpAPI."""
    try:
        import requests
        api_key = os.getenv("SERPAPI_KEY", "")
        if not api_key:
            raise ValueError("SERPAPI_KEY not set")

        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results,
            "engine": "google",
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()

        results = []
        for r in data.get("organic_results", [])[:max_results]:
            results.append({
                "source": r.get("title", "Unknown"),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", "")[:500],
            })

        return results

    except Exception as e:
        raise RuntimeError(f"SerpAPI error: {e}")
