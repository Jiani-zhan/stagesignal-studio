# StageSignal GitHub.io Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete StageSignal AI Agent System demo from `StageSignal_Technical_Spec.md`, powered by `Final presentation.zip` data, deployable as a static GitHub Pages site with no real-time compute.

**Architecture:** Use an offline data pipeline to normalize and enrich core source files into deterministic JSON artifacts, then render a premium static web experience that simulates the 7-agent orchestration flow. The browser only reads precomputed assets and animates agent outputs, charts, and executive memo sections.

**Tech Stack:** Python 3 standard library (offline data processing), HTML/CSS/JavaScript (static site), Plotly.js CDN (client-side chart rendering), GitHub Pages.

---

## File Responsibility Map

- `scripts/build_demo_data.py`: Parse core source files from `Final presentation.zip`, build canonical tables, generate synthetic-but-labeled augmentation, export processed JSON.
- `assets/data/*.json`: Canonical and derived demo artifacts used directly by browser runtime.
- `index.html`: Narrative shell + agent system demo surface.
- `assets/styles/tokens.css`: Global design tokens, typography, color system.
- `assets/styles/layout.css`: Layout grids, section composition, responsive behavior.
- `assets/styles/components.css`: Cards, timeline, chart wrappers, memo styles, interaction states.
- `assets/scripts/data-loader.js`: Fetch and cache demo JSON assets.
- `assets/scripts/agent-system.js`: Deterministic 7-agent orchestration and state transitions.
- `assets/scripts/charts.js`: Plotly chart builders and update functions.
- `assets/scripts/main.js`: Page bootstrapping, section interactions, glue code.
- `README.md`: Project framing, local run steps, GitHub Pages deployment guide.
- `docs/data-analysis-summary.md`: Data audit and schema coverage summary.

---

## Chunk 1: Data Foundation (Core Source -> Canonical Assets)

### Task 1: Build deterministic data extraction and normalization

**Files:**
- Create: `scripts/build_demo_data.py`
- Create: `docs/data-analysis-summary.md`
- Create: `data/processed/spec_coverage_matrix.json`

- [ ] **Step 1: Write extraction scaffolding tests (sanity assertions inside script)**
  - Assert required source files exist after extraction.
  - Assert workbook parser can discover target sheets.

- [ ] **Step 2: Implement minimal XML-based XLSX reader (stdlib only)**
  - Parse shared strings and worksheet XML.
  - Convert worksheets to row dictionaries with header inference.

- [ ] **Step 3: Parse and normalize source tables**
  - Extract `Broadway Revenue`, `Streaming Data`, `Audience Demographics`, `B1`, `B2`, `C2`.
  - Standardize numeric formats (`K/M/B`, percentages, blanks).

- [ ] **Step 4: Build canonical StageSignal tables**
  - `events_comps` (from weekly revenue + benchmark assumptions).
  - `audience_text` (from report/visual seeds + structured snippets).
  - `channel_metrics` (from social/channel proxies).
  - `survey_responses` (synthetic, assumption-labeled for demo only).

- [ ] **Step 5: Export processed assets**
  - Write JSON outputs to `assets/data/`.
  - Write `spec_coverage_matrix.json` and data audit markdown.

### Task 2: Build hero-case derived artifacts for agent modules

**Files:**
- Create: `assets/data/hero_event_brief.json`
- Create: `assets/data/hero_segments.json`
- Create: `assets/data/hero_demand_scenarios.json`
- Create: `assets/data/hero_pricing_recommendation.json`
- Create: `assets/data/hero_memo.json`
- Create: `assets/data/source_health_report.json`

- [ ] **Step 1: Implement deterministic segment synthesis logic**
  - Produce 4 interpretable segments with motivations/barriers/channels/WTP.

- [ ] **Step 2: Implement demand simulation output generation**
  - Generate base/optimistic/conservative scenarios with occupancy and revenue bands.

- [ ] **Step 3: Implement pricing recommendation outputs**
  - Include Van Westendorp range + Gabor-Granger purchase curve summaries.

