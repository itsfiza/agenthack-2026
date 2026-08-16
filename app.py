import streamlit as st
import time

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NexaFlow Autonomous Sales Agent",
    page_icon="🤖",
    layout="wide",
)

# ============================================================
# HEADER
# ============================================================

st.title("🤖 NexaFlow")
st.subheader("Autonomous Sales Intelligence Agent")

st.markdown(
    """
NexaFlow autonomously discovers, researches, qualifies,
and prepares personalized outreach for potential customers.
"""
)

st.divider()

# ============================================================
# SIDEBAR — ICP
# ============================================================

st.sidebar.header("🎯 Ideal Customer Profile")

location = st.sidebar.text_input(
    "Location",
    "Pakistan"
)

industry = st.sidebar.text_input(
    "Industry",
    "E-commerce"
)

company_size = st.sidebar.text_input(
    "Company Size",
    "50-500 employees"
)

target_problem = st.sidebar.text_input(
    "Target Problem",
    "Customer support automation"
)

st.sidebar.divider()

st.sidebar.info(
    "NexaFlow uses an agentic pipeline to move from "
    "company discovery → qualification → outreach."
)

# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None

# ============================================================
# RUN AGENT
# ============================================================

if st.button(
    "🚀 Run NexaFlow Agent",
    type="primary",
    use_container_width=True
):

    progress = st.progress(0)

    stages = [
        ("Creating Ideal Customer Profile", 15),
        ("Discovering companies", 30),
        ("Filtering candidates", 45),
        ("Researching leads", 60),
        ("Qualifying leads", 75),
        ("Matching service", 85),
        ("Generating outreach", 100),
    ]

    status = st.empty()

    for message, value in stages:
        status.write(f"🔄 {message}...")
        progress.progress(value)
        time.sleep(0.4)

    # --------------------------------------------------------
    # DEMO DATA
    # --------------------------------------------------------

    results = [
        {
            "company": "Daraz",
            "website": "https://www.daraz.pk",
            "score": 82,
            "status": "QUALIFIED",
            "service": "WhatsApp AI Assistant",
            "role": "Head of Customer Support / COO",
            "reason": (
                "Large-scale e-commerce operations and "
                "customer communication indicate a strong "
                "potential fit for support automation."
            ),
        },
        {
            "company": "PriceOye",
            "website": "https://priceoye.pk",
            "score": 76,
            "status": "QUALIFIED",
            "service": "Knowledge Assistant",
            "role": "Head of Customer Support / Operations",
            "reason": (
                "E-commerce operations and customer-facing "
                "product information create opportunities "
                "for AI-powered support."
            ),
        },
        {
            "company": "Yayvo",
            "website": "",
            "score": 58,
            "status": "POTENTIAL",
            "service": "Web AI Chatbot",
            "role": "Head of Customer Experience",
            "reason": (
                "Potential e-commerce support automation "
                "opportunity, but additional evidence is needed."
            ),
        },
    ]

    st.session_state.results = results

    status.success("✅ NexaFlow completed the sales pipeline.")

# ============================================================
# RESULTS
# ============================================================

if st.session_state.results:

    results = st.session_state.results

    st.divider()

    st.header("📊 Autonomous Pipeline")

    cols = st.columns(7)

    pipeline = [
        "ICP",
        "Discovery",
        "Filter",
        "Research",
        "Qualification",
        "Service Match",
        "Outreach",
    ]

    for col, stage in zip(cols, pipeline):

        with col:

            st.success("✓")

            st.caption(stage)

    st.divider()

    # ========================================================
    # METRICS
    # ========================================================

    qualified = [
        r for r in results
        if r["status"] == "QUALIFIED"
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Companies Discovered",
        len(results)
    )

    col2.metric(
        "Qualified Leads",
        len(qualified)
    )

    col3.metric(
        "Best Score",
        max(r["score"] for r in results)
    )

    col4.metric(
        "Pipeline Status",
        "CONTACTED"
    )

    # ========================================================
    # LEAD TABLE
    # ========================================================

    st.header("🎯 Qualified Leads")

    for lead in results:

        if lead["status"] == "QUALIFIED":

            with st.container(border=True):

                col1, col2 = st.columns([3, 1])

                with col1:

                    st.subheader(
                        lead["company"]
                    )

                    st.write(
                        lead["website"]
                    )

                    st.write(
                        f"**Recommended Service:** "
                        f"{lead['service']}"
                    )

                    st.write(
                        f"**Decision Maker:** "
                        f"{lead['role']}"
                    )

                with col2:

                    st.metric(
                        "Qualification Score",
                        f"{lead['score']}/100"
                    )

                    st.success(
                        lead["status"]
                    )

                st.info(
                    f"**Why this lead?** {lead['reason']}"
                )

    # ========================================================
    # OUTREACH
    # ========================================================

    st.divider()

    st.header("✉️ AI-Generated Outreach")

    selected = qualified[0] if qualified else results[0]

    subject = (
        f"AI automation opportunity for "
        f"{selected['company']}"
    )

    email = f"""Hi {selected['role']},

I came across {selected['company']} while researching
e-commerce businesses in Pakistan.

Based on the available research, there appears to be
an opportunity related to customer support and automation.

NexaFlow AI's {selected['service']} could be relevant
to this workflow.

Why this may be worth exploring:

{selected['reason']}

Would you be open to a short conversation about whether
this could fit your current workflow?

Best,
NexaFlow AI
"""

    st.text_input(
        "Subject",
        subject
    )

    st.text_area(
        "Email Draft",
        email,
        height=300
    )

    st.success(
        "📌 Outreach status: DRAFT READY"
    )

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    st.divider()

    st.header("🧠 Agent Architecture")

    st.code(
        """
Company Profile
       ↓
      ICP
       ↓
  Discovery Agent
       ↓
   Lead Filter
       ↓
 Research Agent
       ↓
Qualification Agent
       ↓
 Agentic Router
       ↓
 Service Matching
       ↓
Decision Maker
       ↓
Outreach Generator
       ↓
Pipeline Memory
        """,
        language="text"
    )

else:

    st.info(
        "Configure the ICP from the sidebar and click "
        "**Run NexaFlow Agent** to start."
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NexaFlow — AgentHack 2026 | Autonomous Sales Intelligence"
)