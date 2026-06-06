# Knowledgebase Studio

Knowledgebase Studio is a workspace-based document indexing and retrieval platform built with FastAPI, Qdrant, SQLite, and Next.js. Each workspace folder represents one knowledgebase, stores its raw files on disk, indexes cleaned content into one Qdrant collection, and exposes a retrieval API for internal tools and services.

## Features

- Create unique folders/workspaces with case-insensitive name protection
- Upload PDF, DOCX, and TXT files into a folder
- Detect duplicate files inside a folder using SHA-256 hashes
- Extract PDF text and tables, DOCX paragraphs and tables, and TXT content
- Convert tables into row-wise key-value records before chunking
- Chunk processed content and store vectors in Qdrant using `BAAI/bge-base-en-v1.5`
- Re-index folders cleanly so stale chunks from deleted or old files are removed
- Retrieve relevant chunks by folder name through the UI or `POST /retrieve`
- Update only `default_top_k` from the settings screen
- Run locally or on a cloud VM with Docker Compose

## Architecture

- `frontend/`: Next.js App Router UI using TypeScript, Tailwind CSS, Radix-based shadcn-style components, and TanStack Query
- `backend/`: FastAPI API with SQLAlchemy metadata storage, Qdrant vector storage, and document preprocessing services
- `data/uploads`: raw files grouped by folder slug
- `data/qdrant`: shared persistent Qdrant directory
- `data/sqlite`: SQLite database directory

Each folder maps to one Qdrant collection inside the shared persistent Qdrant directory. The backend stores folder metadata in SQLite and chunk metadata in Qdrant. Retrieval uses the same embedding model for indexing and querying.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, TanStack Query, Axios
- Backend: FastAPI, Python, Pydantic, SQLAlchemy, SQLite
- Vector store: Qdrant local persistent client
- Embeddings: Sentence Transformers `BAAI/bge-base-en-v1.5`
- Parsing: `pypdf`, `pdfplumber`, `python-docx`
- Deployment: Docker, Docker Compose, Gunicorn, Uvicorn

## Folder Structure

```text
.
├── backend
│   ├── app
│   │   ├── api
│   │   ├── services
│   │   │   └── preprocessing
│   │   └── utils
│   ├── tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend
│   ├── app
│   ├── components
│   ├── lib
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Environment Variables

Backend:

- `BACKEND_HOST=0.0.0.0`
- `BACKEND_PORT=8000`
- `KB_API_KEY=change-this-secret`
- `CORS_ORIGINS=["http://localhost:3000","http://SERVER_IP:3000"]`
- `UPLOAD_DIR=/app/data/uploads`
- `QDRANT_DIR=/app/data/qdrant`
- `SQLITE_PATH=/app/data/knowledgebase.db`
- `EMBEDDING_MODEL=BAAI/bge-base-en-v1.5`
- `DEFAULT_TOP_K=5`
- `MAX_TOP_K=20`
- `CHUNK_SIZE=700`
- `CHUNK_OVERLAP=100`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- `NEXT_PUBLIC_KB_API_KEY=change-this-secret`

## Local Development

1. Copy `.env.example` to `.env`.
2. Review `KB_API_KEY`, CORS origins, and frontend base URL values.
3. Start the stack:

```bash
docker compose up -d --build
```

4. Open:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Docker Compose and Cloud Background Service

Run in the background:

```bash
docker compose up -d --build
```

Check logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Stop:

```bash
docker compose down
```

Cloud access examples:

- Retrieval API: `http://SERVER_IP:8000/retrieve`
- Frontend: `http://SERVER_IP:3000`

The backend binds to `0.0.0.0` through Gunicorn/Uvicorn, so team members can access it from their own machines when the server port is exposed.

## API Overview

### Health

- `GET /health`

Response:

```json
{
  "status": "ok",
  "service": "Knowledgebase Studio"
}
```

### Folders

- `POST /folders`
- `GET /folders`
- `GET /folders/{folder_name}`
- `DELETE /folders/{folder_name}`

### Documents

- `POST /folders/{folder_name}/upload`
- `GET /folders/{folder_name}/documents`
- `DELETE /folders/{folder_name}/documents/{document_id}`

### Indexing

- `POST /folders/{folder_name}/index`
- `GET /folders/{folder_name}/index/status`

### Retrieval

- `POST /retrieve`

Example curl:

```bash
curl -X POST "http://SERVER_IP:8000/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_name": "Aadhaar SOP Docs",
    "query": "What are the documents required?",
    "top_k": 5
  }'
```

### Settings

- `GET /settings`
- `PATCH /settings`

## Preprocessing and Table Handling

- PDF:
  - Extracts page text using `pypdf`
  - Extracts tables using `pdfplumber`
  - Preserves page number metadata
- DOCX:
  - Extracts paragraph text
  - Extracts tables separately
  - Uses first row as headers when possible
  - Falls back to `Column 1`, `Column 2`, and so on when headers are missing or duplicated
- TXT:
  - Reads with UTF-8 first and falls back gracefully

Tables are converted into row-wise key-value text records before chunking. Empty cells become `N/A`, which keeps the semantic structure useful during retrieval.

## Qdrant Collection Strategy

- One persistent Qdrant directory for the whole application
- One collection per folder using a slug-derived collection name
- Re-indexing recreates the collection so stale chunks are fully removed
- Chunk metadata includes folder, collection, file, content type, page, table, row, and chunk index details

## Edge Cases Handled

- Duplicate folder names
- Empty folder names
- Unsupported file types
- Duplicate file uploads inside the same folder
- Empty files
- Empty extracted document output
- Retrieval before indexing
- Invalid or missing API key on protected endpoints
- `top_k` above the configured maximum
- Re-index after file deletion or new uploads

## Testing

Minimal backend tests are included for:

- health endpoint
- folder creation and duplicate rejection
- settings validation
- API key enforcement
- unsupported upload rejection
- table record conversion fallback behavior

Suggested end-to-end checklist:

1. `docker compose up -d --build`
2. Create `Aadhaar SOP Docs`
3. Upload PDF, DOCX, and TXT files
4. Re-upload the same file and confirm duplicate warning
5. Run indexing and confirm folder status becomes `indexed`
6. Add or delete a file and confirm status becomes `needs_reindex`
7. Re-index and verify retrieval returns updated chunks only
8. Change `default_top_k` in Settings and test retrieval without passing `top_k`

## Future Improvements

- Background indexing with Celery or RQ
- User authentication
- Role-based API keys
- OCR for scanned PDFs
- Hybrid search with BM25 plus vector search
- Reranking model
- Document versioning
- Multi-user workspaces
- Cloud object storage
- Streaming indexing status via WebSocket
