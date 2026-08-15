import os
from typing import List, Dict, Any
from urllib.parse import urlparse

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
# DOMAIN HELPERS
# ============================================================

def extract_domain(url: str) -> str:
    """
    Extract clean domain from a URL.
    """

    try:
        parsed = urlparse(url)

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def is_directory_or_social_domain(url: str) -> bool:
    """
    Reject obvious directories, social platforms and
    review/listing websites during company discovery.
    """

    domain = extract_domain(url)

    blocked_domains = [
        "instagram.com",
        "facebook.com",
        "linkedin.com",
        "youtube.com",
        "twitter.com",
        "x.com",
        "reddit.com",
        "goodfirms.co",
        "clutch.co",
        "ensun.io",
        "crunchbase.com",
        "wikipedia.org",
        "medium.com",
        "yelp.com",
        "tripadvisor.com",
    ]

    return any(
        domain == blocked
        or domain.endswith("." + blocked)
        for blocked in blocked_domains
    )


def looks_like_company_page(
    title: str,
    url: str,
    content: str,
) -> bool:
    """
    Heuristic check for whether a search result looks like
    an actual company/business page instead of an article,
    directory, social page or generic list.
    """

    text = (
        title
        + " "
        + content[:4000]
    ).lower()

    # ----------------------------------------------
    # Reject obvious article/list pages
    # ----------------------------------------------

    article_signals = [
        "top ",
        "best ",
        "guide",
        "list",
        "reviews",
        "statistics",
        "how to",
        "2026",
        "2025",
        "companies in pakistan",
        "companies in",
        "leading companies",
        "directory",
        "ranking",
    ]

    title_lower = title.lower()

    # If the TITLE itself strongly looks like an article/list,
    # don't treat it as the company.
    if any(
        signal in title_lower
        for signal in article_signals
    ):
        return False

    # ----------------------------------------------
    # Company/business signals
    # ----------------------------------------------

    company_signals = [
        "about us",
        "our services",
        "our products",
        "contact us",
        "we offer",
        "who we are",
        "our company",
        "founded",
        "headquartered",
        "employees",
        "solutions",
        "services",
    ]

    has_company_signal = any(
        signal in text
        for signal in company_signals
    )

    # ----------------------------------------------
    # Must have a real-looking domain
    # ----------------------------------------------

    domain = extract_domain(url)

    if not domain:
        return False

    if is_directory_or_social_domain(url):
        return False

    return has_company_signal


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
    Search results are candidates only.
    We reject obvious articles, directories and social
    pages before passing candidates to the sales pipeline.
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

    query = " ".join(query_parts)

    print(
        f"[DISCOVERY] Query: {query}"
    )

    raw_results = search_web(
        query=query,
        max_results=max_results,
    )

    companies = []

    seen_domains = set()

    for result in raw_results:

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

        domain = extract_domain(url)

        # ----------------------------------------------
        # Reject directories/social platforms
        # ----------------------------------------------

        if is_directory_or_social_domain(url):

            print(
                f"[DISCOVERY] Skipping non-company source: {title}"
            )

            continue

        # ----------------------------------------------
        # Reject duplicate domains
        # ----------------------------------------------

        if domain in seen_domains:

            continue

        # ----------------------------------------------
        # Reject obvious article/list pages
        # ----------------------------------------------

        if not looks_like_company_page(
            title=title,
            url=url,
            content=content,
        ):

            print(
                f"[DISCOVERY] Skipping article/list result: {title}"
            )

            continue

        seen_domains.add(domain)

        # ----------------------------------------------
        # Create clean candidate
        # ----------------------------------------------

        companies.append(
            {
                "name": title,
                "website": url,
                "domain": domain,
                "description": content,
                "search_score": result.get(
                    "score",
                    0
                ),
                "discovery_query": query,
                "source": "Tavily Web Search",
                "lead_type": "company_candidate",
            }
        )

    # ----------------------------------------------
    # Rank candidates
    # ----------------------------------------------

    companies = sorted(
        companies,
        key=lambda x: x.get(
            "search_score",
            0
        ),
        reverse=True,
    )[:max_results]

    print(
        f"[DISCOVERY] {len(companies)} company candidates accepted."
    )

    for company in companies:

        print(
            f"  ✓ {company['name']} "
            f"| {company['domain']}"
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


# ============================================================
# DEEP RESEARCH
# ============================================================

def deep_research_company(
    company_name: str,
    website: str = "",
    max_results_per_query: int = 3,
):
    """
    Perform structured research on a candidate company.

    Evidence categories:
        1. Products/services
        2. Customer support / pain points
        3. AI / automation
        4. Growth / expansion
    """

    research_queries = [
        f'"{company_name}" products services',
        f'"{company_name}" customer support ecommerce',
        f'"{company_name}" automation AI technology',
        f'"{company_name}" growth expansion news',
    ]

    all_evidence = []

    for query in research_queries:

        print(
            f'  → Searching: "{query}"'
        )

        results = search_web(
            query=query,
            max_results=max_results_per_query,
        )

        for result in results:

            all_evidence.append(
                {
                    "company": company_name,
                    "query": query,
                    "title": result.get(
                        "title",
                        ""
                    ),
                    "url": result.get(
                        "url",
                        ""
                    ),
                    "content": result.get(
                        "content",
                        ""
                    ),
                    "search_score": result.get(
                        "score",
                        0
                    ),
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