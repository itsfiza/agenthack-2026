import os
import json
from typing import List, Dict, Any

from tavily import TavilyClient
from anthropic import Anthropic


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
# LLM CLIENT — GOOGLE GEMINI (free tier)
# ============================================================

from google import genai

def _call_llm(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


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
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Verify each named company via Tavily and pull its real website + content.
    """
    rejected_domains = [
        "ensun.io", "goodfirms.co", "designrush.com", "clutch.co",
        "linkedin.com", "facebook.com", "instagram.com", "youtube.com",
        "reddit.com", "medium.com", "forbes.com", "crunchbase.com",
        "wikipedia.org",
    ]

    candidates = []

    for name in company_names:
        query = f'"{name}" official website'
        print(f"\n[DISCOVERY] Verifying: {name}")

        try:
            results = search_web(query=query, max_results=3)
        except Exception as e:
            print(f"[DISCOVERY] Search failed for {name}: {e}")
            continue

        best = None
        for result in results:
            url = result.get("url", "").lower()
            if any(domain in url for domain in rejected_domains):
                continue
            best = result
            break

        if not best:
            print(f"[DISCOVERY] No clean website found for {name}, skipping.")
            continue

        candidate = {
            "name": name,
            "website": best.get("url", ""),
            "description": best.get("content", ""),
            "search_score": best.get("score", 0),
            "discovery_query": query,
            "source": "Claude seed + Tavily verification",
        }
        candidates.append(candidate)
        print(f"[DISCOVERY] Candidate accepted: {name} → {candidate['website']}")

    candidates = candidates[:max_results]
    print(f"\n[DISCOVERY] {len(candidates)} company candidates accepted.")
    return candidates


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