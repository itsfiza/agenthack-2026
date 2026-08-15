from typing import Dict, List, Any

from tools.web_search import search_web


def research_single_lead(
    company: Dict[str, Any],
    icp: Dict[str, Any],
) -> List[Dict[str, Any]]:

    company_name = company.get(
        "name",
        "Unknown Company"
    )

    queries = [
        f'"{company_name}" customer support',
        f'"{company_name}" WhatsApp',
        f'"{company_name}" automation',
        f'"{company_name}" AI',
        f'"{company_name}" ecommerce',
        f'"{company_name}" growth',
        f'"{company_name}" customer service',
    ]

    evidence = []

    seen_urls = set()

    for query in queries:

        print(
            f"  → Searching: {query}"
        )

        try:

            results = search_web(
                query=query,
                max_results=3
            )

            for result in results:

                url = result.get(
                    "url",
                    ""
                )

                if not url:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                evidence.append(
                    {
                        "title": result.get(
                            "title",
                            "Unknown"
                        ),
                        "url": url,
                        "description": result.get(
                            "description",
                            result.get(
                                "content",
                                ""
                            )
                        ),
                        "source": result.get(
                            "source",
                            "Web Search"
                        ),
                        "search_score": result.get(
                            "search_score",
                            result.get(
                                "score",
                                0
                            )
                        ),
                    }
                )

        except Exception as e:

            print(
                f"  ⚠ Search failed: {e}"
            )

    return evidence[:15]


# ============================================================
# LANGGRAPH RESEARCH NODE
# ============================================================

def research_leads(
    state
) -> dict:

    print(
        "\n" + "=" * 60
    )

    print(
        "[RESEARCH] Deep research on filtered leads"
    )

    print(
        "=" * 60
    )

    leads = state.get(
        "filtered_leads",
        []
    )

    icp = state.get(
        "icp",
        {}
    )

    research = {}

    errors = state.get(
        "errors",
        []
    )

    for lead in leads:

        company_name = lead.get(
            "name",
            "Unknown Company"
        )

        print(
            f"\nResearching: {company_name}"
        )

        try:

            evidence = research_single_lead(
                company=lead,
                icp=icp
            )

            research[
                company_name
            ] = evidence

            print(
                f"[RESEARCH] Collected "
                f"{len(evidence)} evidence items."
            )

        except Exception as e:

            print(
                f"[RESEARCH ERROR] {e}"
            )

            research[
                company_name
            ] = []

            errors.append(
                f"Research failed for "
                f"{company_name}: {str(e)}"
            )

    return {
        **state,
        "research": research,
        "errors": errors,
        "current_stage": "RESEARCH_COMPLETED",
    }