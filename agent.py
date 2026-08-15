from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, START, END

from tools.web_search import discover_companies
from agents.qualification import qualify_lead
from agents.research import research_leads

# ============================================================
# STATE
# ============================================================

class SalesState(TypedDict, total=False):

    # --------------------------------------------------------
    # Company / NexaFlow
    # --------------------------------------------------------
    company_profile: Dict[str, Any]

    # --------------------------------------------------------
    # ICP
    # --------------------------------------------------------
    icp: Dict[str, Any]

    # --------------------------------------------------------
    # Lead discovery
    # --------------------------------------------------------
    discovered_leads: List[Dict[str, Any]]

    # --------------------------------------------------------
    # Cheap filtering
    # --------------------------------------------------------
    filtered_leads: List[Dict[str, Any]]

    # --------------------------------------------------------
    # Deep research
    # --------------------------------------------------------
    research: Dict[str, List[Dict[str, Any]]]

    # --------------------------------------------------------
    # Qualification
    # --------------------------------------------------------
    qualifications: Dict[str, Dict[str, Any]]

    # --------------------------------------------------------
    # Selected lead
    # --------------------------------------------------------
    selected_lead: Dict[str, Any]
    selected_score: int
    # --------------------------------------------------------
    # Service matching
    # --------------------------------------------------------
    recommended_service: Dict[str, Any]

    # --------------------------------------------------------
    # Decision maker
    # --------------------------------------------------------
    decision_maker: Dict[str, Any]

    # --------------------------------------------------------
    # Outreach
    # --------------------------------------------------------
    outreach: Dict[str, Any]

    # --------------------------------------------------------
    # Pipeline
    # --------------------------------------------------------
    pipeline_status: str

    # --------------------------------------------------------
    # Current stage
    # --------------------------------------------------------
    current_stage: str

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------
    errors: List[str]


# ============================================================
# NODE 1 — CREATE ICP
# ============================================================

def create_icp(state: SalesState) -> SalesState:

    print("\n" + "=" * 60)
    print("[ICP] Creating Ideal Customer Profile")
    print("=" * 60)

    # --------------------------------------------------------
    # MVP structured ICP
    # --------------------------------------------------------
    icp = {
        "location": "Pakistan",
        "industry": "e-commerce",
        "company_size": "50-500 employees",
        "target_problem": "customer support automation",
    }

    print("\n[ICP] Created:")
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

    print("\n" + "=" * 60)
    print("[DISCOVERY] Searching the web")
    print("=" * 60)

    icp = state.get("icp", {})

    try:

        leads = discover_companies(
            location=icp.get("location", ""),
            industry=icp.get("industry", ""),
            company_size=icp.get("company_size", ""),
            target_problem=icp.get("target_problem", ""),
            max_results=5,
        )

        print(
            f"\n[DISCOVERY] Found {len(leads)} candidates."
        )

        for lead in leads:
            print(
                f"  • {lead.get('name', 'Unknown')}"
            )

        return {
            **state,
            "discovered_leads": leads,
            "current_stage": "LEADS_DISCOVERED",
        }

    except Exception as e:

        error_message = (
            f"Lead discovery failed: {str(e)}"
        )

        print(f"\n[ERROR] {error_message}")

        errors = list(
            state.get("errors", [])
        )

        errors.append(error_message)

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

    print("\n" + "=" * 60)
    print("[FILTER] Filtering candidates")
    print("=" * 60)

    leads = state.get(
        "discovered_leads",
        []
    )

    filtered = []

    # --------------------------------------------------------
    # Domains that are not actual prospect companies
    # --------------------------------------------------------
    bad_domains = [
        "instagram.com",
        "facebook.com",
        "youtube.com",
        "goodfirms.co",
        "linkedin.com",
        "reddit.com",
        "medium.com",
    ]

    # --------------------------------------------------------
    # Signals that suggest a company/business page
    # --------------------------------------------------------
    content_indicators = [
        "our services",
        "our products",
        "about us",
        "contact us",
        "we offer",
        "company",
        "business",
    ]

    # --------------------------------------------------------
    # Signals relevant to our ICP
    # --------------------------------------------------------
    industry_indicators = [
        "ecommerce",
        "e-commerce",
        "online store",
        "retail",
        "shop",
        "customer support",
        "automation",
        "whatsapp",
    ]

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
            + description
        )

        # ----------------------------------------------------
        # 1. Reject obvious directory/social sources
        # ----------------------------------------------------

        is_bad_domain = any(
            domain in url
            for domain in bad_domains
        )

        if is_bad_domain:
            continue

        # ----------------------------------------------------
        # 2. Company/business signal
        # ----------------------------------------------------

        has_company_signal = any(
            term in combined_text
            for term in content_indicators
        )

        # ----------------------------------------------------
        # 3. ICP relevance
        # ----------------------------------------------------

        has_industry_signal = any(
            term in combined_text
            for term in industry_indicators
        )

        # ----------------------------------------------------
        # 4. Accept candidate
        # ----------------------------------------------------

        if (
            has_company_signal
            and has_industry_signal
        ):
            filtered.append(lead)

    # --------------------------------------------------------
    # Rank by search confidence
    # --------------------------------------------------------

    filtered = sorted(
        filtered,
        key=lambda x: x.get(
            "search_score",
            0
        ),
        reverse=True,
    )[:3]

    print(
        f"\n[FILTER] {len(filtered)} leads survived."
    )

    for lead in filtered:

        print(
            f"  ✓ {lead.get('name', 'Unknown')}"
        )

    return {
        **state,
        "filtered_leads": filtered,
        "current_stage": "LEADS_FILTERED",
    }


