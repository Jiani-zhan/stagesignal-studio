# StageSignal ML Upgrade Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real trained predictive models (real labels from source zip) and redesign the static demo to show predicted-vs-actual comparisons with pass/fail metrics.

**Architecture:** Keep offline data pipeline + static rendering. Introduce a dedicated model training script that parses source labels from `Broadway Revenue`, trains 3 deterministic models, exports model artifacts, then surface those artifacts in a new frontend validation section.

**Tech Stack:** Python 3 stdlib, HTML/CSS/JavaScript, Plotly.js.

---

## File Responsibility Map

- `scripts/train_model_suite.py`: parse source rows and train/evaluate all models.
- `assets/data/model_performance.json`: quality metrics and acceptance gates.
- `assets/data/model_predictions.json`: holdout predictions vs actual labels.
- `assets/data/model_features.json`: feature definitions and model coefficients.
- `index.html`: add Model Validation Lab section and target containers.
- `assets/styles/layout.css`, `assets/styles/components.css`: add layout/components for model cards and comparison panels.
- `assets/scripts/data-loader.js`: load model assets.
- `assets/scripts/charts.js`: render prediction-vs-actual and confusion matrix charts.
- `assets/scripts/main.js`: wire model metrics, validation cards, and chart updates.
- `README.md`: add model training and acceptance verification instructions.

---

## Chunk 1: Model Training Pipeline

### Task 1: Implement deterministic training script

**Files:**
- Create: `scripts/train_model_suite.py`
- Create: `assets/data/model_performance.json`
- Create: `assets/data/model_predictions.json`
- Create: `assets/data/model_features.json`

- [ ] **Step 1: Implement source extraction and row normalization**
- [ ] **Step 2: Implement split, scaling, and matrix utilities (stdlib only)**
- [ ] **Step 3: Train two regression models + one classification model**
- [ ] **Step 4: Compute holdout metrics and acceptance gates**
- [ ] **Step 5: Export model artifacts and print summary**

### Task 2: Integrate training into data build flow

**Files:**
- Modify: `scripts/build_demo_data.py`

- [ ] **Step 1: invoke training script from build process (or document explicit command sequence)**
- [ ] **Step 2: ensure deterministic order and error handling**

---

## Chunk 2: Frontend Redesign for Validation

### Task 3: Add Model Validation Lab UI

**Files:**
- Modify: `index.html`
- Modify: `assets/styles/layout.css`
- Modify: `assets/styles/components.css`

- [ ] **Step 1: add validation section with model cards and metric badges**
- [ ] **Step 2: add chart containers for regression and classification comparisons**
- [ ] **Step 3: ensure responsive composition and readability**

---

## Chunk 3: Runtime Wiring and Visualization

### Task 4: Load model artifacts and render comparisons

**Files:**
- Modify: `assets/scripts/data-loader.js`
- Modify: `assets/scripts/charts.js`
- Modify: `assets/scripts/main.js`

- [ ] **Step 1: load model JSON assets and expose normalized state**
- [ ] **Step 2: add chart builders for predicted-vs-actual and confusion matrix**
- [ ] **Step 3: bind model metrics to cards and pass/fail state**
- [ ] **Step 4: reset flows and fallback behavior when Plotly unavailable**

---

## Chunk 4: Verification and Documentation

### Task 5: Verify acceptance criteria and update docs

**Files:**
- Modify: `README.md`

- [ ] **Step 1: run training and confirm `R2/Accuracy >= 0.8` for all models**
- [ ] **Step 2: run JS syntax checks and local static smoke test**
- [ ] **Step 3: document verification commands and metric thresholds in README**

---

## Subagent Assignment

- **Subagent A (Modeling):** Task 1 + Task 2.
- **Subagent B (UI/Design):** Task 3.
- **Subagent C (Runtime/Charts):** Task 4.
- **Main coordinator:** Task 5 integration verification and final acceptance reporting.
