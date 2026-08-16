from typing import List, Dict, Any

from tools.web_search import search_web


# ============================================================
# COMPANY SEED DISCOVERY
# ============================================================

def discover_company_seeds(
    location: str,
    industry: str,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Find candidate company names from the web.

    Search results may be articles/listicles.
    Those pages are treated as SOURCES, not companies.

    The function extracts company-like names from result
    content using simple heuristics.
    """

    queries = [
        f"real {industry} companies in {location}",
        f"leading {industry} businesses in {location}",
        f"{industry} brands operating in {location}",
    ]

    seeds = []

    for query in queries:

        print(
            f"\n[SEED DISCOVERY] Searching: {query}"
        )

        results = search_web(
            query=query,
            max_results=5,
        )

        for result in results:

            title = result.get(
                "title",
                ""
            )

            url = result.get(
                "url",
                ""
            )

            content = result.get(
                "content",
                ""
            )

            # ----------------------------------------------
            # Only use the page as a discovery source.
            # We DO NOT call its title a company.
            # ----------------------------------------------

            source = {
                "source_title": title,
                "source_url": url,
                "content": content,
            }

            # Store the source for the next entity-resolution
            # step.

            seeds.append(source)

    return seeds