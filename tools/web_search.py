import os
import json
from typing import List, Dict, Any

from tavily import TavilyClient
from groq import Groq


# ============================================================
# TAVILY CLIENT
# ============================================================

def get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY is not set.")
    return TavilyClient(api_key=api_key)


# ============================================================
# WEB SEARCH
# ============================================================

def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
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
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
            "score": item.get("score", 0),
        })

    return results


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client() -> Groq:
    """
    Create Groq client using GROQ_API_KEY.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set."
        )

    return Groq(
        api_key=api_key
    )
# ============================================================
# EXTRACT REAL COMPANY NAMES
# ============================================================

def extract_company_names(
    search_results: List[Dict[str, Any]],
    max_companies: int = 10,
) -> List[str]:
    """
    Use Groq to extract real company names from web-search
    results.

    The LLM is NOT allowed to invent companies.
    It can only extract names supported by the provided
    search-result content.
    """

    client = get_groq_client()

    source_text = ""

    for i, result in enumerate(search_results):

        source_text += f"""
RESULT {i + 1}

TITLE:
{result.get("title", "")}

URL:
{result.get("url", "")}

CONTENT:
{result.get("content", "")[:4000]}

----------------------------------------
"""

    prompt = f"""
You are an entity extraction system for a B2B sales agent.

We are looking for REAL companies operating in Pakistan.

Extract ONLY actual company/business names mentioned
inside the provided search results.

DO NOT return:
- article titles
- directory names
- listicle titles
- websites
- social media pages
- marketplace categories
- generic descriptions
- phrases such as "Top 100 E-Commerce Companies"
- "GoodFirms"
- "ensun"
- "Shopify"
- "F6S"
- "StartupBlink"
- "Upwork"

IMPORTANT:
Only extract a company if the search-result content actually
mentions that company as a business.

Return ONLY valid JSON.

Format:

[
    "Company 1",
    "Company 2",
    "Company 3"
]

Maximum {max_companies} companies.

SEARCH RESULTS:

