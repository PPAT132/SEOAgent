# Current Goal

Build the end‑to‑end pipeline on top of the existing `POST /optimizev1` endpoint (no new optimize routes). Add Lighthouse summary endpoints and the necessary services/core utilities to:

1. extract SEO issues with locations,
2. optionally attach HTML fragments,
3. orchestrate LLM‑driven modifications (Patch Plan first, full HTML as fallback), and
4. return a unified diff to the frontend.

---

# Levels (Execution Plan)

**Rules**

- Levels reflect dependency stages. All tasks in the same level can run in parallel.
- You must finish every task in Level N before starting Level N+1.
- We keep `/optimizev1` as the only optimize endpoint and evolve its implementation internally.

### Level 1 — Skeletons (parallel)

- **Models**: add skeletons in `app/models/seo.py`.
- **Routes**: extend `app/api/routes.py` with:

  - `POST /lighthouse/summary` (placeholder)
  - `POST /lighthouse/summary-with-html` (placeholder)
  - (Keep existing `POST /optimizev1`)

- **Service stubs**:

  - `app/services/lighthouse_summary_service.py` (extract_summary, attach_html_fragments)
  - `app/services/page_intent_service.py` (build_page_intent)
  - `app/services/optimization_v1.py` (adapter for `/optimizev1`, calls core agent)

- **Core stubs**:

  - `app/core/prompt_builder.py` (build_prompt)
  - `app/core/diff_tool.py` (to_unified_diff, validate_unified_diff)
  - `app/core/agent.py` (optimize)
  - **NEW** `app/core/patch_plan.py` (Patch Plan schema/types only, no logic)
  - **NEW** `app/core/patch_applier.py` (apply_plan placeholder; does nothing yet)
  - `app/core/llm_tool.py` (already present or skeleton)

- **Utils stubs**:

  - `app/utils/selectors.py` (find_by_selector, find_by_path, find_by_snippet, extract_context)
  - `app/utils/text.py` (clean/strip/truncate/detect_lang)

- **Config**: update `app/config.py` with placeholders:

  - `SEO_AGENT_LANG`, `MAX_LOCATIONS_PER_ISSUE`, `LLM_MODEL`, `TIMEOUTS`, `SAFE_CSS_TOGGLE`

- **Frontend**:

  - API wrappers for the two Lighthouse endpoints and `/optimizev1`
  - Minimal UI hooks: IssuesPanel (static), diff display (static)

- **Tests**:

  - Minimal files: `test_lighthouse_summary_service.py`, `test_selectors.py` (structure only)

**Acceptance (L1)**: App starts; endpoints exist and return placeholders; frontend calls succeed and render placeholder results.

---

### Level 2 — Summary & Display

- **lighthouse_summary_service.extract_summary(lhr)**:

  - Pull `seoScore` (support both `result.seoScore` and `categories.seo.score`).
  - Produce a trimmed SEO‑focused `issues[]` list; include `locations[]` with `selector/path/snippet` if available (no fragments yet).

- **page_intent_service.build_page_intent(html)**:

  - Minimal fields: `title`, `h1`, `lang`, `canonical`, `og:{title,description,type}`.

- **routes.py**:

  - Wire `/lighthouse/summary` to `extract_summary`.
  - `/lighthouse/summary-with-html` returns the same structure (outerHTML/context empty for now).

- **selectors.find_by_selector**:

  - Minimal: return first match and `outerHTML`.
  - `extract_context`: return a small window of nearby text.

- **Frontend**:

  - IssuesPanel renders real issues; display first location’s raw metadata (no outerHTML yet).

**Acceptance (L2)**: Frontend renders real seoScore + issues; page intent is extracted; API returns stable summary shapes.

---

### Level 3 — Closed Loop (placeholder diff) **+ Patch Plan protocol**

- **Prompt rules** in `core/prompt_builder.py`:

  - Guardrails: _only modify specified nodes or head meta/link_, safe CSS override toggle (Tier‑1: scoped, minimal CSS), no script removal, unified diff required.
  - **Instruct LLM to output a Patch Plan JSON first**; accept full HTML as fallback.

