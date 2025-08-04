# SEO Agent (step 1)

A minimal full‑stack prototype that demonstrates how an AI agent can automatically generate SEO‑focused HTML patches inside a developer’s normal workflow. It consists of a **React 18 + Vite + Tailwind** front‑end and a **FastAPI** back‑end that calls **Gemini 2 Flash‑Lite** (or any LLM you wire) to build unified diffs fixing missing `<title>`, `<meta description>`, Open Graph tags, and other on‑page SEO issues.

---

## Features

| Area       | Highlights                                                                                                                                                                                               |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Front‑end  | ✨ Two‑pane editor (raw HTML ➜ diff) with animated Framer‑Motion transitions and gradient theme.✨ Single‑page build (vite) hot‑reloads in dev mode.                                                     |
| Back‑end   | ⚡ `POST /optimize` takes raw HTML, detects missing metadata, builds an LLM prompt, generates a patch with `difflib.unified_diff`, re‑parses & validates, and returns JSON `{ diff: "<unified‑diff>" }`. |
| Dev UX     | 🪄 "Generate Patch" button shows an artificial delay so you can wire the API later; "Apply & Download" is stubbed for future diff export.                                                                |
| Extensible | Road‑map includes VS Code extension, local vector indexer, Lighthouse‑CI check loop, and multi‑model support (OpenAI, Claude, etc.).                                                                     |

---

## Architecture

```
┌──────────────┐        raw HTML       ┌──────────────────────┐
│  React UI    │  ───────────────▶   │  FastAPI /optimize   │
│ (Vite + TS)  │        diff          │  LLM Caller + Patch   │
└──────────────┘  ◀───────────────   │  Generator + Validator│
        ▲ dev/build                └──────────────────────┘
        │                                     ▲
        └────────── localhost:5173 ◀──────────┘
```

---

## Prerequisites

| Tool                  | Version                 |
| --------------------- | ----------------------- |
| **Node.js**           | ≥ 18 LTS                |
| **npm / bun**         | latest                  |
| **Python**            | ≥ 3.10                  |
| **FastAPI & Uvicorn** | installed via pip       |
| **Gemini API Key**    | export `GEMINI_API_KEY` |

---

## Getting Started

1. **Clone the repo**

   ```bash
   git clone https://github.com/PPAT132/SEOAgent.git
   cd SEOAgent
   ```

2. **Back‑end (FastAPI)**

   ```bash
   python -m venv venv && source venv/bin/activate
   pip install fastapi "uvicorn[standard]" beautifulsoup4 difflib google‑generativeai
   export GEMINI_API_KEY=<your‑key>
   uvicorn api:app --reload
   # backend on http://localhost:8000
   ```

3. **Front‑end (React + Vite)**

   ```bash
   cd seo-agent-demo
   npm install
   npm run dev  # opens http://localhost:5173
   ```

4. **Workflow**

   1. Paste HTML into the left pane.
   2. Click **Generate Patch** – diff appears on the right.
   3. (Soon) Click **Apply & Download** to save a .patch file.

---

## License
