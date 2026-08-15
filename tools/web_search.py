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
# COMPANY DISCOVERY
# ============================================================

def discover_companies(
    location: str,
    industry: str,
    company_size: str = "",
    target_problem: str = "",
    max_results: int = 10,
) -> List[Dict[str, Any]]:

    print(
        f"[DISCOVERY] Query: "
        f"{industry} companies "
        f"{location} "
        f"{company_size} "
        f"{target_problem}"
    )

    # --------------------------------------------------------
    # Use several targeted queries.
    #
    # This is much more reliable than one giant query.
    # --------------------------------------------------------

    queries = [
        f"{industry} companies {location} {company_size}",

        f"{industry} companies {location} "
        f"{target_problem}",

        f"{industry} businesses {location} "
        f"customer service automation",

        f"{industry} companies {location} "
        f"WhatsApp customer support",

        f"{industry} companies {location} AI automation",
    ]

    companies = []
    seen_urls = set()

    # --------------------------------------------------------
    # Search each query
    # --------------------------------------------------------

    for query in queries:

        print(
            f"\n[DISCOVERY] Searching: {query}"
        )

        try:

            raw_results = search_web(
                query=query,
                max_results=max_results,
            )

        except Exception as e:

            print(
                f"[DISCOVERY] Search failed: {e}"
            )

            continue

        for result in raw_results:

            name = result.get(
                "title",
                ""
            ).strip()

            url = result.get(
                "url",
                ""
            ).strip()

            description = result.get(
                "content",
                ""
            ).strip()

            # ------------------------------------------------
            # Skip empty results
            # ------------------------------------------------

            if not name or not url:
                continue

            # ------------------------------------------------
            # Avoid duplicate URLs
            # ------------------------------------------------

            if url in seen_urls:
                continue

            # ------------------------------------------------
            # Reject social media only
            # ------------------------------------------------

            if is_obvious_non_company(
                url,
                name
            ):

                print(
                    f"[DISCOVERY] Skipping social source: "
                    f"{name}"
                )

                continue

            # ------------------------------------------------
            # Basic relevance check
            # ------------------------------------------------

            text = (
                name
                + " "
                + description
            ).lower()

            relevance_terms = [
                "ecommerce",
                "e-commerce",
                "online store",
                "retail",
                "shop",
                "shopping",
                "customer",
                "support",
                "automation",
                "ai",
                "whatsapp",
                "commerce",
            ]

            relevance_score = sum(
                1
                for term in relevance_terms
                if term in text
            )

            # If the result has no relationship whatsoever
            # to our ICP, skip it.
            if relevance_score < 2:

                print(
                    f"[DISCOVERY] Skipping low relevance: "
                    f"{name}"
                )

                continue

            seen_urls.add(url)

            companies.append(
                {
                    "name": name,

                    "website": url,

                    "description": description,

                    "search_score": result.get(
                        "score",
                        0
                    ),

                    "relevance_score":
                        relevance_score,

                    "discovery_query": query,

                    "source":
                        "Tavily Web Search",
                }
            )

            print(
                f"[DISCOVERY] Candidate accepted: "
                f"{name}"
            )

            # ------------------------------------------------
            # Stop after enough candidates
            # ------------------------------------------------

            if len(companies) >= max_results:
                break

        if len(companies) >= max_results:
            break

    # --------------------------------------------------------
    # Rank candidates
    # --------------------------------------------------------

    companies = sorted(
        companies,
        key=lambda x: (
            x.get(
                "relevance_score",
                0
            ),
            x.get(
                "search_score",
                0
            ),
        ),
        reverse=True,
    )

    companies = companies[:max_results]

    print(
        f"\n[DISCOVERY] "
        f"{len(companies)} company candidates accepted."
    )

    return companies


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