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

    for i, item in enumerate(evidence, start=1):

        formatted.append(
            f"""
--- EVIDENCE {i} ---

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Content:
{item.get("content", "")[:1800]}
"""
        )

    return "\n".join(formatted)


# ============================================================
# EXTRACT JSON SAFELY
# ============================================================

def extract_json(text: str) -> Dict[str, Any]:

    if not text:
        raise ValueError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # Remove markdown fences if present
    if "```json" in text:

        text = text.replace(
            "```json",
            ""
        )

    if "```" in text:

        text = text.replace(
            "```",
            ""
        )

    text = text.strip()

    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            f"LLM response did not contain JSON.\n\n"
            f"RAW RESPONSE:\n{text}"
        )

    json_text = text[start:end + 1]

    try:

        return json.loads(
            json_text
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            f"Invalid JSON returned by LLM.\n\n"
            f"JSON ATTEMPT:\n{json_text}\n\n"
            f"RAW RESPONSE:\n{text}\n\n"
            f"ERROR:\n{e}"
        )


# ============================================================
# QUALIFY LEAD
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

Evaluate ONE potential prospect for NexaFlow AI.

IMPORTANT RULES:

- Use ONLY the supplied ICP, company information,
  and research evidence.
- NEVER invent facts.
- If evidence is insufficient, reduce the score.
- A blog article or directory listing is NOT automatically
  proof that the named entity is a target company.
- Do not treat a search-result title as proof.
- Explain the qualification using evidence.
- Return ONLY a JSON object.
- Do not use markdown.
- Do not write anything before or after the JSON.

NEXAFLOW SERVICES:

1. Web AI Chatbot
2. WhatsApp AI Assistant
3. Workflow Automation
4. AI Voice Agent
5. Knowledge Assistant
6. Sales Automation

ICP:

{json.dumps(icp, indent=2)}

COMPANY:

{json.dumps(company, indent=2)}

RESEARCH EVIDENCE:

{evidence_text}

SCORING:

ICP Fit: 0-25
Problem Fit: 0-25
Service Fit: 0-25
Buying Signals: 0-15
Evidence Quality: 0-10

Total must equal the sum of the five scores.

CLASSIFICATION:

80-100 = HIGH_POTENTIAL
60-79 = POTENTIAL
0-59 = NOT_QUALIFIED

Return EXACTLY:

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

    # --------------------------------------------------------
    # Call LLM
    # --------------------------------------------------------

    response = llm.invoke(
        prompt
    )

    # LangChain normally returns this as a string,
    # but handle unusual responses safely.

    raw = response.content

    if isinstance(raw, list):

        raw = "".join(
            str(part)
            for part in raw
        )

    raw = str(raw).strip()

    print("\n" + "=" * 60)
    print("LLM QUALIFICATION RESPONSE")
    print("=" * 60)
    print(raw)
    print("=" * 60)

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    result = extract_json(
        raw
    )

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    required_fields = [
        "icp_fit",
        "problem_fit",
        "service_fit",
        "buying_signals",
        "evidence_quality",
        "reason",
        "evidence",
    ]

    for field in required_fields:

        if field not in result:

            raise ValueError(
                f"Qualification response is missing "
                f"required field: {field}"
            )

    # --------------------------------------------------------
    # Calculate score ourselves
    # --------------------------------------------------------

    calculated_score = (
        int(result["icp_fit"])
        + int(result["problem_fit"])
        + int(result["service_fit"])
        + int(result["buying_signals"])
        + int(result["evidence_quality"])
    )

    result["total_score"] = calculated_score

    # --------------------------------------------------------
    # Classification ourselves
    # --------------------------------------------------------

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