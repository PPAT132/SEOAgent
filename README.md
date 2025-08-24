# SEO Agent

A comprehensive SEO analysis and optimization tool with AI-powered recommendations.

## Architecture

- **Frontend**: React app (`seo-agent-demo/`)
- **Backend**: FastAPI with PyTorch (`backend/`) - **Dockerized**
- **Lighthouse Service**: Node.js service (`lighthouse-service/`)

## Quick Start

### 1. Start Backend (Docker)

```bash
# Start backend with all dependencies (PyTorch, transformers, etc.)
./start-backend.sh
```

### 2. Start Lighthouse Service

```bash
cd lighthouse-service
npm install
node server.js
```

### 3. Start Frontend

```bash
cd seo-agent-demo
npm install
npm run dev
```

## Services

- **Backend API**: http://localhost:3001
- **Lighthouse Service**: http://localhost:3002
- **Frontend**: http://localhost:5173

## Development

### Backend (Docker)

```bash
cd backend
docker-compose up --build
```

### Lighthouse Service (Local)

```bash
cd lighthouse-service
node server.js
```

### Frontend (Local)

```bash
cd seo-agent-demo
npm run dev
```

## Testing

Run the full pipeline test:

```bash
cd backend/tests
python test_full_pipeline.py
```

## Docker Commands

```bash
# View backend logs
docker-compose logs -f

# Stop backend
docker-compose down

# Rebuild backend
docker-compose up --build
```
