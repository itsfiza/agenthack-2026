import os
from typing import List, Dict, Any

from tavily import TavilyClient


# ============================================================
# TAVILY CLIENT
# ============================================================

def get_tavily_client() -> TavilyClient:
    """
    Create Tavily client using the environment variable.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "TAVILY_API_KEY is not set."
        )

    return TavilyClient(
        api_key=api_key
    )


# ============================================================
# WEB SEARCH
# ============================================================

def search_web(
    query: str,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search the public web and return structured results.

    This is our first external research tool.
    """

    client = get_tavily_client()

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
        include_raw_content=False,
    )

    results = []

    for item in response.get(
        "results",
        []
    ):

        results.append(
            {
                "title": item.get(
                    "title",
                    ""
                ),
                "url": item.get(
                    "url",
                    ""
                ),
                "content": item.get(
                    "content",
                    ""
                ),
                "score": item.get(
                    "score",
                    0
                ),
            }
        )

    return results


# ============================================================
# COMPANY DISCOVERY
# ============================================================

def discover_companies(
    location: str,
    industry: str,
    company_size: str = "",
    target_problem: str = "",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Discover potential companies matching an ICP.

    IMPORTANT:
    The search engine provides the candidates.
    The LLM does NOT invent company names.
    """

    query_parts = [
        f"{industry} companies",
        location,
    ]

    if company_size:
        query_parts.append(
            company_size
        )

    if target_problem:
        query_parts.append(
            target_problem
        )

    query = " ".join(
        query_parts
    )

    raw_results = search_web(
        query=query,
        max_results=max_results,
    )

    companies = []

    for result in raw_results:

        companies.append(
            {
                "name": result["title"],
                "website": result["url"],
                "description": result["content"],
                "search_score": result["score"],
                "discovery_query": query,
                "source": "Tavily Web Search",
            }
        )

    return companies


# ============================================================
# SIMPLE RESEARCH
# ============================================================

def research_company(
    company_name: str,
    website: str = "",
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Perform deeper web research about a candidate company.

    We deliberately keep this separate from discovery.
    """

    query_parts = [
        f'"{company_name}"',
    ]

    if website:
        query_parts.append(
            website
        )

    query_parts.extend(
        [
            "company",
            "products services",
            "customers",
            "growth",
        ]
    )

    query = " ".join(
        query_parts
    )

    return search_web(
        query=query,
        max_results=max_results,
    )
def deep_research_company(
    company_name: str,
    website: str = "",
    max_results_per_query: int = 3,
):
    """
    Perform structured research on a candidate company.

    We search multiple evidence categories separately so the
    qualification stage receives useful evidence rather than
    one generic search result.
    """

    research_queries = [
        f'"{company_name}" products services',
        f'"{company_name}" customer support ecommerce',
        f'"{company_name}" automation AI technology',
        f'"{company_name}" growth expansion news',
    ]

    all_evidence = []

    for query in research_queries:

        results = search_web(
            query=query,
            max_results=max_results_per_query,
        )

        for result in results:

            all_evidence.append(
                {
                    "company": company_name,
                    "query": query,
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["content"],
                    "search_score": result["score"],
                    "source": "Tavily",
                }
            )

    return all_evidence

# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Web search tool loaded successfully."
    )