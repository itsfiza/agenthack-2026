from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, START, END

from tools.web_search import discover_companies


# ============================================================
# STATE
# ============================================================

class SalesState(TypedDict, total=False):

    # ICP
    icp: Dict[str, Any]

    # Discovery
    discovered_leads: List[Dict[str, Any]]

    # Filtering
    filtered_leads: List[Dict[str, Any]]

    # Status / debugging
    current_stage: str
    errors: List[str]


# ============================================================
# NODE 1 — CREATE ICP
# ============================================================

def create_icp(state: SalesState) -> SalesState:

    print("\n[ICP] Creating Ideal Customer Profile...")

    # MVP:
    # We use structured input first.
    # Later the LLM can convert natural-language user input
    # into this structure.

    icp = {
        "location": "Pakistan",
        "industry": "e-commerce",
        "company_size": "50-500 employees",
        "target_problem": "customer support automation",
    }

    print("[ICP] Created:")
    print(icp)

    return {
        **state,
        "icp": icp,
        "current_stage": "ICP_CREATED",
    }


# ============================================================
# NODE 2 — DISCOVER LEADS
# ============================================================

def discover_leads(state: SalesState) -> SalesState:

    print("\n[DISCOVERY] Searching the web...")

    icp = state["icp"]

    try:

        leads = discover_companies(
            location=icp["location"],
            industry=icp["industry"],
            company_size=icp["company_size"],
            target_problem=icp["target_problem"],
            max_results=5,
        )

        print(
            f"[DISCOVERY] Found {len(leads)} candidates."
        )

        return {
            **state,
            "discovered_leads": leads,
            "current_stage": "LEADS_DISCOVERED",
        }

    except Exception as e:

        errors = state.get(
            "errors",
            []
        )

        errors.append(
            f"Lead discovery failed: {str(e)}"
        )

        return {
            **state,
            "discovered_leads": [],
            "errors": errors,
            "current_stage": "DISCOVERY_FAILED",
        }


# ============================================================
# NODE 3 — CHEAP FILTER
# ============================================================

def filter_leads(state: SalesState) -> SalesState:

    print("\n[FILTER] Filtering candidates...")

    leads = state.get(
        "discovered_leads",
        []
    )

    filtered = []

    for lead in leads:

        title = lead.get(
            "name",
            ""
        ).lower()

        url = lead.get(
            "website",
            ""
        ).lower()

        description = lead.get(
            "description",
            ""
        ).lower()

        combined_text = (
            title
            + " "
            + url
            + " "
            + description
        )

        # ----------------------------------------------------
        # Basic quality signals
        # ----------------------------------------------------

        relevant_terms = [
            "ecommerce",
            "e-commerce",
            "online store",
            "retail",
            "shop",
            "customer support",
            "automation",
        ]

        # Reject obvious non-company sources
        bad_sources = [
            "instagram.com",
            "facebook.com",
            "youtube.com",
            "goodfirms.co",
            "linkedin.com",
        ]

        has_relevance = any(
            term in combined_text
            for term in relevant_terms
        )

        is_bad_source = any(
            source in url
            for source in bad_sources
        )

        if has_relevance and not is_bad_source:

            filtered.append(
                lead
            )

    # Keep only the best few candidates
    filtered = sorted(
        filtered,
        key=lambda x: x.get(
            "search_score",
            0
        ),
        reverse=True,
    )[:3]

    print(
        f"[FILTER] {len(filtered)} leads survived."
    )

    for lead in filtered:

        print(
            f"  ✓ {lead['name']}"
        )

    return {
        **state,
        "filtered_leads": filtered,
        "current_stage": "LEADS_FILTERED",
    }


# ============================================================
# GRAPH
# ============================================================

def build_sales_graph():

    graph = StateGraph(
        SalesState
    )

    # Add nodes
    graph.add_node(
        "create_icp",
        create_icp
    )

    graph.add_node(
        "discover_leads",
        discover_leads
    )

    graph.add_node(
        "filter_leads",
        filter_leads
    )

    # Edges
    graph.add_edge(
        START,
        "create_icp"
    )

    graph.add_edge(
        "create_icp",
        "discover_leads"
    )

    graph.add_edge(
        "discover_leads",
        "filter_leads"
    )

    graph.add_edge(
        "filter_leads",
        END
    )

    return graph.compile()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app = build_sales_graph()

    initial_state: SalesState = {
        "errors": []
    }

    final_state = app.invoke(
        initial_state
    )

    print(
        "\n========================================"
    )

    print(
        "FINAL STATE"
    )

    print(
        "========================================"
    )

    print(
        "Stage:",
        final_state.get(
            "current_stage"
        )
    )

    print(
        "ICP:",
        final_state.get(
            "icp"
        )
    )

    print(
        "Discovered:",
        len(
            final_state.get(
                "discovered_leads",
                []
            )
        )
    )

    print(
        "Filtered:",
        len(
            final_state.get(
                "filtered_leads",
                []
            )
        )
    )

    print(
        "Errors:",
        final_state.get(
            "errors",
            []
        )
    )