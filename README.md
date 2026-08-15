# AgentHack 2026 — Autonomous AI Sales Pipeline

An autonomous AI sales intelligence system built for AgentHack 2026.

The system is designed to take a company's knowledge base and an Ideal Customer Profile (ICP), discover potential leads, research and qualify them using evidence, recommend the most relevant service, identify an appropriate decision maker, and generate personalized outreach.

## Core Pipeline

Company Knowledge
↓
RAG
↓
ICP
↓
Lead Discovery
↓
Lead Filtering
↓
Deep Research
↓
Qualification & Scoring
↓
Service Matching
↓
Decision Maker Identification
↓
Personalized Outreach
↓
Pipeline & Memory

## Architecture

LangGraph is used as the main orchestration layer.

Individual tools and functions handle tasks such as:

- Company knowledge retrieval
- Lead discovery
- Web research
- Lead qualification
- Service matching
- Decision-maker identification
- Outreach generation
- Pipeline management

The system maintains shared state between stages and uses conditional decisions where appropriate.

## Current Development Stage

### Phase 1 — Knowledge / RAG

- [ ] PDF ingestion
- [ ] Document chunking
- [ ] Embeddings
- [ ] Chroma vector database
- [ ] Company knowledge retrieval
- [ ] Evidence metadata

### Phase 2 — Sales Pipeline

- [ ] ICP creation
- [ ] Lead discovery
- [ ] Lead filtering
- [ ] Deep research
- [ ] Qualification
- [ ] Service matching
- [ ] Decision maker identification
- [ ] Personalized outreach

### Phase 3 — Lifecycle

- [ ] Pipeline state
- [ ] SQLite memory
- [ ] Response classification
- [ ] Follow-up
- [ ] Meeting simulation

### Phase 4 — Optional Features

- [ ] WhatsApp integration
- [ ] Calendar integration
- [ ] Advanced UI
- [ ] Additional automation

## Technology

- Python
- LangChain
- LangGraph
- Groq
- ChromaDB
- Sentence Transformers
- SQLite
- Streamlit / web UI (planned)

## Development Strategy

The project follows an MVP-first approach.

The priority is a complete working sales pipeline rather than a large collection of disconnected features.

## Project Structure

```text
agenthack-2026/
│
├── data/
│   └── company knowledge
│
├── rag/
│   └── RAG implementation
│
├── app.py
├── agent.py
├── tools.py
├── requirements.txt
├── README.md
└── .gitignore