# ============================================================
# NODE 4 — DEEP RESEARCH
# ============================================================
#
# IMPORTANT:
# Your research node already exists elsewhere in your project.
# This wrapper expects a function called `research_company`.
#
# If your existing research function has a different name,
# change ONLY the import/function call here.
# ============================================================

# ============================================================
# NODE 4 — DEEP RESEARCH
# ============================================================

def research_filtered_leads(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[RESEARCH] Deep research on filtered leads")
    print("=" * 60)

    leads = state.get(
        "filtered_leads",
        []
    )

    icp = state.get(
        "icp",
        {}
    )

    if not leads:

        print(
            "[RESEARCH] No filtered leads."
        )

        return {
            **state,
            "research": {},
            "current_stage": "RESEARCH_SKIPPED",
        }

    try:

        research = research_leads(
            leads=leads,
            icp=icp,
        )

        return {
            **state,
            "research": research,
            "current_stage": "RESEARCH_COMPLETED",
        }

    except Exception as e:

        print(
            f"[ERROR] Research failed: {e}"
        )

        errors = state.get(
            "errors",
            []
        )

        errors.append(
            f"Research failed: {str(e)}"
        )

        return {
            **state,
            "research": {},
            "errors": errors,
            "current_stage": "RESEARCH_FAILED",
        }

# ============================================================
# NODE 5 — QUALIFICATION
# ============================================================

def qualify_leads(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[QUALIFICATION]")
    print("=" * 60)

    filtered_leads = state.get(
        "filtered_leads",
        []
    )

    research = state.get(
        "research",
        {}
    )

    icp = state.get(
        "icp",
        {}
    )

    qualifications = {}

    for lead in filtered_leads:

        company_name = lead.get(
            "name",
            "Unknown"
        )

        print(
            f"\n[QUALIFICATION] Evaluating: {company_name}"
        )

        evidence = research.get(
            company_name,
            []
        )

        try:

            result = qualify_lead(
                company=lead,
                icp=icp,
                evidence=evidence,
            )

            qualifications[
                company_name
            ] = result

            print(
                f"  Score: {result.get('total_score', 0)}/100"
            )

            print(
                f"  Status: {result.get('status', 'UNKNOWN')}"
            )

        except Exception as e:

            print(
                f"  ✗ Qualification failed: {e}"
            )

            qualifications[
                company_name
            ] = {
                "total_score": 0,
                "status": "NOT_QUALIFIED",
                "reason": (
                    f"Qualification failed: {str(e)}"
                ),
                "evidence": [],
            }

    return {
        **state,
        "qualifications": qualifications,
        "current_stage": "LEADS_QUALIFIED",
    }


# ============================================================
# ROUTER — AFTER QUALIFICATION
# ============================================================

def route_after_qualification(
    state: SalesState
) -> str:

    print("\n" + "=" * 60)
    print("[ROUTER] Qualification decision")
    print("=" * 60)

    qualifications = state.get(
        "qualifications",
        {}
    )

    if not qualifications:

        print(
            "[ROUTER] No qualifications found."
        )

        return "no_qualified_leads"

    # --------------------------------------------------------
    # Find highest scoring lead
    # --------------------------------------------------------

    best_company_name = max(
        qualifications,
        key=lambda company_name:
            qualifications[
                company_name
            ].get(
                "total_score",
                0
            )
    )

    best_result = qualifications[
        best_company_name
    ]

    score = best_result.get(
        "total_score",
        0
    )

    print(
        f"\nBest lead: {best_company_name}"
    )

    print(
        f"Score: {score}/100"
    )

    # --------------------------------------------------------
    # Agentic decision
    # --------------------------------------------------------

    if score >= 60:

        print(
            "[ROUTER] → SERVICE MATCH"
        )

        return "service_match"

    print(
        "[ROUTER] → NO QUALIFIED LEADS"
    )

    return "no_qualified_leads"


# ============================================================
# NODE 6 — SELECT BEST LEAD
# ============================================================

def select_best_lead(
    state: SalesState
) -> SalesState:

    qualifications = state.get(
        "qualifications",
        {}
    )

    filtered_leads = state.get(
        "filtered_leads",
        []
    )

    if not qualifications:

        return {
            **state,
            "current_stage": "NO_QUALIFIED_LEADS",
        }

    # --------------------------------------------------------
    # Highest score
    # --------------------------------------------------------

    best_company_name = max(
        qualifications,
        key=lambda company_name:
            qualifications[
                company_name
            ].get(
                "total_score",
                0
            )
    )

    # --------------------------------------------------------
    # Find corresponding lead object
    # --------------------------------------------------------

    selected_lead = None

    for lead in filtered_leads:

        if (
            lead.get("name")
            == best_company_name
        ):

            selected_lead = lead
            break

    if selected_lead is None:

        selected_lead = {
            "name": best_company_name
        }

    score = qualifications[
        best_company_name
    ].get(
        "total_score",
        0
    )

    print(
        f"\n[SELECT] Selected lead:"
        f" {best_company_name}"
    )

    print(
        f"[SELECT] Score: {score}/100"
    )

    return {
        **state,
        "selected_lead": selected_lead,
        "current_stage": "LEAD_SELECTED",
    }


# ============================================================
# NODE 7 — SERVICE MATCHING
# ============================================================
#
# This uses NexaFlow's RAG-backed company knowledge.
#
# For the MVP we use deterministic matching first.
# This is safer than asking an LLM to randomly choose
# a service.
# ============================================================

def match_service(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[SERVICE MATCH]")
    print("=" * 60)

    lead = state.get(
        "selected_lead",
        {}
    )

    company_name = lead.get(
        "name",
        "Unknown"
    )

    research = state.get(
        "research",
        {}
    )

    evidence = research.get(
        company_name,
        []
    )

    evidence_text = " ".join(
        str(item)
        for item in evidence
    ).lower()

    # --------------------------------------------------------
    # Service matching rules
    # --------------------------------------------------------

    service_rules = [

        {
            "keywords": [
                "whatsapp",
                "whatsapp automation",
                "whatsapp support",
            ],
            "service": "WhatsApp AI Assistant",
            "reason": (
                "Evidence indicates WhatsApp-based "
                "customer communication or automation."
            ),
        },

        {
            "keywords": [
                "customer support",
                "customer service",
                "support automation",
                "faq",
                "knowledge base",
            ],
            "service": "Knowledge Assistant",
            "reason": (
                "Evidence indicates a customer-support "
                "or knowledge-retrieval problem."
            ),
        },

        {
            "keywords": [
                "workflow",
                "operations",
                "process automation",
            ],
            "service": "Workflow Automation",
            "reason": (
                "Evidence indicates repetitive "
                "business workflows suitable for automation."
            ),
        },

        {
            "keywords": [
                "sales",
                "lead generation",
                "crm",
                "conversion",
            ],
            "service": "Sales Automation",
            "reason": (
                "Evidence indicates sales or lead-management "
                "automation opportunities."
            ),
        },

        {
            "keywords": [
                "voice",
                "call",
                "phone",
            ],
            "service": "AI Voice Agent",
            "reason": (
                "Evidence indicates voice or phone-based "
                "customer interaction."
            ),
        },
    ]

    selected_service = None

    # --------------------------------------------------------
    # Check strongest service signals
    # --------------------------------------------------------

    for rule in service_rules:

        matched_keywords = [
            keyword
            for keyword in rule["keywords"]
            if keyword in evidence_text
        ]

        if matched_keywords:

            selected_service = {
                "service": rule["service"],
                "reason": rule["reason"],
                "matched_signals": matched_keywords,
                "evidence_based": True,
            }

            break

    # --------------------------------------------------------
    # Safe fallback
    # --------------------------------------------------------

    if selected_service is None:

        selected_service = {
            "service": "Web AI Chatbot",
            "reason": (
                "The available evidence does not provide "
                "a stronger service-specific signal."
            ),
            "matched_signals": [],
            "evidence_based": False,
        }

    print(
        f"\n[SERVICE MATCH] {selected_service['service']}"
    )

    print(
        f"[SERVICE MATCH] Reason:"
        f" {selected_service['reason']}"
    )

    return {
        **state,
        "recommended_service": selected_service,
        "current_stage": "SERVICE_MATCHED",
    }


# ============================================================
# NODE 8 — DECISION MAKER
# ============================================================

def find_decision_maker(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[DECISION MAKER]")
    print("=" * 60)

    service_info = state.get(
        "recommended_service",
        {}
    )

    service = service_info.get(
        "service",
        ""
    )

    # --------------------------------------------------------
    # MVP role mapping
    # --------------------------------------------------------

    role_map = {

        "WhatsApp AI Assistant":
            "Head of Customer Support / COO",

        "Knowledge Assistant":
            "Head of Customer Support / Operations",

        "Workflow Automation":
            "COO / Head of Operations",

        "Sales Automation":
            "Head of Sales / CRO",

        "AI Voice Agent":
            "Head of Customer Experience / COO",

        "Web AI Chatbot":
            "Head of Customer Experience / Marketing",
    }

    target_role = role_map.get(
        service,
        "COO / Head of Operations"
    )

    decision_maker = {
        "target_role": target_role,
        "service": service,
        "status": "ROLE_IDENTIFIED",
        "note": (
            "MVP identifies the most relevant "
            "decision-maker role. Actual contact "
            "enrichment can be added later."
        ),
    }

    print(
        f"[DECISION MAKER] Target:"
        f" {target_role}"
    )

    return {
        **state,
        "decision_maker": decision_maker,
        "current_stage": "DECISION_MAKER_IDENTIFIED",
    }


# ============================================================
# NODE 9 — PERSONALIZED OUTREACH
# ============================================================

def generate_outreach(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[OUTREACH]")
    print("=" * 60)

    lead = state.get(
        "selected_lead",
        {}
    )

    company_name = lead.get(
        "name",
        "your company"
    )

    service_info = state.get(
        "recommended_service",
        {}
    )

    service = service_info.get(
        "service",
        "AI automation"
    )

    decision_maker = state.get(
        "decision_maker",
        {}
    )

    target_role = decision_maker.get(
        "target_role",
        "your team"
    )

    qualifications = state.get(
        "qualifications",
        {}
    )

    qualification = qualifications.get(
        company_name,
        {}
    )

    reason = qualification.get(
        "reason",
        ""
    )

    # --------------------------------------------------------
    # Evidence-backed email
    # --------------------------------------------------------

    subject = (
        f"AI automation opportunity for {company_name}"
    )

    body = f"""Hi {target_role},

I came across {company_name} while researching
e-commerce businesses in Pakistan.

Based on the available research, there appears to be
an opportunity related to customer support and
automation.

NexaFlow AI's {service} could be relevant to this
workflow.

Why this may be worth exploring:
{reason}

Would you be open to a short conversation about
whether this could fit your current workflow?

Best,
NexaFlow AI
"""

    outreach = {
        "channel": "email",
        "subject": subject,
        "body": body,
        "target_role": target_role,
        "grounded_reason": reason,
        "status": "DRAFT",
    }

    print(
        f"[OUTREACH] Draft generated for {company_name}"
    )

    return {
        **state,
        "outreach": outreach,
        "pipeline_status": "CONTACTED",
        "current_stage": "OUTREACH_READY",
    }


# ============================================================
# NODE 10 — NO QUALIFIED LEADS
# ============================================================

def no_qualified_leads(
    state: SalesState
) -> SalesState:

    print("\n" + "=" * 60)
    print("[PIPELINE] No qualified leads")
    print("=" * 60)

    return {
        **state,
        "pipeline_status": "NOT_QUALIFIED",
        "current_stage": "NO_QUALIFIED_LEADS",
    }


# ============================================================
# GRAPH
# ============================================================

def build_sales_graph():

    graph = StateGraph(
        SalesState
    )

    # --------------------------------------------------------
    # Add nodes
    # --------------------------------------------------------

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

    graph.add_node(
        "research_leads",
        research_leads
    )

    graph.add_node(
        "qualify_leads",
        qualify_leads
    )

    graph.add_node(
        "select_best_lead",
        select_best_lead
    )

    graph.add_node(
        "service_match",
        match_service
    )

    graph.add_node(
        "decision_maker",
        find_decision_maker
    )

    graph.add_node(
        "generate_outreach",
        generate_outreach
    )

    graph.add_node(
        "no_qualified_leads",
        no_qualified_leads
    )

    # --------------------------------------------------------
    # Main pipeline
    # --------------------------------------------------------

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
        "research_leads"
    )

    graph.add_edge(
        "research_leads",
        "qualify_leads"
    )

    # --------------------------------------------------------
    # AGENTIC CONDITIONAL ROUTING
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "qualify_leads",
        route_after_qualification,
        {
            "service_match":
                "select_best_lead",

            "no_qualified_leads":
                "no_qualified_leads",
        }
    )

    # --------------------------------------------------------
    # Qualified path
    # --------------------------------------------------------

    graph.add_edge(
        "select_best_lead",
        "service_match"
    )

    graph.add_edge(
        "service_match",
        "decision_maker"
    )

    graph.add_edge(
        "decision_maker",
        "generate_outreach"
    )

    graph.add_edge(
        "generate_outreach",
        END
    )

    # --------------------------------------------------------
    # Negative path
    # --------------------------------------------------------

    graph.add_edge(
        "no_qualified_leads",
        END
    )

    return graph.compile()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    print(
        "\n"
        + "=" * 60
    )

    print(
        "NexaFlow Autonomous Sales Agent"
    )

    print(
        "=" * 60
    )

    app = build_sales_graph()

    initial_state: SalesState = {
        "errors": [],
        "company_profile": {},
    }

    final_state = app.invoke(
        initial_state
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FINAL STATE"
    )

    print(
        "=" * 60
    )

    print(
        "\nStage:",
        final_state.get(
            "current_stage"
        )
    )

    print(
        "\nICP:"
    )

    print(
        final_state.get(
            "icp"
        )
    )

    print(
        "\nDiscovered leads:",
        len(
            final_state.get(
                "discovered_leads",
                []
            )
        )
    )

    print(
        "\nFiltered leads:",
        len(
            final_state.get(
                "filtered_leads",
                []
            )
        )
    )

    print(
        "\nQualifications:"
    )

    for (
        company,
        result
    ) in final_state.get(
        "qualifications",
        {}
    ).items():

        print(
            f"  {company}: "
            f"{result.get('total_score', 0)}/100 "
            f"({result.get('status', 'UNKNOWN')})"
        )

    print(
        "\nSelected lead:"
    )

    print(
        final_state.get(
            "selected_lead"
        )
    )

    print(
        "\nRecommended service:"
    )

    print(
        final_state.get(
            "recommended_service"
        )
    )

    print(
        "\nDecision maker:"
    )

    print(
        final_state.get(
            "decision_maker"
        )
    )

    print(
        "\nPipeline status:"
    )

    print(
        final_state.get(
            "pipeline_status"
        )
    )

    print(
        "\nErrors:"
    )

    print(
        final_state.get(
            "errors",
            []
        )
    )

    print(
        "\n"
        + "=" * 60
    )