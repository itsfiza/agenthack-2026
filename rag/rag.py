import os
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.documents import Document


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "AgentHack_company_description.pdf"
)

CHROMA_PATH = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "nexaflow_company_knowledge"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

LLM_MODEL = "llama-3.3-70b-versatile"

TOP_K = 4


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# 1. LOAD PDF
# ============================================================

def load_company_pdf() -> List[Document]:
    """Load the company PDF."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Company PDF not found:\n{PDF_PATH}"
        )

    loader = PyPDFLoader(str(PDF_PATH))

    documents = loader.load()

    print(
        f"Loaded {len(documents)} pages "
        f"from company PDF."
    )

    return documents


# ============================================================
# 2. ADD METADATA
# ============================================================

def add_source_metadata(
    documents: List[Document],
) -> List[Document]:
    """
    Add metadata that will later support
    evidence and judge-mode explanations.
    """

    for document in documents:

        page = document.metadata.get(
            "page",
            0,
        )

        document.metadata.update(
            {
                "source": "NexaFlow company description",
                "source_type": "company_document",
                "authority": "official",
                "page_number": page + 1,
            }
        )

    return documents


# ============================================================
# 3. SPLIT DOCUMENT
# ============================================================

def split_documents(
    documents: List[Document],
) -> List[Document]:
    """Split PDF into retrieval-friendly chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Created {len(chunks)} document chunks."
    )

    return chunks


# ============================================================
# 4. CREATE EMBEDDINGS
# ============================================================

def create_embeddings() -> HuggingFaceEmbeddings:
    """Create local embedding model."""

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        },
    )


# ============================================================
# 5. BUILD VECTOR DATABASE
# ============================================================

def build_vector_database(
    chunks: List[Document],
) -> Chroma:
    """Create persistent Chroma vector database."""

    embeddings = create_embeddings()

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_PATH),
    )

    print(
        "Chroma vector database created."
    )

    return vector_store


# ============================================================
# 6. LOAD EXISTING VECTOR DATABASE
# ============================================================

def load_vector_database() -> Chroma:
    """Load existing Chroma database."""

    embeddings = create_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PATH),
    )

    return vector_store


# ============================================================
# 7. BUILD COMPLETE KNOWLEDGE BASE
# ============================================================

def build_knowledge_base() -> Chroma:
    """
    Complete ingestion pipeline:

    PDF
    ↓
    Documents
    ↓
    Metadata
    ↓
    Chunks
    ↓
    Embeddings
    ↓
    Chroma
    """

    print(
        "\n======================================"
    )

    print(
        "BUILDING NEXAFLOW KNOWLEDGE BASE"
    )

    print(
        "======================================\n"
    )

    documents = load_company_pdf()

    documents = add_source_metadata(
        documents
    )

    chunks = split_documents(
        documents
    )

    vector_store = build_vector_database(
        chunks
    )

    print(
        "\nKnowledge base ready."
    )

    return vector_store


# ============================================================
# 8. RETRIEVE EVIDENCE
# ============================================================

def retrieve_evidence(
    query: str,
    k: int = TOP_K,
) -> List[Document]:
    """
    Retrieve the most relevant company
    knowledge chunks.
    """

    vector_store = load_vector_database()

    results = vector_store.similarity_search(
        query,
        k=k,
    )

    return results


# ============================================================
# 9. FORMAT EVIDENCE
# ============================================================

def format_evidence(
    documents: List[Document],
) -> str:
    """
    Convert retrieved documents into
    structured evidence for the LLM.
    """

    evidence_blocks = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        metadata = document.metadata

        source = metadata.get(
            "source",
            "Unknown",
        )

        page = metadata.get(
            "page_number",
            "Unknown",
        )

        authority = metadata.get(
            "authority",
            "Unknown",
        )

        content = document.page_content.strip()

        evidence_blocks.append(
            f"""
[EVIDENCE {index}]
Source: {source}
Page: {page}
Authority: {authority}

Content:
{content}
"""
        )

    return "\n".join(
        evidence_blocks
    )


# ============================================================
# 10. GENERATE GROUNDED ANSWER
# ============================================================

def generate_answer(
    query: str,
    documents: List[Document],
) -> str:
    """
    Generate an answer using ONLY
    retrieved company evidence.
    """

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set."
        )

    evidence = format_evidence(
        documents
    )

    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=0,
        api_key=api_key,
    )

    prompt = f"""
You are the internal knowledge assistant
for NexaFlow.

Your job is to answer questions about
NexaFlow using ONLY the provided evidence.

STRICT RULES:

1. Never invent company information.
2. Never assume information that is not
   present in the evidence.
3. If the evidence is insufficient,
   explicitly say that there is not enough
   evidence.
4. Prefer official company information.
5. Keep answers concise and useful.
6. When possible, mention the source page.

USER QUESTION:
{query}

COMPANY EVIDENCE:
{evidence}

Answer:
"""

    response = llm.invoke(
        prompt
    )

    return response.content


# ============================================================
# 11. COMPLETE RAG QUERY
# ============================================================

def ask_company_knowledge(
    query: str,
    k: int = TOP_K,
) -> Dict[str, Any]:
    """
    Complete RAG operation.

    Query
      ↓
    Retrieval
      ↓
    Evidence
      ↓
    Grounded LLM answer
    """

    documents = retrieve_evidence(
        query,
        k=k,
    )

    answer = generate_answer(
        query,
        documents,
    )

    evidence = []

    for document in documents:

        evidence.append(
            {
                "content": document.page_content,
                "source": document.metadata.get(
                    "source"
                ),
                "page": document.metadata.get(
                    "page_number"
                ),
                "authority": document.metadata.get(
                    "authority"
                ),
            }
        )

    return {
        "query": query,
        "answer": answer,
        "evidence": evidence,
    }


# ============================================================
# 12. LANGGRAPH-READY COMPANY KNOWLEDGE TOOL
# ============================================================

def company_knowledge(
    query: str,
) -> str:
    """
    Simple interface that our LangGraph
    agent can call later.

    Input:
        query

    Output:
        grounded company answer
    """

    result = ask_company_knowledge(
        query
    )

    return result["answer"]


# ============================================================
# 13. LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "NexaFlow RAG module loaded."
    )

    print(
        f"PDF: {PDF_PATH}"
    )

    print(
        f"Chroma: {CHROMA_PATH}"
    )