- **Patch Plan schema** in `core/patch_plan.py`:

  - `operations[]` with types (no logic yet):

    - `upsertTitle(text)`
    - `upsertMetaName(name, content)`
    - `upsertMetaProperty(property, content)`
    - `upsertLinkRel(rel, href[, hreflang])`
    - `replaceAttr(selector, name, value)` (e.g., `img[alt]`)
    - `insertStyleScoped(selector, cssRules)` (Tier‑1 layout fixes)

  - Each op references an **auditId** and **NodeRef** (selector | path | snippet | fingerprint | confidence).

- **agent.optimize (placeholder)**:

  - Build prompt from `summary + page_intent`.
  - For now, synthesize a small Patch Plan locally (no real LLM yet), apply it to the original HTML (trivial/no‑op), and output a **placeholder diff** via `diff_tool.to_unified_diff`.

- **optimization_v1.py**:

  - Refactor to call `agent.optimize` and return `{ diff }` under the same `/optimizev1` contract.

**Acceptance (L3)**: `/optimizev1` returns a realistic placeholder diff produced by the agent (closed loop demonstrated).

---

### Level 4 — HTML Targeting Enhancements

- **selectors**:

  - Implement `find_by_path` (DOM index path) and `find_by_snippet` (fuzzy match) with a `confidence` score.
  - Add a small `fingerprint` helper (tag/class chain + neighbor text hash) used only when selector/path fail.

- **lighthouse_summary_service.attach_html_fragments(summary, html)**:

  - Fill `outerHTML/context/confidence` using **priority: selector > path > snippet+fingerprint**.
  - Limit to `MAX_LOCATIONS_PER_ISSUE`.

- **routes**:

  - `/lighthouse/summary-with-html` now returns enriched fragments.

- **Frontend**:

  - IssuesPanel shows the first resolved `outerHTML` (if any) and confidence.

**Acceptance (L4)**: Most actionable issues map back to concrete HTML fragments with confidence; frontend displays the first hit.

---

### Level 5 — Real Model & Diff Tooling

- **llm_tool.complete**:

  - Wire real model (Gemini 2 Flash‑Lite; can hot switch to GPT‑4o‑mini/Claude Haiku).

- **agent.optimize**:

  - Call LLM; **prefer Patch Plan** output. If model returns full HTML, parse as fallback.
  - Add a minimal **Plan validator** (reject dangerous ops; enforce Tier‑1 CSS).

- **patch_applier.apply_plan**:

  - Implement **idempotent upsert/replace** with stable ordering inside `<head>`:

    1. meta charset → 2) meta viewport → 3) other meta (name/property sorted) → 4) title → 5) link canonical/alternate → 6) `<style data-seo-agent>`

  - Use unique keys:

    - meta\[name], meta\[property], link\[rel] (+ hreflang), title (single)

  - Attach `data-seo-agent="v1"` on any new/modified node.

- **diff_tool**:

  - Implement real unified diff (normalize newlines/whitespace to reduce noise).
  - Add `validate_unified_diff` minimal checks (can apply, not empty).

**Acceptance (L5)**: With real LLM enabled, `/optimizev1` returns an apply‑ready, validated unified diff based on Patch Plan.

---

### Level 6 — Light Validation & Response Enrichment

- **validator_service.quick_check(html, issues)**:

  - Verify presence/format for: title, meta description, robots, canonical, hreflang, img alt (counts fixed).

- **/optimizev1**:

  - Non‑blocking: return `{ diff, quick_check }` (backward compatible; `quick_check` optional).

- **Optional**: include `htmlHash` in `SummaryOut` and `OptimizeIn` to warn if HTML changed between summary and optimize.

**Acceptance (L6)**: Response includes quick checks; repeated runs remain idempotent; manualFix items (if any) are listed.

---

### Level 7 — Hardening & Tests

- Expand tests:

  - Summary extraction fidelity, selector/path/snippet targeting, Patch Plan idempotency, safe CSS guardrails, diff stability.