- [ ] **Step 4: Implement memo + critic-ready fields**
  - Ensure every numeric claim in memo maps to upstream artifacts.

- [ ] **Step 5: Validate output schema completeness**
  - Assert required keys per artifact before writing files.

---

## Chunk 2: Premium GitHub Pages Shell (Static)

### Task 3: Build editorial, admissions-grade landing + demo frame

**Files:**
- Create: `index.html`
- Create: `assets/styles/tokens.css`
- Create: `assets/styles/layout.css`
- Create: `assets/styles/components.css`

- [ ] **Step 1: Create semantic section structure in HTML**
  - Sections: Hero, Problem, Agent Stack, Data Intelligence, Demand Lab, Pricing Studio, Executive Memo, Methodology, Columbia Fit.

- [ ] **Step 2: Implement design tokens and typography setup**
  - Dark editorial base with restrained accents and clear contrast.

- [ ] **Step 3: Implement responsive layout and composition**
  - Desktop split layouts + mobile single-column stack.

- [ ] **Step 4: Implement component styling**
  - Agent timeline cards, KPI strips, chart cards, memo panel, assumptions panel.

- [ ] **Step 5: Add non-generic motion layer**
  - Staggered reveals, data pulse effect, agent progression highlights.

---

## Chunk 3: Agent System Runtime (No Real-Time Compute)

### Task 4: Implement deterministic 7-agent orchestration in browser

**Files:**
- Create: `assets/scripts/data-loader.js`
- Create: `assets/scripts/agent-system.js`
- Create: `assets/scripts/charts.js`
- Create: `assets/scripts/main.js`

- [ ] **Step 1: Implement data loading and cache layer**
  - Fetch all required JSON assets once and expose normalized state.

- [ ] **Step 2: Implement sequential orchestration engine**
  - Simulate Agent 1 -> Agent 7 with deterministic payload handoffs.

- [ ] **Step 3: Implement panel rendering per agent output**
  - Update cards/tables/narrative blocks as each step completes.

- [ ] **Step 4: Implement chart rendering and updates (Plotly)**
  - Audience map proxy, scenario chart, pricing curves, risk matrix.

- [ ] **Step 5: Implement controls for Demo Mode and replay**
  - Buttons: Run Full Pipeline, Step Through, Reset, Export Memo JSON.

---

## Chunk 4: Integration, Validation, and Deployment Packaging

### Task 5: Wire everything and validate static deploy readiness

**Files:**
- Modify: `index.html`
- Modify: `assets/styles/*.css`
- Modify: `assets/scripts/*.js`
- Create: `README.md`

- [ ] **Step 1: Integrate all script/style references and data paths**
  - Ensure pathing works on root-level GitHub Pages.

- [ ] **Step 2: Run local static server check**
  - Verify all assets load and no JS runtime errors.

- [ ] **Step 3: Validate mobile and desktop rendering**
  - Confirm navigation, chart containers, and CTA behavior.

- [ ] **Step 4: Validate narrative and methodological claims**
  - Ensure all numbers are sourced from artifacts and assumptions disclosed.

- [ ] **Step 5: Document deployment and demo script**
  - Add GitHub Pages deployment steps and a 60-90s walkthrough.

---

## Subagent Assignment Matrix

- **Subagent A (Data Engineering):** Task 1 + Task 2 (`scripts/build_demo_data.py`, all `assets/data/*.json`, `docs/data-analysis-summary.md`).
- **Subagent B (Visual Design):** Task 3 (`index.html` + all CSS files).
- **Subagent C (Agent Runtime):** Task 4 (`assets/scripts/*.js` with deterministic orchestration).
- **Main Coordinator (this session):** Task 5 integration, verification, and README finalization.

## Completion Criteria

- Static site launches from `index.html` and runs full 7-agent demo offline from local JSON.
- No real-time model inference required in browser.
- Core source provenance from `Final presentation.zip` is documented, including synthetic augmentation assumptions.
- Project is directly deployable to GitHub Pages.
