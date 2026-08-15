import os
from pathlib import Path
from typing import List

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

PDF_PATH = PROJECT_ROOT / "data" / "AgentHack_company_description.pdf"

CHROMA_PATH = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "nexaflow_company_knowledge"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

LLM_MODEL = "llama-3.3-70b-versatile"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# 1. LOAD COMPANY PDF
# ============================================================

def load_company_pdf() -> List[Document]:
    """Load the NexaFlow company PDF."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Company PDF not found at: {PDF_PATH}"
        )

    loader = PyPDFLoader(str(PDF_PATH))

    documents = loader.load()

    print(f"Loaded {len(documents)} pages from company PDF.")

    return documents


# ============================================================
# 2. ADD SOURCE METADATA
# ============================================================

def add_source_metadata(
    documents: List[Document],
) -> List[Document]:
    """Add metadata to every document."""

    for document in documents:

        page_number = document.metadata.get("page", 0)

        document.metadata["source"] = (
            "NexaFlow company description"
        )

        document.metadata["source_type"] = (
            "company_document"
        )

        document.metadata["authority"] = "official"

        document.metadata["page_number"] = (
            page_number + 1
        )

    return documents


# ============================================================
# 3. SPLIT DOCUMENTS
# ============================================================

def split_documents(
    documents: List[Document],
) -> List[Document]:
    """Split documents into retrieval chunks."""

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

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks.")

    return chunks


# ============================================================
# 4. CREATE EMBEDDINGS
# ============================================================

def create_embeddings() -> HuggingFaceEmbeddings:
    """Create the embedding model."""

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        },
    )

    return embeddings


# ============================================================
# 5. BUILD CHROMA DATABASE
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
        f"Chroma database created at: {CHROMA_PATH}"
    )

    return vector_store


# ============================================================
# 6. LOAD EXISTING CHROMA DATABASE
# ============================================================

def load_vector_database() -> Chroma:
    """Load an existing Chroma database."""

    if not CHROMA_PATH.exists():
        raise FileNotFoundError(
            "Chroma database does not exist yet. "
            "Run build_knowledge_base() first."
        )

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
    """Build the complete PDF → Chroma pipeline."""

    print("\n==============================")
    print("BUILDING NEXAFLOW KNOWLEDGE BASE")
    print("==============================\n")

    documents = load_company_pdf()

    documents = add_source_metadata(documents)

    chunks = split_documents(documents)

    vector_store = build_vector_database(chunks)

    print("\nKnowledge base ready.")

    return vector_store


# ============================================================
# 8. RETRIEVE EVIDENCE
# ============================================================

def retrieve_evidence(
    query: str,
    k: int = 4,
):
    """Retrieve relevant company-document chunks."""

    vector_store = load_vector_database()

    results = vector_store.similarity_search(
        query,
        k=k,
    )

    return results


# ============================================================
# 9. DISPLAY EVIDENCE
# ============================================================

def display_evidence(
    results: List[Document],
):
    """Display retrieved evidence and metadata."""

    print("\n==============================")
    print("RETRIEVED EVIDENCE")
    print("==============================\n")

    for index, document in enumerate(
        results,
        start=1,
    ):

        metadata = document.metadata

        print(f"--- Evidence {index} ---")

        print(
            f"Source: "
            f"{metadata.get('source', 'Unknown')}"
        )

        print(
            f"Page: "
            f"{metadata.get('page_number', 'Unknown')}"
        )

        print(
            f"Authority: "
            f"{metadata.get('authority', 'Unknown')}"
        )

        print("\nContent:")

        print(
            document.page_content[:1500]
        )

        print()


# ============================================================
# 10. GENERATE GROUNDED ANSWER
# ============================================================

def generate_answer(
    query: str,
    results: List[Document],
) -> str:
    """Generate answer using retrieved evidence only."""

    if not os.getenv("GROQ_API_KEY"):
        raise EnvironmentError(
            "GROQ_API_KEY is not set."
        )

    llm = ChatGroq(
        model=LLM_MODEL,
        temperature=0,
    )

    evidence_blocks = []

    for index, document in enumerate(
        results,
        start=1,
    ):

        page = document.metadata.get(
            "page_number",
            "Unknown",
        )

        content = document.page_content

        evidence_blocks.append(
            f"[Evidence {index} | Page {page}]\n"
            f"{content}"
        )

    evidence = "\n\n".join(
        evidence_blocks
    )

    prompt = f"""
You are NexaFlow's internal company knowledge assistant.

Answer the user's question using ONLY the evidence
provided below.

Do NOT invent facts.

If the evidence does not contain enough information,
say:

"I don't have enough evidence in the company knowledge base
to answer that."

USER QUESTION:
{query}

EVIDENCE:
{evidence}

Answer clearly and concisely.
"""

    response = llm.invoke(prompt)

    return response.content


# ============================================================
# 11. COMPLETE RAG QUERY
# ============================================================

def ask_company_knowledge(
    query: str,
    k: int = 4,
):
    """
    Complete RAG operation:

    Query
    ↓
    Retrieve evidence
    ↓
    Generate grounded answer
    """

    results = retrieve_evidence(
        query=query,
        k=k,
    )

    answer = generate_answer(
        query=query,
        results=results,
    )

    return {
        "query": query,
        "answer": answer,
        "evidence": results,
    }


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("NexaFlow RAG module loaded.")

    print(f"PDF: {PDF_PATH}")

    print(f"Chroma: {CHROMA_PATH}")