import json
from typing import Dict, Any, List

from langchain_groq import ChatGroq


# ============================================================
# LLM
# ============================================================

def get_llm():

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )


# ============================================================
# FORMAT EVIDENCE
# ============================================================

def format_evidence(
    evidence: List[Dict[str, Any]]
) -> str:

    formatted = []

    for i, item in enumerate(
        evidence,
        start=1
    ):

        formatted.append(
            f"""
EVIDENCE {i}

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Content:
{item.get("content", "")[:1500]}
"""
        )

    return "\n".join(
        formatted
    )


# ============================================================
# QUALIFICATION
# ============================================================

def qualify_lead(
    company: Dict[str, Any],
    icp: Dict[str, Any],
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:

    llm = get_llm()

    evidence_text = format_evidence(
        evidence
    )

    prompt = f"""
You are a B2B sales qualification analyst.

Your job is to evaluate ONE potential prospect for
NexaFlow AI.

IMPORTANT RULES:

1. Use ONLY the provided ICP and research evidence.
2. Do NOT invent company facts.
3. If evidence is missing, say that it is missing.
4. Do not treat a search result title alone as proof.
5. Every important conclusion must be supported by evidence.
6. Return ONLY valid JSON.
7. The total score MUST equal the sum of the five
   category scores.

NEXAFLOW SERVICES:

NexaFlow offers:

- Web AI Chatbot
- WhatsApp AI Assistant
- Workflow Automation
- AI Voice Agent
- Knowledge Assistant
- Sales Automation

ICP:

{json.dumps(icp, indent=2)}

COMPANY:

{json.dumps(company, indent=2)}

RESEARCH EVIDENCE:

{evidence_text}

SCORING:

ICP Fit:
0-25

Problem Fit:
0-25

Service Fit:
0-25

Buying Signals:
0-15

Evidence Quality:
0-10

Total:
100 maximum.

CLASSIFICATION:

80-100 = HIGH_POTENTIAL
60-79 = POTENTIAL
0-59 = NOT_QUALIFIED

Return exactly this JSON structure:

{{
    "icp_fit": 0,
    "problem_fit": 0,
    "service_fit": 0,
    "buying_signals": 0,
    "evidence_quality": 0,
    "total_score": 0,
    "status": "NOT_QUALIFIED",
    "reason": "",
    "evidence": [
        {{
            "claim": "",
            "source": "",
            "url": ""
        }}
    ]
}}
"""

    response = llm.invoke(
        prompt
    )

    raw = response.content

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        result = json.loads(
            raw
        )

    except json.JSONDecodeError:

        # Try extracting JSON from markdown fences
        cleaned = (
            raw
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

        result = json.loads(
            cleaned
        )

    # --------------------------------------------------------
    # Safety check score
    # --------------------------------------------------------

    calculated_score = (
        result["icp_fit"]
        + result["problem_fit"]
        + result["service_fit"]
        + result["buying_signals"]
        + result["evidence_quality"]
    )

    result["total_score"] = calculated_score

    # Recalculate classification ourselves
    # instead of blindly trusting the LLM.

    if calculated_score >= 80:

        result["status"] = (
            "HIGH_POTENTIAL"
        )

    elif calculated_score >= 60:

        result["status"] = (
            "POTENTIAL"
        )

    else:

        result["status"] = (
            "NOT_QUALIFIED"
        )

    return result