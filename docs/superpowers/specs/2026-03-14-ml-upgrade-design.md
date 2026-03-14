# StageSignal ML Upgrade Design

## Objective

Upgrade the existing static StageSignal demo so that core analytical sections are backed by genuinely trained predictive models. All model labels must come from real fields inside `Final presentation.zip` source data.

## Scope

- Keep static GitHub Pages architecture (no real-time browser compute).
- Add offline model training pipeline and persist outputs as JSON assets.
- Redesign presentation layer to visualize predicted vs actual labels and model quality metrics.

## Model Suite

### Model 1: Weekly Gross Regression (Demand)

- **Label (real):** `This Week's Gross` from `Broadway Revenue` sheet.
- **Features:** `Last Week's Gross`, `Average Ticket`, `Top Ticket`, `Seats Sold`, `Total Seats`, `Last Week %`, week serial trend.
- **Type:** Multiple linear regression (closed-form normal equation).
- **Primary metric:** holdout `R2`.

### Model 2: Seats Sold Regression (Demand)

- **Label (real):** `Seats` (sold seats) from `Broadway Revenue` sheet.
- **Features:** `Last Week's Gross`, `Average Ticket`, `Top Ticket`, `Total Seats`, `This Week %`, week serial trend.
- **Type:** Multiple linear regression (closed-form normal equation).
- **Primary metric:** holdout `R2`.

### Model 3: Sellout Classification (Audience/Launch Risk)

- **Label (real):** `sellout_flag = 1 if This Week % >= 1.0 else 0` derived from real occupancy label column.
- **Features:** `Last Week's Gross`, `Diff $`, `Average Ticket`, `Top Ticket`, `Total Seats`, `Last Week %`.
- **Type:** Logistic regression (gradient descent).
- **Primary metric:** holdout `Accuracy`.

## Data and Validation Strategy

- Parse source xlsx deterministically with stdlib zip+xml parser.
- Remove rows with missing required numeric columns.
- Deterministic train/test split (fixed seed, shuffled index).
- Compute and export per-model metrics: `R2`, `MAE`, `RMSE` for regressions, `Accuracy`, `Precision`, `Recall`, confusion matrix for classification.
- Acceptance gate: every model must satisfy `R2 >= 0.8` or `Accuracy >= 0.8`.

## Artifacts

- `assets/data/model_performance.json`: model-level metrics and acceptance status.
- `assets/data/model_predictions.json`: holdout predicted vs actual rows for visualization.
- `assets/data/model_features.json`: feature definitions and coefficient/weight diagnostics.

## Frontend Redesign

- Add a dedicated **Model Validation Lab** section.
- Show model cards for all 3 models with metric badges and pass/fail status.
- Add predicted vs actual visualizations:
  - Gross: scatter + ideal line.
  - Seats sold: scatter + ideal line.
  - Sellout classifier: confusion matrix and sample-level predicted/actual comparison.
- Preserve existing 7-agent narrative and integrate model outputs into Agent 3-5 panels.

## Risks and Mitigations

- **Risk:** data quality issues in source rows.
  - **Mitigation:** strict numeric parse guards and dropped-row counts in model report.
- **Risk:** metrics under threshold.
  - **Mitigation:** feature engineering with trend/interaction terms and deterministic tuning loops.
- **Risk:** UI complexity overload.
  - **Mitigation:** add one focused validation section instead of scattering charts everywhere.