{source_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract real company entities from "
                    "web search evidence. Never invent names."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown fences if model adds them
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    try:
        companies = json.loads(raw)

        if not isinstance(companies, list):
            return []

        return [
            str(company).strip()
            for company in companies
            if str(company).strip()
        ][:max_companies]

    except json.JSONDecodeError:

        print(
            "[DISCOVERY] Could not parse company extraction response:"
        )

        print(raw)

        return []
# ============================================================
# HELPER — REJECT OBVIOUS NON-COMPANY SOURCES
# ============================================================

def is_obvious_non_company(url: str, title: str) -> bool:
    url = url.lower()
    title = title.lower()

    blocked_domains = [
        "instagram.com", "facebook.com", "youtube.com", "linkedin.com",
        "reddit.com", "twitter.com", "x.com", "tiktok.com",
    ]

    for domain in blocked_domains:
        if domain in url:
            return True

    return False


# ============================================================
# LLM SEED GENERATION
# ============================================================

def generate_seed_company_names(icp: dict, max_names: int = 12) -> List[str]:
    """
    Ask Claude for real, named companies fitting the ICP.
    Replaces generic keyword search as the discovery seed —
    search engines return articles/directories, not entities.
    """
    prompt = f"""List {max_names} real, currently operating companies matching this profile.
Location: {icp.get('location')}
Industry: {icp.get('industry')}
Company size: {icp.get('company_size')}

Return ONLY a JSON array of company names, nothing else.
Example: ["Daraz", "PriceOye", "Yayvo"]"""

    text = _call_llm(prompt)
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        names = json.loads(text)
    except json.JSONDecodeError:
        names = [
            line.strip("-•* ").strip()
            for line in text.split("\n")
            if line.strip()
        ]

    print(f"\n[SEED] Claude suggested {len(names)} companies: {names}")
    return names[:max_names]


# ============================================================
# COMPANY DISCOVERY BY NAME (verification via Tavily)
# ============================================================
def discover_companies_by_name(
    company_names: List[str],
    location: str = "",
    industry: str = "",
    target_problem: str = "",
    max_results_per_company: int = 3,
) -> List[Dict[str, Any]]:
    """
    Research real, named companies instead of treating
    directory/listicle pages as companies.

    The company names come from the seed-generation stage.
    Tavily is then used to verify/research each named company.
    """

    companies = []

    for company_name in company_names:

        company_name = company_name.strip()

        if not company_name:
            continue

        query_parts = [
            f'"{company_name}"',
        ]

        if location:
            query_parts.append(location)

        if industry:
            query_parts.append(industry)

        if target_problem:
            query_parts.append(target_problem)

        query = " ".join(query_parts)

        print(
            f"\n[DISCOVERY] Verifying company: {company_name}"
        )

        try:
            results = search_web(
                query=query,
                max_results=max_results_per_company,
            )

            # Look for the strongest result belonging
            # to the named company.
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

                combined = (
                    title
                    + " "
                    + url
                    + " "
                    + content
                ).lower()

                company_lower = company_name.lower()

                # Basic entity verification.
                if company_lower not in combined:
                    continue

                companies.append(
                    {
                        "name": company_name,
                        "website": url,
                        "description": content,
                        "search_score": result.get(
                            "score",
                            0
                        ),
                        "discovery_query": query,
                        "source": "Tavily Named Company Search",
                    }
                )

                print(
                    f"[DISCOVERY] ✓ Verified: {company_name}"
                )

                # One strongest result is enough
                # for the discovery stage.
                break

            else:
                print(
                    f"[DISCOVERY] ✗ Could not verify: {company_name}"
                )

        except Exception as e:

            print(
                f"[DISCOVERY] Search failed for "
                f"{company_name}: {e}"
            )

    return companies
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
    Discover REAL company entities.

    Tavily:
        Finds relevant web pages.

    Groq:
        Extracts actual company names from those pages.

    Tavily:
        Then researches each named company.
    """

    print(
        "\n[DISCOVERY] Starting entity-based company discovery"
    )

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

    # --------------------------------------------------------
    # STEP 1 — Find source pages
    # --------------------------------------------------------

    raw_results = search_web(
        query=query,
        max_results=max_results,
    )

    print(
        f"[DISCOVERY] Retrieved {len(raw_results)} web results."
    )

    if not raw_results:
        return []

    # --------------------------------------------------------
    # STEP 2 — Extract actual companies
    # --------------------------------------------------------

    company_names = extract_company_names(
        raw_results,
        max_companies=max_results,
    )

    print(
        f"[DISCOVERY] Extracted {len(company_names)} real company names."
    )

    for name in company_names:

        print(
            f"  ✓ {name}"
        )

    # --------------------------------------------------------
    # STEP 3 — Research each company
    # --------------------------------------------------------

    companies = []

    for company_name in company_names:

        print(
            f"\n[DISCOVERY] Verifying: {company_name}"
        )

        verification_query = (
            f'"{company_name}" '
            f'{location} '
            f'{industry} '
            f'company website'
        )

        verification_results = search_web(
            query=verification_query,
            max_results=3,
        )

        if not verification_results:
            print(
                f"[DISCOVERY] No evidence found for {company_name}"
            )
            continue

        best_result = verification_results[0]

        companies.append(
            {
                "name": company_name,
                "website": best_result.get(
                    "url",
                    ""
                ),
                "description": best_result.get(
                    "content",
                    ""
                ),
                "search_score": best_result.get(
                    "score",
                    0
                ),
                "discovery_query": query,
                "source": "Tavily + Groq Entity Discovery",
            }
        )

    print(
        f"\n[DISCOVERY] {len(companies)} verified companies accepted."
    )

    return companies


# ============================================================
# COMPANY ENTITY DISCOVERY (fallback — generic search)
# ============================================================

def discover_companies(
    location: str,
    industry: str,
    company_size: str = "",
    target_problem: str = "",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fallback discovery used only if Claude seed generation fails.
    Rejects obvious directories/listicles/social platforms.
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
        "ensun.io", "goodfirms.co", "designrush.com", "clutch.co",
        "linkedin.com", "facebook.com", "instagram.com", "youtube.com",
        "reddit.com", "medium.com", "forbes.com", "crunchbase.com",
    ]

    rejected_title_patterns = [
        "top ", "best ", "list of", "companies in", "companies -",
        "companies |", "directory", "reviews", "ranking", "ranked",
        "guide", "comparison", "marketplace", "emails & contacts",
    ]

    for query in query_variants:
        print(f"\n[DISCOVERY] Searching: {query}")

        try:
            results = search_web(query=query, max_results=max_results)
        except Exception as e:
            print(f"[DISCOVERY] Search failed: {e}")
            continue

        for result in results:
            title = result.get("title", "").strip()
            url = result.get("url", "").strip()
            content = result.get("content", "").strip()

            title_lower = title.lower()
            url_lower = url.lower()

            if any(domain in url_lower for domain in rejected_domains):
                print(f"[DISCOVERY] Rejected source: {title}")
                continue

            if any(pattern in title_lower for pattern in rejected_title_patterns):
                print(f"[DISCOVERY] Rejected list/article: {title}")
                continue

            company_signals = [
                "about us", "our services", "our products", "contact us",
                "solutions", "customers", "company", "we provide",
                "we offer", "founded",
            ]
            signal_count = sum(signal in content.lower() for signal in company_signals)

            if signal_count < 2:
                print(f"[DISCOVERY] Rejected weak entity: {title}")
                continue

            if any(existing["website"] == url for existing in candidates):
                continue

            candidate = {
                "name": title,
                "website": url,
                "description": content,
                "search_score": result.get("score", 0),
                "discovery_query": query,
                "source": "Tavily Web Search",
            }
            candidates.append(candidate)
            print(f"[DISCOVERY] Candidate accepted: {title}")

    candidates = sorted(candidates, key=lambda x: x.get("search_score", 0), reverse=True)
    candidates = candidates[:max_results]

    print(f"\n[DISCOVERY] {len(candidates)} company candidates accepted.")
    return candidates



# ============================================================
# SIMPLE COMPANY RESEARCH
# ============================================================

def research_company(company_name: str, website: str = "", max_results: int = 5) -> List[Dict[str, Any]]:
    query_parts = [f'"{company_name}"']
    if website:
        query_parts.append(website)
    query_parts.extend(["company", "products services", "customers", "growth"])
    query = " ".join(query_parts)
    return search_web(query=query, max_results=max_results)


# ============================================================
# DEEP RESEARCH
# ============================================================

def deep_research_company(company_name: str, website: str = "", max_results_per_query: int = 3):
    research_queries = [
        f'"{company_name}" products services',
        f'"{company_name}" customer support ecommerce',
        f'"{company_name}" automation AI technology',
        f'"{company_name}" WhatsApp customer service',
        f'"{company_name}" growth expansion news',
        f'"{company_name}" customers pain points',
        f'"{company_name}" contact leadership',
    ]

    all_evidence = []
    print(f"\nResearching: {company_name}")

    for query in research_queries:
        print(f'  → Searching: "{query}"')
        try:
            results = search_web(query=query, max_results=max_results_per_query)
        except Exception as e:
            print(f"  → Research search failed: {e}")
            continue

        for result in results:
            all_evidence.append({
                "company": company_name,
                "query": query,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "search_score": result.get("score", 0),
                "source": "Tavily",
            })

    print(f"[RESEARCH] Collected {len(all_evidence)} evidence items.")
    return all_evidence


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Web search tool loaded successfully.")

    test_icp = {
        "location": "Pakistan",
        "industry": "e-commerce",
        "company_size": "50-500 employees",
    }

    names = generate_seed_company_names(test_icp)
    leads = discover_companies_by_name(names)

    for l in leads:
        print(l["name"], "→", l["website"])