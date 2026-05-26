"""
search.py
Handles web search functionality using Tavily API.
Latest Tavily Python SDK integration.
"""

import os
from typing import List, Dict, Optional
from tavily import TavilyClient


class SearchEngine:
    """Search engine wrapper for Tavily API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search engine.

        Args:
            api_key: Tavily API key. If None, reads from environment variable.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key not found. Please set TAVILY_API_KEY in your .env file."
            )

        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 8) -> List[Dict]:
        """
        Search the web for evidence related to a claim.

        Args:
            query: The search query (typically the claim text)
            max_results: Maximum number of search results to return

        Returns:
            List of search result dictionaries
        """
        try:
            # Enhance query for better fact-checking results
            enhanced_query = f"fact check verify: {query}"

            response = self.client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
                include_raw_content=True
            )

            results = response.get("results", [])

            # Format results for consistency
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", "Untitled"),
                    "url": result.get("url", ""),
                    "snippet": result.get("content", ""),
                    "content": result.get("raw_content", result.get("content", "")),
                    "source": self._extract_domain(result.get("url", "")),
                    "score": result.get("score", 0)
                })

            return formatted_results

        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL for display."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain
        except:
            return "Unknown source"


class SearchError(Exception):
    """Custom exception for search-related errors."""
    pass


def perform_search(claim: str, api_key: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to perform a search for a claim.

    Args:
        claim: The claim to search for
        api_key: Optional Tavily API key

    Returns:
        List of search results
    """
    engine = SearchEngine(api_key=api_key)
    return engine.search(claim)
