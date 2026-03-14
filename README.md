# StageSignal

StageSignal is an audience intelligence and pricing prototype for live arts launches. This build is a static, admissions-focused GitHub Pages app that uses offline-generated artifacts from `Final presentation.zip` for the hero case **Beethoven After Dark (NYC)**, ending with an executive recommendation synthesis section.

## What this demo shows

- Audience signal integration from comparable events, audience text, channel proxies, and survey-style pricing responses.
- Beautiful static analytics report layout focused on evidence, scenarios, pricing, and model validation.
- Pricing-first recommendation flow with acceptable range, purchase probability curve, revenue curve, and executive memo output.
- Real trained model suite with labels from source zip (`Broadway Revenue`):
  - weekly gross regression
  - average ticket regression
  - sellout classification
- Model Validation Lab showing predicted-vs-actual charts and threshold gates (`R2` / `Accuracy`).
- Final recommendation synthesis section that consolidates narrative conclusions from upstream artifacts.
- Data Foundation section includes curated dataset catalog and direct downloads for normalized CSV/JSON files.
- No real-time model inference in browser: all outputs are precomputed JSON artifacts.

## Repository map

- `index.html`: GitHub Pages entrypoint and full narrative/demo UI.
- `assets/styles/`: design tokens, layout, and UI components.
- `assets/scripts/`: data loader, agent runtime, chart rendering, page wiring.
- `assets/data/`: canonical and hero-case JSON artifacts consumed by frontend.
- `scripts/build_demo_data.py`: deterministic stdlib-only data pipeline.
- `scripts/train_model_suite.py`: deterministic stdlib-only model training pipeline.
- `docs/data-analysis-summary.md`: source audit, assumptions, and output summary.
- `docs/superpowers/plans/2026-03-14-stagesignal-githubio-demo.md`: implementation plan and subagent assignment.

## Core data source

- `Final presentation.zip` (and extracted `Final presentation/`) is the primary evidence source.
- Since source files are incomplete for full production-grade schemas, synthetic augmentation is included and explicitly labeled with:
  - `is_synthetic`
  - `assumption_note`

## Local run

1) Rebuild demo data assets:

```bash
python3 scripts/build_demo_data.py
```

This command also runs model training and refreshes:

- `assets/data/model_performance.json`
- `assets/data/model_predictions.json`
- `assets/data/model_features.json`

To reproduce model training directly from curated downloadable CSV data:

```bash
python3 scripts/train_model_suite.py --events-csv assets/data/events_comps.csv --output-dir ./repro_output
```

2) Serve static site:

```bash
python3 -m http.server 8000
```

3) Open:

`http://localhost:8000`

## Deploy to GitHub Pages

1) Push this project to a GitHub repository.
2) In GitHub -> Settings -> Pages:
   - Source: `Deploy from a branch`
   - Branch: `main` (or your default branch)
   - Folder: `/ (root)`
3) Wait for Pages build and open your public URL.

Alternative (already included):

- `.github/workflows/deploy-pages.yml` can publish automatically via GitHub Actions when pushed to `main`.
- Ensure Pages is enabled with **Build and deployment -> GitHub Actions**.

Because the app is static and path-relative, no backend service is required.

## Verification commands

```bash
node --check assets/scripts/data-loader.js
node --check assets/scripts/agent-system.js
node --check assets/scripts/charts.js
node --check assets/scripts/main.js
python3 scripts/build_demo_data.py
python3 scripts/train_model_suite.py
```

## Model acceptance gate

- Metrics are generated in `assets/data/model_performance.json`.
- Required threshold per model:
  - regression models: `R2 >= 0.8`
  - classification models: `Accuracy >= 0.8`
- Frontend `Model Validation Lab` mirrors these gates and displays predicted-vs-actual comparisons.

## 60-90 second demo script

1) Hero: explain the launch decision problem for immersive Beethoven in NYC.
2) Highlight source reliability, audience segment snapshot, and theme prevalence.
3) Show Demand Scenario analysis and occupancy/revenue implications.
4) Show Pricing Studio curves and rationale.
5) Open Model Validation Lab to compare predicted vs actual labels + threshold pass badges.
6) End on Agent-Assisted Text Synthesis for final recommendations and risk framing.
