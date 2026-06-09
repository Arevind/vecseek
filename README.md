# VecSeek

VecSeek is a self-hosted multi-workspace RAG platform for uploading files, indexing them into vectors, and serving retrieval-ready results through a UI or API.

## What It Does

- Create separate workspaces, each backed by its own Qdrant collection
- Upload PDF, DOCX, and TXT files with duplicate detection
- Extract text and tables, chunk them, and store both dense vectors and searchable chunk records
- Retrieve with hybrid search: dense vectors plus SQLite FTS keyword matching
- Inspect retrieval results with citations, explanations, and chunk lineage
- Tune chunking, candidate depth, hybrid search, reranking, and concurrency settings from the app
- Configure per-folder evaluations with Ollama or OpenAI
- Build folder-specific eval datasets for retrieval, answer quality, and red-team testing
- Track full evaluation run history with scores, failures, and run artifacts

## Current Runtime Design

- `frontend/`: Next.js dashboard for workspace management, retrieval testing, settings, and API reference
- `backend/`: FastAPI API for uploads, indexing, retrieval, settings, and diagnostics
- `Qdrant`: vector storage, now supporting both local mode and server mode
- `SQLite`: metadata store plus FTS-backed keyword retrieval over indexed chunks
- `Index queue`: bounded in-process job queue with worker concurrency controls

For development and small single-node installs, local Qdrant mode still works well. For production or higher concurrency, use Qdrant server mode.

## Retrieval Strategy

VecSeek now uses a hybrid retrieval pipeline:

1. Embed the query with the configured dense model
2. Search the workspace collection in Qdrant
3. Search the indexed chunk corpus with SQLite FTS
4. Merge dense and keyword candidates
5. Rerank with lightweight semantic + lexical heuristics
6. Return top results with metadata, citations, and explanations

The default embedding model remains `BAAI/bge-base-en-v1.5`, but the backend now uses an embedding abstraction so the model can be swapped later without changing the retrieval API.

## Environment Variables

Core backend:

- `BACKEND_HOST=0.0.0.0`
- `BACKEND_PORT=8080`
- `UPLOAD_DIR=/app/data/uploads`
- `SQLITE_PATH=/app/data/knowledgebase.db`
- `EMBEDDING_MODEL=BAAI/bge-base-en-v1.5`
- `DEFAULT_TOP_K=5`
- `MAX_TOP_K=20`
- `CHUNK_SIZE=1400`
- `CHUNK_OVERLAP=250`
- `VECTOR_CANDIDATE_LIMIT=32`
- `HYBRID_RETRIEVAL_ENABLED=true`
- `RERANKER_ENABLED=true`
- `RETRIEVAL_CONCURRENCY_LIMIT=12`
- `INDEXING_WORKER_CONCURRENCY=2`
- `RETRIEVAL_TIMEOUT_SECONDS=8`
- `EVAL_CONCURRENCY_LIMIT=1`
- `EVAL_TIMEOUT_SECONDS=45`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OPENAI_BASE_URL=https://api.openai.com/v1`
- `PROMPTFOO_COMMAND=npx promptfoo`

Qdrant:

- `QDRANT_MODE=local` or `server`
- `QDRANT_DIR=/app/data/qdrant`
- `QDRANT_URL=http://qdrant:6333`
- `QDRANT_API_KEY=...` optional
- `QDRANT_PREFER_GRPC=false`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8080`
- `NEXT_PUBLIC_KB_API_KEY=` optional for deployments that still want shared-key protection

## Quickstart

```bash
docker compose up -d --build
```

Open:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Health: [http://localhost:8080/health](http://localhost:8080/health)
- Diagnostics: [http://localhost:8080/health/diagnostics](http://localhost:8080/health/diagnostics)
- Docs: [http://localhost:8080/docs](http://localhost:8080/docs)

## API Highlights

- `GET /health`
- `GET /health/diagnostics`
- `POST /folders`
- `POST /folders/{folder_name}/upload`
- `POST /folders/{folder_name}/index`
- `GET /folders/{folder_name}/index/status`
- `POST /retrieve`
- `GET /settings`
- `PATCH /settings`
- `GET /eval/providers/ollama/models`
- `GET /folders/{folder_name}/evaluations/profile`
- `PATCH /folders/{folder_name}/evaluations/profile`
- `GET /folders/{folder_name}/evaluations/cases`
- `POST /folders/{folder_name}/evaluations/cases`
- `PATCH /folders/{folder_name}/evaluations/cases/{case_id}`
- `DELETE /folders/{folder_name}/evaluations/cases/{case_id}`
- `GET /folders/{folder_name}/evaluations/runs`
- `POST /folders/{folder_name}/evaluations/runs`
- `GET /folders/{folder_name}/evaluations/runs/{run_id}`

Example retrieval request:

```bash
curl -X POST "http://localhost:8080/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_name": "Health",
    "query": "How to check my BMI?",
    "top_k": 5
  }'
```

Example settings update:

```bash
curl -X PATCH "http://localhost:8080/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "default_top_k": 5,
    "chunk_size": 1400,
    "chunk_overlap": 250,
    "vector_candidate_limit": 32,
    "retrieval_concurrency_limit": 12,
    "indexing_worker_concurrency": 2,
    "hybrid_retrieval_enabled": true,
    "reranker_enabled": true
  }'
```

## Benchmarking

A small benchmark helper is included:

```bash
python backend/benchmarks/benchmark_retrieval.py \
  --base-url http://localhost:8080 \
  --folder Health \
  --query "How to check my BMI?" \
  --runs 20
```

## Sample Data

Use the included sample corpus in [sample_data/payments-faq.txt](C:/Users/arevi/OneDrive/Desktop/knowledgebase-creator/sample_data/payments-faq.txt) for quick smoke testing.

## Recommended Production Direction

- Run Qdrant in server mode instead of embedded local mode
- Keep indexing backgrounded and bounded so retrieval stays responsive
- Use diagnostics to watch queue depth, active retrievals, and average vector/query timings
- Move metadata storage from SQLite to Postgres once write contention becomes meaningful

## Open-Source Roadmap

- OCR for scanned PDFs
- richer rerankers
- metadata filters in retrieval
- import/export and backup
- optional auth/token flows for public deployments
- richer benchmark datasets and evaluation scripts