- Add timeouts/retries for LLM and external Lighthouse calls.
- Update dependencies (`beautifulsoup4`, etc.) and README (how to run, DEV_MODE for summary endpoints).

**Acceptance (L7)**: Test suite passes; docs updated; timeouts/retries in place.

---

# File‑by‑File Responsibilities (What each file is for)

> Format: **Purpose** / **Inputs** / **Outputs** / **Used by**

### API

**`app/api/routes.py`**

- **Purpose**: Single FastAPI router exposing all endpoints.
- **Inputs**: Request bodies for `/optimizev1`, `/lighthouse/summary`, `/lighthouse/summary-with-html`.
- **Outputs**: `{ diff }` (and later `{ diff, quick_check? }`) for optimize; `SummaryOut` for summary endpoints.
- **Used by**: Frontend.

### Models

**`app/models/seo.py`**

- **Purpose**: Pydantic models for request/response contracts.
- **Inputs**: n/a (definitions).
- **Outputs**:

  - `LighthouseSummaryIn { lhr: dict, html?: str }`
  - `PageIntent { title?, h1?, subheads?, summary?, canonical?, og?, lang? }`
  - `IssueLocation { selector?, path?, snippet?, outerHTML?, context?, confidence? }`
  - `Issue { id, title, description?, score?, locations: IssueLocation[], needsGlobalAnalysis?, suggestAction? }`
  - `SummaryOut { seoScore: int, pageIntent?, issues: Issue[] }`
  - `OptimizeIn { html: str, summary: SummaryOut }`
  - `OptimizeOut { diff: str, quick_check?: object }`
  - _(Optional internal)_ `htmlHash?: string`

- **Used by**: API, services, core.

### Services

**`app/services/optimization_v1.py`**

- **Purpose**: Adapter for `/optimizev1`; orchestrates the optimize flow by calling the core agent.
- **Inputs**: HTML (and optionally SummaryOut if your contract later includes it).
- **Outputs**: `{ diff }` (later `{ diff, quick_check }`).
- **Used by**: `routes.py`.

**`app/services/lighthouse_service.py`** _(existing)_

- **Purpose**: Talk to external Lighthouse microservice (URL or raw HTML audit).
- **Inputs**: URL or HTML.
- **Outputs**: Raw Lighthouse report (LHR).
- **Used by**: validator, summary service, diagnostics.

**`app/services/lighthouse_summary_service.py`**

- **Purpose**: Convert LHR to SEO‑focused `SummaryOut`; attach HTML fragments.
- **Inputs**: LHR, raw HTML (optional for fragments).
- **Outputs**: `SummaryOut` (with or without fragments).
- **Used by**: `routes.py` (summary endpoints), `prompt_builder`, `agent`.

**`app/services/page_intent_service.py`**

- **Purpose**: Extract minimal page semantics for prompt context.
- **Inputs**: raw HTML.
- **Outputs**: `PageIntent`.
- **Used by**: `agent`, `prompt_builder`.

**`app/services/validator_service.py`** _(extend)_

- **Purpose**: Quick local checks after patch application.
- **Inputs**: modified HTML, `issues`.
- **Outputs**: `quick_check` object (e.g., `{ meta_ok, alt_fixed, ... }`).
- **Used by**: `/optimizev1` response enrichment.

### Core

**`app/core/llm_tool.py`**

- **Purpose**: LLM integration wrapper.
- **Inputs**: prompt string.
- **Outputs**: model raw output (Patch Plan JSON preferred; full HTML as fallback).
- **Used by**: `agent`.

**`app/core/prompt_builder.py`**

- **Purpose**: Build guarded prompts using `SummaryOut + PageIntent`.
- **Inputs**: summary, page intent, strategy flags (e.g., `SAFE_CSS_TOGGLE`).
- **Outputs**: prompt string.
- **Used by**: `agent`.

**`app/core/patch_plan.py`** _(NEW)_

