import os
from typing import List, Dict, Any

from tavily import TavilyClient


# ============================================================
# TAVILY CLIENT
# ============================================================

def get_tavily_client() -> TavilyClient:
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

    client = get_tavily_client()

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
        include_raw_content=False,
    )

    results = []

    for item in response.get("results", []):

        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0),
            }
        )

    return results


# ============================================================
# HELPER — REJECT OBVIOUS NON-COMPANY SOURCES
# ============================================================

def is_obvious_non_company(url: str, title: str) -> bool:

    url = url.lower()
    title = title.lower()

    blocked_domains = [
        "instagram.com",
        "facebook.com",
        "youtube.com",
        "linkedin.com",
        "reddit.com",
        "twitter.com",
        "x.com",
        "tiktok.com",
    ]

    for domain in blocked_domains:
        if domain in url:
            return True

    return False
# ============================================================
# COMPANY ENTITY DISCOVERY
# ============================================================

def discover_companies(
    location: str,
    industry: str,
    company_size: str = "",
    target_problem: str = "",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Discover REAL company entities.

    Search engines often return:
        - directories
        - listicles
        - blog posts
        - social media
        - comparison pages

    These are NOT companies.

    This function attempts to reject those pages and only
    return results that look like actual company websites.
    """

    query_variants = [
        f"{industry} companies {location} {company_size}",
        f"{industry} businesses {location} customer support",
        f"{industry} companies {location} WhatsApp",
        f"{industry} companies {location} AI automation",
        f"{industry} companies {location} customer service",
    ]

    candidates = []

    rejected_domains = [
        "ensun.io",
        "goodfirms.co",
        "designrush.com",
        "clutch.co",
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "reddit.com",
        "medium.com",
        "forbes.com",
        "crunchbase.com",
    ]

    rejected_title_patterns = [
        "top ",
        "best ",
        "list of",
        "companies in",
        "companies -",
        "companies |",
        "directory",
        "reviews",
        "ranking",
        "ranked",
        "guide",
        "comparison",
        "marketplace",
        "emails & contacts",
    ]

    for query in query_variants:

        print(
            f"\n[DISCOVERY] Searching: {query}"
        )

        try:

            results = search_web(
                query=query,
                max_results=max_results,
            )

        except Exception as e:

            print(
                f"[DISCOVERY] Search failed: {e}"
            )

            continue

        for result in results:

            title = (
                result.get(
                    "title",
                    ""
                )
                .strip()
            )

            url = (
                result.get(
                    "url",
                    ""
                )
                .strip()
            )

            content = (
                result.get(
                    "content",
                    ""
                )
                .strip()
            )

            title_lower = title.lower()
            url_lower = url.lower()

            # ------------------------------------------------
            # Reject known directories/social platforms
            # ------------------------------------------------

            if any(
                domain in url_lower
                for domain in rejected_domains
            ):

                print(
                    f"[DISCOVERY] Rejected source: {title}"
                )

                continue

            # ------------------------------------------------
            # Reject obvious listicles/articles
            # ------------------------------------------------

            if any(
                pattern in title_lower
                for pattern in rejected_title_patterns
            ):

                print(
                    f"[DISCOVERY] Rejected list/article: {title}"
                )

                continue

            # ------------------------------------------------
            # Basic company-content signals
            # ------------------------------------------------

            company_signals = [
                "about us",
                "our services",
                "our products",
                "contact us",
                "solutions",
                "customers",
                "company",
                "we provide",
                "we offer",
                "founded",
            ]

            signal_count = sum(
                signal in content.lower()
                for signal in company_signals
            )

            if signal_count < 2:

                print(
                    f"[DISCOVERY] Rejected weak entity: {title}"
                )

                continue

            # ------------------------------------------------
            # Avoid duplicates
            # ------------------------------------------------

            if any(
                existing["website"] == url
                for existing in candidates
            ):

                continue

            # ------------------------------------------------
            # Accept candidate
            # ------------------------------------------------

            candidate = {
                "name": title,
                "website": url,
                "description": content,
                "search_score": result.get(
                    "score",
                    0
                ),
                "discovery_query": query,
                "source": "Tavily Web Search",
            }

            candidates.append(
                candidate
            )

            print(
                f"[DISCOVERY] Candidate accepted: {title}"
            )

    # --------------------------------------------------------
    # Sort by search confidence
    # --------------------------------------------------------

    candidates = sorted(
        candidates,
        key=lambda x: x.get(
            "search_score",
            0
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # Limit results
    # --------------------------------------------------------

    candidates = candidates[
        :max_results
    ]

    print(
        f"\n[DISCOVERY] "
        f"{len(candidates)} company candidates accepted."
    )

    return candidates


# ============================================================
# SIMPLE COMPANY RESEARCH
# ============================================================

def research_company(
    company_name: str,
    website: str = "",
    max_results: int = 5,
) -> List[Dict[str, Any]]:

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


# ============================================================
# DEEP RESEARCH
# ============================================================

def deep_research_company(
    company_name: str,
    website: str = "",
    max_results_per_query: int = 3,
):

    research_queries = [

        f'"{company_name}" '
        f'products services',

        f'"{company_name}" '
        f'customer support ecommerce',

        f'"{company_name}" '
        f'automation AI technology',

        f'"{company_name}" '
        f'WhatsApp customer service',

        f'"{company_name}" '
        f'growth expansion news',

        f'"{company_name}" '
        f'customers pain points',

        f'"{company_name}" '
        f'contact leadership',
    ]

    all_evidence = []

    print(
        f"\nResearching: {company_name}"
    )

    for query in research_queries:

        print(
            f'  → Searching: "{query}"'
        )

        try:

            results = search_web(
                query=query,
                max_results=
                    max_results_per_query,
            )

        except Exception as e:

            print(
                f"  → Research search failed: "
                f"{e}"
            )

            continue

        for result in results:

            all_evidence.append(
                {
                    "company":
                        company_name,

                    "query":
                        query,

                    "title":
                        result.get(
                            "title",
                            ""
                        ),

                    "url":
                        result.get(
                            "url",
                            ""
                        ),

                    "content":
                        result.get(
                            "content",
                            ""
                        ),

                    "search_score":
                        result.get(
                            "score",
                            0
                        ),

                    "source":
                        "Tavily",
                }
            )

    print(
        f"[RESEARCH] Collected "
        f"{len(all_evidence)} evidence items."
    )

    return all_evidence


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Web search tool loaded successfully."
    )