- **Purpose**: Define the Patch Plan schema/types and NodeRef shape.
- **Inputs**: none (type definitions).
- **Outputs**:

  - `Plan { operations: PlanOp[] }`
  - `PlanOp` union: `upsertTitle`, `upsertMetaName`, `upsertMetaProperty`, `upsertLinkRel`, `replaceAttr`, `insertStyleScoped`
  - `NodeRef { selector?, path?, snippet?, fingerprint?, confidence? }`, `auditId`, `reason`.

- **Used by**: `agent`, `patch_applier`.

**`app/core/patch_applier.py`** _(NEW)_

- **Purpose**: Apply a Patch Plan to the original HTML (idempotent upserts, safe CSS Tier‑1).
- **Inputs**: original HTML, `Plan`.
- **Outputs**: modified HTML (and `manualFix[]` if operations were skipped/unsafe).
- **Used by**: `agent`, `diff_tool`.

**`app/core/diff_tool.py`**

- **Purpose**: Generate/validate unified diffs with normalized whitespace to minimize noise.
- **Inputs**: original and modified HTML.
- **Outputs**: diff string; `validate_unified_diff` boolean.
- **Used by**: `agent`, `optimization_v1`.

**`app/core/agent.py`**

- **Purpose**: Orchestrate end‑to‑end optimize flow for `/optimizev1`.
- **Inputs**: original HTML, `SummaryOut`.
- **Outputs**: unified diff (and optional `quick_check`).
- **Flow**: page_intent → prompt → LLM → **Patch Plan preferred** → patch_applier → diff_tool → quick_check.

### Utilities

**`app/utils/selectors.py`**

- **Purpose**: Robust DOM targeting and local context extraction.
- **Inputs**: HTML, targeting info (`selector`, `path`, `snippet`).
- **Outputs**: `{ outerHTML, confidence, context }` when resolvable.
- **Used by**: `lighthouse_summary_service.attach_html_fragments`, `patch_applier` (when resolving NodeRef).

**`app/utils/text.py`**

- **Purpose**: Text normalization utilities for clean prompts and summaries.
- **Inputs**: strings/HTML.
- **Outputs**: cleaned strings, truncations, language detection fallback.
- **Used by**: page intent, prompt building.

### Configuration

**`app/config.py`**

- **Purpose**: Central runtime config.
- **Keys**: `SEO_AGENT_LANG`, `MAX_LOCATIONS_PER_ISSUE`, `LLM_MODEL`, `TIMEOUTS`, `SAFE_CSS_TOGGLE`, `DEV_MODE` (optional for summary endpoints).
- **Used by**: services/core.

---

# Design Conventions (baked into implementation, no new routes)

1. **Plan‑first, HTML‑fallback**

   - LLM is asked to output a **Patch Plan JSON**; if it returns full HTML, we parse it as a fallback.
   - This enables precise **insert vs replace** and keeps changes idempotent and traceable.

2. **NodeRef (target address) priority**

   - Resolve in order: **selector > path > snippet+fingerprint**, with a `confidence` score.
   - Low‑confidence targets are either skipped or flagged as `manualFix`.

3. **Idempotent upsert & stable ordering**

   - Unique keys: `meta[name]`, `meta[property]`, `link[rel] (+hreflang)`, single `title`.
   - Stable order in `<head>` to keep diffs deterministic.
   - All agent changes tagged `data-seo-agent="v1"` for easy rollback.

4. **Safe CSS (Tier‑1) only**

   - Minimal, scoped overrides (`font-size`, `min-height`, `padding`, `line-height`) under a dedicated `<style data-seo-agent>`; optional `@media` guard; avoid `!important` unless whitelisted.

5. **Quick checks & manualFix**

   - Non‑blocking validation returns `quick_check` and a `manualFix[]` list for unresolved/unsafe operations.

---

# Risks & Mitigations (short)

- **Selector drift / SPA DOM differences** → Use NodeRef priority & confidence, keep operations conservative on low confidence.
- **Diff noise** → Normalize whitespace, enforce head ordering, prune no‑ops before diff.
- **Token/latency** → Summarize context (PageIntent + first fragment per issue), cap `MAX_LOCATIONS_PER_ISSUE`.
- **Concurrency** → Optional `htmlHash` to verify same page version between summary and optimize.

---
