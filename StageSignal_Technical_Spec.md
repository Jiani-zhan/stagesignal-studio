# StageSignal — Technical Specification

## 0. One-sentence brief

**StageSignal** is an agentic audience intelligence and pricing studio for live arts launches. It turns fragmented audience signals, comparable event data, and rapid survey inputs into audience segmentation, demand estimation, pricing scenarios, and an executive recommendation memo.

This project is optimized for **Columbia MS in Marketing Science admissions signaling**, not for building a generic AI demo. Everything in the system is designed to make the applicant look like someone who already thinks in the language of marketing science: problem definition, mixed-method research, segmentation, demand forecasting, pricing, and decision support.

---

## 1. Product thesis

### 1.1 Why this exact product

The strongest storyline is not “music student who built an AI app.” It is:

> “I repeatedly encountered the same decision problem in live arts and music marketing—how to identify the right audience, estimate demand, and price an artistic experience under uncertainty—so I built a decision system that formalizes those choices using marketing research and statistical modeling.”

That narrative aligns with:

- audience research and segmentation
- text mining and qualitative/quantitative synthesis
- demand estimation
- pricing strategy
- decision-oriented recommendations
- consulting-style output

### 1.2 Hero use case

**Primary demo case:**

`Launch planning for an immersive Beethoven after-dark performance in New York City`

This hero case should be preloaded and polished.

It connects:
- classical music / live arts credibility
- prior Beethoven Festival experience
- future immersive theater ambition
- a pricing problem with obvious business stakes

### 1.3 Non-goals

Do **not** turn StageSignal into:
- a generic chatbot
- an AI copywriter
- a social media post generator
- a music recommendation engine
- a full CRM / marketing automation suite
- a production-grade enterprise SaaS

This is a **high-conviction, narrow, admissions-optimized decision prototype**.

---

## 2. Final architecture decision

## 2.1 Recommended architecture: hybrid shell

Use a **hybrid architecture**:

1. **GitHub Pages landing shell**
   - purpose: premium first impression
   - style: editorial / minimalist / “impeccable-style” inspired
   - content: thesis, hero visuals, agent stack, screenshots, methodology summary, Columbia fit
   - CTA: `Open Demo` → Streamlit app

2. **Streamlit analytical workspace**
   - purpose: actual data interaction, simulation, memo generation
   - content: event brief, audience intelligence, forecast lab, pricing lab, recommendation memo, methodology

3. **Offline Python analytics pipeline**
   - purpose: reproducible preprocessing, feature engineering, modeling, artifact generation
   - outputs: cleaned data, model artifacts, JSON summaries, cached embeddings, screenshots for landing page

This architecture maximizes both:
- **design quality** for admissions reviewers
- **functional credibility** for analytics and modeling

## 2.2 Why not pure Streamlit

Pure Streamlit can support multipage apps, navigation, forms, session state, caching, themes, HTML insertion, and components. However, the design target here is not a standard dashboard; it is a polished narrative experience with strong motion, typography, and landing-page composition. Pixel-perfect design-heavy hero sections are easier and cleaner on a static front-end shell. The Streamlit side should remain focused on interaction and decision support.

## 2.3 Deployment topology

- `stagesignal.github.io` → landing page
- `stagesignal-demo.streamlit.app` (or Render/Cloud Run) → Streamlit app
- Optional single custom domain later if desired

---

## 3. System modules

StageSignal has **two layers**:

### Layer A — Narrative shell (landing page)
Purpose: make the project feel like a polished research product.

### Layer B — Analytical engine (app)
Purpose: let a user input or load an event brief and get structured outputs.

### Layer C — Agent / model orchestration
Purpose: convert data into decision-ready deliverables.

---

## 4. End-to-end user flow

1. Reviewer lands on GitHub Pages landing page.
2. Sees hero: “From artistic intuition to marketing science.”
3. Scrolls through 4–5 sections:
   - problem
   - agent stack
   - dashboard previews
   - methodology
   - Columbia fit
4. Clicks `Open Demo`.
5. Streamlit opens in **Demo Mode** with the Beethoven case preloaded.
6. User can inspect:
   - audience segments
   - demand drivers
   - price sensitivity
   - pricing scenarios
   - executive memo
7. Optional: user switches to **Custom Mode** and uploads CSVs.
8. App exports PDF/Markdown memo and screenshot bundle.

---

## 5. Data strategy

## 5.1 Core principle

Do not rely on large, unstable scraping infrastructure.

For a 7-day build, the right choice is a **small but methodologically serious dataset**.

Use 3 data layers:

### A. Comparable events table (`events_comps.csv`)
Target size: 80–150 rows

Fields:
- `event_id`
- `event_name`
- `event_type` (classical / broadway / immersive / jazz / crossover)
- `city`
- `venue_name`
- `venue_capacity`
- `event_date`
- `launch_window_days`
- `positioning_statement`
- `genre_tags`
- `language_context`
- `ticket_price_low`
- `ticket_price_mid`
- `ticket_price_high`
- `bundle_available`
- `student_discount`
- `premium_experience`
- `social_posts_count`
- `engagement_proxy`
- `sellout_proxy`
- `attendance_proxy`
- `earned_media_count`
- `partner_branding`
- `notes`

### B. Audience text corpus (`audience_text.csv`)
Target size: 500–1,500 rows

Sources can be manually collected public text snippets from:
- Reddit
- YouTube comments
- public event reviews
- public forum posts
- public captions / comments copied into CSV

Fields:
- `text_id`
- `source`
- `source_type` (reddit / review / youtube / blog / forum)
- `event_reference`
- `raw_text`
- `date`
- `city_context`
- `language`
- `engagement_signal` (upvotes/likes if available)

### C. Micro-survey (`survey_responses.csv`)
Target size: 50–150 responses

This is the most important “marketing science” asset.

Include:
- demographics and context
- event interest
- channel preference
- attendance history
- willingness-to-pay
- perceived fit
- price sensitivity items

Use two pricing methods:

#### Method 1: Gabor-Granger
Ask purchase intent at randomized ticket prices.

Fields:
- `price_shown`
- `purchase_intent_binary`
- `purchase_intent_likert`

#### Method 2: Van Westendorp
Ask:
- at what price is this too cheap?
- a bargain?
- expensive but still worth considering?
- too expensive?

Fields:
- `too_cheap`
- `cheap`
- `expensive`
- `too_expensive`

### D. Optional channel metrics (`channel_metrics.csv`)
Target size: small, manual

Fields:
- `channel`
- `audience_size_proxy`
- `historical_ctr`
- `estimated_conversion`
- `cpm_or_cost_proxy`

---

## 6. Predictive modeling stack

## 6.1 Design principles

Models must be:
- explainable
- implementable in 7 days
- visually compelling in a demo
- aligned with marketing science language
- robust under small-data constraints

Do **not** center the project on deep learning.

## 6.2 Model suite

### Model A — Audience theme extraction
Goal: identify what people care about in live arts discourse.

**Recommended v1 approach:**
- text cleaning
- TF-IDF + noun phrase extraction
- sentence embeddings (`all-MiniLM-L6-v2`)
- topic extraction using BERTopic or NMF fallback

**Outputs:**
- top themes
- theme frequencies
- representative quotes/snippets
- theme-by-source matrix

### Model B — Audience segmentation
Goal: produce 3–5 audience segments that feel both data-driven and strategically useful.

**Inputs:**
- survey features
- text-cluster affinities
- attendance habits
- genre preferences
- price sensitivity
- channel preference

**Recommended v1 approach:**
- standardize numeric survey variables
- one-hot encode categorical variables
- optionally append semantic-cluster proportions
- KMeans or Agglomerative clustering
- choose `k` with silhouette score + interpretability

**Outputs:**
- segment labels
- segment size
- key motivations
- key channel preferences
- average WTP
- risk flags

**Proposed segment examples:**
- Classical Purists
- Cultural Trend Seekers
- Broadway/Experience Enthusiasts
- International Young Professionals / Students

### Model C — Interest / conversion intent model
Goal: estimate how likely each segment is to attend the hero event.

**Target options:**
- binary: likely to attend vs not likely
- ordinal: interest score 1–5

**Recommended v1 approach:**
- logistic regression for binary intent
- ordinal regression or gradient boosting for Likert intent
- calibration step if using probabilistic output

**Features:**
- segment
- prior attendance frequency
- city proximity
- genre fit
- immersive interest
- social proof sensitivity
- price shown
- preferred show time
- friend/group attendance tendency

**Outputs:**
- predicted probability of attendance by segment
- marginal effect of price
- feature importance / coefficient table

### Model D — Demand scenario simulator
Goal: turn intent into venue-level outcomes.

This should not pretend to forecast real box office exactly. It should simulate plausible demand under assumptions.

**Recommended v1 approach:**
- base audience reach assumption by segment
- multiply by predicted conversion probability
- adjust by channel mix, launch timing, and message fit
- run Monte Carlo simulation over conversion uncertainty

**Outputs:**
- expected attendance
- occupancy interval
- expected revenue interval
- sensitivity by channel / positioning / price

### Model E — Pricing model
This is the signature module.

#### Part 1: Acceptable range
Use Van Westendorp to estimate:
- indifference price point
- optimal price point
- acceptable price range

#### Part 2: Purchase probability
Use Gabor-Granger responses to fit:
- logistic purchase model vs price
- segment-specific elasticity if sample size allows

#### Part 3: Ticket architecture simulation
Simulate pricing structures:
- standard tiering (GA / premium / VIP)
- early-bird
- student ticket
- pair bundle
- premium package with backstage/artist talk

**Optimization target:**
Provide three objectives, not one:
- maximize revenue
- maximize occupancy
- maximize accessibility-adjusted revenue

**Outputs:**
- recommended base price
- recommended premium tier
- student discount guardrail
- scenario matrix
- elasticity chart

### Model F — Recommendation synthesis
Goal: convert raw analysis into a concise executive recommendation.

This is where the LLM is used.

**LLM responsibilities:**
- summarize segments
- explain price recommendation
- draft decision memo
- suggest channel emphasis
- translate charts into plain-English recommendations

**LLM must not:**
- invent numbers
- invent sources
- override model outputs
- make unsupported claims

---

## 7. Agent system

The system should be framed as **7 coordinated agents**, even though the core logic is deterministic analytics.

## 7.1 Agent list

### Agent 1 — Brief Agent
**Role:** Parse and normalize the event brief.

**Input:**
- event concept
- city
- venue size
- target audience hypothesis
- budget assumptions
- candidate price range
- experience type

**Output JSON:**
```json
{
  "event_name": "Beethoven After Dark",
  "city": "New York",
  "venue_capacity": 280,
  "event_type": "immersive classical",
  "candidate_price_low": 45,
  "candidate_price_high": 120,
  "target_goal": "maximize revenue with strong first-night buzz"
}
```

### Agent 2 — Research Ingestion Agent
**Role:** Load comparable events, text corpus, and survey data.

**Responsibilities:**
- schema validation
- missing value audit
- derived feature generation
- source health report

**Outputs:**
- cleaned tables
- data quality warnings
- source summary card

### Agent 3 — Audience Intelligence Agent
**Role:** Extract themes and cluster audiences.

**Responsibilities:**
- topic extraction
- keyword surfacing
- persona generation
- segment naming

**Outputs:**
- segment summary objects
- audience map artifacts
- supporting evidence snippets

### Agent 4 — Demand Forecast Agent
**Role:** Estimate attendance intent and simulate occupancy.

**Responsibilities:**
- fit/load intent model
- predict by segment
- aggregate across channel assumptions
- generate uncertainty intervals

**Outputs:**
- demand scenario table
- occupancy band chart
- high/low/base cases

### Agent 5 — Pricing Agent
**Role:** Estimate willingness-to-pay and optimize ticket architecture.

**Responsibilities:**
- compute Van Westendorp intersections
- fit Gabor-Granger purchase model
- simulate tier/bundle outcomes
- rank pricing options

**Outputs:**
- recommended pricing ladder
- elasticity curves
- trade-off explanation

### Agent 6 — Memo Agent
**Role:** Produce a consulting-style recommendation.

**Structure:**
- objective
- target segments
- pricing recommendation
- launch messaging
- risk/assumption note
- next test to run

### Agent 7 — Critic / QA Agent
**Role:** Block hallucinations and weak logic.

**Checks:**
- every number in memo appears in upstream outputs
- no unsupported claims
- no contradiction between occupancy and revenue claims
- price recommendation remains inside acceptable range unless explicitly justified

---

## 8. Agent orchestration

## 8.1 Orchestration mode

Use **deterministic sequential orchestration**.

Not autonomous multi-hop agents.

Reason:
- more stable
- easier to debug
- better for small data
- easier to explain in interview
- safer for Streamlit rerun model

## 8.2 Pipeline sequence

```text
User submits Event Brief
    ↓
Brief Agent normalizes inputs
    ↓
Research Ingestion Agent validates and loads data
    ↓
Audience Intelligence Agent builds segments and themes
    ↓
Demand Forecast Agent predicts attendance under scenarios
    ↓
Pricing Agent estimates acceptable range and optimal ladder
    ↓
Memo Agent generates executive brief
    ↓
Critic Agent validates claims
    ↓
Streamlit renders outputs + export options
```

## 8.3 Caching policy

- cache data transforms
- cache embedding/model objects
- cache precomputed hero case artifacts
- do not cache user-specific memo text globally

---

## 9. Suggested tech stack

## 9.1 Core analytics
- Python 3.11
- pandas
- numpy
- scikit-learn
- scipy
- sentence-transformers
- plotly
- pydantic
- statsmodels (optional, especially for pricing / ordinal models)
- networkx (optional community graph)
- joblib
- pyarrow / parquet

## 9.2 App
- Streamlit
- Plotly charts inside Streamlit
- `st.Page` / `st.navigation`
- `st.form`
- `st.session_state`
- `st.cache_data`
- `st.cache_resource`
- optional `st.html` for branded hero blocks inside the app

## 9.3 Landing page
Preferred:
- Astro or static HTML/CSS/JS

Alternative:
- Vite + React if team prefers component structure

Design system:
- CSS variables
- minimal JS motion
- GSAP optional but not required

## 9.4 Storage
- local CSV/Parquet for v1
- optional DuckDB for cleaner queries

## 9.5 Deployment
- GitHub Pages for landing
- Streamlit Community Cloud / Render for app
- artifact bundle in repo releases if needed

---

## 10. Repository structure

```text
stagesignal/
├── README.md
├── landing/
│   ├── index.html
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── layout.css
│   │   └── components.css
│   ├── scripts/
│   │   └── main.js
│   └── assets/
│       ├── hero-preview.webp
│       ├── screenshots/
│       └── icons/
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   │   ├── 01_Overview.py
│   │   ├── 02_Event_Brief.py
│   │   ├── 03_Audience_Intelligence.py
│   │   ├── 04_Demand_Lab.py
│   │   ├── 05_Pricing_Studio.py
│   │   ├── 06_Executive_Memo.py
│   │   └── 07_Methodology.py
│   ├── services/
│   │   ├── orchestrator.py
│   │   ├── schemas.py
│   │   ├── loaders.py
│   │   ├── preprocess.py
│   │   ├── topics.py
│   │   ├── segmentation.py
│   │   ├── demand.py
│   │   ├── pricing.py
│   │   ├── memo.py
│   │   └── critic.py
│   ├── components/
│   │   ├── cards.py
│   │   ├── charts.py
│   │   ├── hero.py
│   │   └── exports.py
│   ├── assets/
│   │   ├── theme.css
│   │   └── logo.svg
│   └── .streamlit/
│       └── config.toml
├── data/
│   ├── raw/
│   │   ├── events_comps.csv
│   │   ├── audience_text.csv
│   │   ├── survey_responses.csv
│   │   └── channel_metrics.csv
│   ├── interim/
│   └── processed/
│       ├── events_features.parquet
│       ├── survey_features.parquet
│       ├── text_topics.json
│       ├── segments.json
│       └── hero_case_outputs.json
├── models/
│   ├── segment_model.joblib
│   ├── intent_model.joblib
│   └── pricing_model.joblib
├── notebooks/
│   ├── 01_data_prep.ipynb
│   ├── 02_segmentation.ipynb
│   ├── 03_demand_model.ipynb
│   └── 04_pricing_model.ipynb
├── scripts/
│   ├── build_artifacts.py
│   ├── export_screenshots.py
│   └── generate_demo_bundle.py
└── docs/
    ├── methodology.md
    ├── data_dictionary.md
    ├── model_cards.md
    └── application_storyline.md
```

---

## 11. Data contracts

## 11.1 `EventBrief`

```python
class EventBrief(BaseModel):
    event_name: str
    event_type: str
    city: str
    venue_name: str | None = None
    venue_capacity: int
    launch_date: date | None = None
    candidate_price_low: float
    candidate_price_mid: float | None = None
    candidate_price_high: float
    budget_band: str | None = None
    target_goal: Literal[
        "maximize_revenue",
        "maximize_occupancy",
        "balanced",
        "accessibility_weighted"
    ]
    concept_description: str
```

## 11.2 `AudienceSegment`

```python
class AudienceSegment(BaseModel):
    segment_id: str
    segment_name: str
    segment_size_pct: float
    motivations: list[str]
    barriers: list[str]
    preferred_channels: list[str]
    avg_wtp: float | None = None
    price_sensitivity: str
    representative_themes: list[str]
```

## 11.3 `DemandScenario`

```python
class DemandScenario(BaseModel):
    scenario_name: str
    base_price: float
    premium_price: float | None = None
    expected_attendance: float
    expected_occupancy_pct: float
    expected_revenue: float
    revenue_p10: float
    revenue_p90: float
```

## 11.4 `PriceRecommendation`

```python
class PriceRecommendation(BaseModel):
    acceptable_range_low: float
    acceptable_range_high: float
    optimal_price_point: float | None = None
    recommended_ga_price: float
    recommended_premium_price: float | None = None
    recommended_student_price: float | None = None
    rationale: list[str]
```

## 11.5 `ExecutiveMemo`

```python
class ExecutiveMemo(BaseModel):
    headline: str
    objective: str
    top_segments: list[str]
    pricing_decision: str
    channel_decision: str
    positioning_decision: str
    key_risks: list[str]
    next_experiment: str
    support_metrics: dict[str, float | str]
```

---

## 12. Streamlit app design

## 12.1 Multipage navigation

Pages:
1. Overview
2. Event Brief
3. Audience Intelligence
4. Demand Lab
5. Pricing Studio
6. Executive Memo
7. Methodology

### Page 1 — Overview
Purpose: orient reviewer instantly.

Content blocks:
- one-sentence thesis
- “Why this exists”
- hero KPIs for demo case
- `Load Demo Case` button
- `Switch to Custom Mode` toggle

### Page 2 — Event Brief
Purpose: structured input, not free-form chaos.

Layout:
- left: form
- right: live summary card

Inputs:
- event concept
- city
- venue capacity
- event type
- price range
- objective
- optional target audience assumption

Must use `st.form` so inputs batch before rerun.

### Page 3 — Audience Intelligence
Purpose: prove this is more than a pricing calculator.

Visuals:
- segment cards
- topic/theme bar chart
- 2D cluster map
- source distribution
- quote evidence drawer

Key widgets:
- filter by source
- filter by segment
- filter by city context

### Page 4 — Demand Lab
Purpose: connect audience to business outcome.

Visuals:
- attendance forecast card
- occupancy interval chart
- sensitivity table
- scenario selector (base / optimistic / conservative)

Widgets:
- channel mix sliders
- message fit dropdown
- launch lead time slider

### Page 5 — Pricing Studio
Purpose: signature page.

Visuals:
- Van Westendorp chart
- purchase probability vs price curve
- revenue curve
- occupancy vs price curve
- tiered ticket matrix

Widgets:
- GA price slider
- premium price slider
- student discount toggle
- pair bundle toggle
- objective selector

### Page 6 — Executive Memo
Purpose: consulting-style output.

Content:
- summary headline
- 3 recommended actions
- supporting metrics
- key assumptions
- export buttons

Export:
- Markdown
- PDF (optional)
- screenshot bundle

### Page 7 — Methodology
Purpose: admissions credibility.

Content:
- data sources
- model logic
- assumptions and limitations
- what is statistical inference vs simulation
- what would be improved in a v2

This page matters a lot.

---

## 13. Visual design system

## 13.1 Design direction

The landing page should be **editorial, spacious, and deliberate**, inspired by the design principles visible on the reference site:
- hierarchy first
- obvious whitespace
- numbered sections
- restrained color use
- anti-generic layout choices

Do **not** build a dashboard that looks like a Kaggle demo.

## 13.2 Brand concept

Theme name: **Nocturne Intelligence**

This bridges:
- performing arts sophistication
- analytics precision
- premium admissions presentation

## 13.3 Color tokens

```css
--bg: #0b0d12;
--surface: #121722;
--surface-2: #171d2b;
--text: #f4efe6;
--muted: #a6adbb;
--line: rgba(255,255,255,0.10);
--accent: #d8b36a;      /* brass / stage light */
--accent-2: #6fd3c4;    /* data / signal */
--danger: #ff8a7a;
--success: #8ad29a;
```

Alternative light panel tokens for chart cards:

```css
--paper: #f7f3eb;
--ink: #11151c;
--ink-muted: #515866;
```

## 13.4 Typography

Recommended:
- Display/headlines: `Fraunces` or `Cormorant Garamond`
- UI/body: `Manrope` or `Geist`

Reason:
- serif for culture / gravitas
- sans for analytics / clarity

## 13.5 Spacing system

Use 8-point spacing scale:
- 8 / 16 / 24 / 32 / 48 / 64 / 96

## 13.6 Visual rules

- use thin borders, not heavy shadows
- large section padding
- no excessive gradients
- no “cards on cards on cards” clutter
- one accent color per section max
- charts should use muted neutral gridlines
- keep copy tight and high-signal

## 13.7 Landing page sections

### Section 1 — Hero
Headline example:

**From artistic intuition to marketing science.**

Subhead:

StageSignal helps live arts teams identify audiences, estimate demand, and design pricing under uncertainty.

Hero layout:
- left: headline / thesis / CTA
- right: animated mockup of audience map + pricing curve

### Section 2 — Problem
Numbered label: `01`

Copy frame:
- live arts teams still make launch decisions with fragmented data
- the hard parts are not promotion alone, but targeting, valuation, and pricing

### Section 3 — Agent Stack
Numbered label: `02`

Use a clean 6-step horizontal flow or vertical rail.

### Section 4 — Demo Screens
Numbered label: `03`

Show 3 screenshots:
- audience intelligence
- demand lab
- pricing studio

### Section 5 — Methodology
Numbered label: `04`

Mixed-method → segmentation → estimation → pricing → memo

### Section 6 — Why it matters
Numbered label: `05`

Tie to cultural marketing and immersive experience design.

---

## 14. Streamlit styling strategy

## 14.1 What to customize in Streamlit

Safe/clean customizations:
- theme via `.streamlit/config.toml`
- page config
- custom cards via `st.container` + `st.markdown`
- selective `st.html` blocks for premium hero or stat banners
- Plotly theme consistency

Avoid:
- relying on fragile DOM class selectors for the entire app
- reproducing the full landing page inside Streamlit

## 14.2 Streamlit theme config sketch

```toml
[theme]
base="dark"
primaryColor="#d8b36a"
backgroundColor="#0b0d12"
secondaryBackgroundColor="#121722"
textColor="#f4efe6"
font="sans serif"
```

## 14.3 Streamlit components usage

Use custom helper components for:
- metric card
- segment card
- assumption warning pill
- recommendation block
- methodology accordion

---

## 15. Chart specification

## 15.1 Audience Intelligence charts
- Topic prevalence bar chart
- 2D embedding scatter (colored by segment)
- Source-by-theme heatmap
- Segment WTP boxplot
- Segment channel preference stacked bar

## 15.2 Demand Lab charts
- Attendance forecast with P10/P50/P90 bands
- Waterfall of key demand contributors
- Segment-level conversion bar chart
- Scenario comparison table

## 15.3 Pricing Studio charts
- Van Westendorp cumulative curves
- Purchase probability vs price
- Revenue vs price
- Occupancy vs price
- Ticket tier comparison table
- Segment-specific elasticity panel

## 15.4 Memo visuals
- 3 key decision cards
- risk matrix
- “What to test next” panel

---

## 16. Modeling details for the AI coder

## 16.1 Text preprocessing pipeline

Steps:
1. normalize unicode
2. lowercase
3. remove URLs / emoji if needed
4. light stopword removal
5. preserve proper nouns and genre terms
6. language flag
7. compute sentence embeddings
8. compute TF-IDF features

Artifacts:
- `text_embeddings.npy`
- `tfidf_matrix.npz`
- `topic_terms.json`

## 16.2 Segmentation feature matrix

Candidate features:
- age band
- student / professional
- borough / city proximity
- attendance frequency
- genre preference scores
- immersive interest score
- price sensitivity score
- group attendance tendency
- channel preference encoding
- semantic theme proportions

Procedure:
1. impute missing values
2. scale numeric variables
3. one-hot categoricals
4. fit clustering model
5. compute silhouette / Davies-Bouldin
6. generate segment narrative summaries

## 16.3 Intent model

Baseline:
- logistic regression with regularization

Optional better model:
- XGBoost / LightGBM if the data size is large enough

Output:
- per-respondent intent probability
- per-segment average intent
- effect of price / immersive preference / attendance frequency

## 16.4 Demand simulation

Formula sketch:

```text
expected_attendance
= Σ over segments (
    reachable_audience_segment
    × modeled_conversion_segment
    × message_fit_multiplier
    × timing_multiplier
)
```

Uncertainty:
- sample conversion probability from Beta or normal approximation
- run 1,000 simulations
- summarize P10 / P50 / P90

## 16.5 Pricing estimation

### Van Westendorp
Compute cumulative distributions of:
- too cheap
- cheap
- expensive
- too expensive

Derive:
- point of marginal cheapness
- point of marginal expensiveness
- indifference price point
- optimal price point

### Gabor-Granger
Fit logistic model:

```text
purchase ~ price + segment + immersive_interest + attendance_frequency
```

Then simulate purchase probability across a price grid.

### Ticket optimization
For each candidate ladder:
- GA price
- premium price
- student discount
- bundle option

Estimate:
- expected attendance
- expected occupancy
- expected revenue
- accessibility score

Rank ladders by user objective.

---

## 17. Memo agent prompt contract

Use a structured prompt like this:

```text
SYSTEM:
You are a marketing strategy analyst. You must only use the metrics provided in the structured input. Do not invent data, benchmarks, or causal claims.

USER:
Create a concise executive recommendation for a live arts launch.
Use the following sections:
1. Objective
2. Top audience segments
3. Pricing recommendation
4. Positioning recommendation
5. Channel recommendation
6. Key risks and assumptions
7. Next experiment

Inputs:
- event brief
- segment summaries
- demand scenarios
- pricing recommendation
- methodology notes
```

Output should be JSON first, then rendered markdown.

---

## 18. Critic agent checks

The QA agent should run the following assertions:

1. All numeric claims in memo appear in upstream JSON.
2. Recommended price is within acceptable range or explicitly marked exploratory.
3. Revenue recommendation does not contradict occupancy objective.
4. Segment names appearing in memo exist in segmentation output.
5. Risk section includes at least one data limitation.
6. No absolute language like “will definitely sell out.”
7. If survey N < 50, include low-confidence warning.

---

## 19. Subagent task breakdown

Below is the recommended multi-subagent assignment for your AI coder.

## Subagent A — Product & orchestration lead
**Mission:** own system blueprint and data contracts.

**Deliverables:**
- `docs/application_storyline.md`
- `app/services/schemas.py`
- `app/services/orchestrator.py`
- routing logic for Demo Mode vs Custom Mode

**Acceptance criteria:**
- every module shares the same schemas
- full pipeline runs end-to-end on hero case

## Subagent B — Data engineering
**Mission:** data ingestion, validation, and preprocessing.

**Deliverables:**
- `app/services/loaders.py`
- `app/services/preprocess.py`
- `docs/data_dictionary.md`
- sample processed datasets

**Acceptance criteria:**
- all CSVs validate cleanly
- app displays clear warnings for missing columns

## Subagent C — NLP / audience intelligence
**Mission:** topic extraction and segmentation.

**Deliverables:**
- `app/services/topics.py`
- `app/services/segmentation.py`
- `models/segment_model.joblib`
- `data/processed/segments.json`

**Acceptance criteria:**
- 3–5 interpretable segments
- segment cards auto-generated from data
- at least one audience map visualization works

## Subagent D — Demand forecasting
**Mission:** interest model + simulation engine.

**Deliverables:**
- `app/services/demand.py`
- `models/intent_model.joblib`
- scenario simulator utilities

**Acceptance criteria:**
- outputs expected attendance and uncertainty bands
- supports objective toggles and scenario toggles

## Subagent E — Pricing science
**Mission:** WTP and ticket ladder recommendation.

**Deliverables:**
- `app/services/pricing.py`
- `models/pricing_model.joblib`
- Van Westendorp chart builder
- Gabor-Granger simulation

**Acceptance criteria:**
- app returns acceptable range + recommended ladder
- revenue curve responds to slider changes

## Subagent F — Streamlit interface
**Mission:** build analytical workspace.

**Deliverables:**
- all `app/pages/*.py`
- `app/components/*.py`
- `.streamlit/config.toml`
- `app/assets/theme.css`

**Acceptance criteria:**
- multipage navigation works
- demo mode loads instantly
- export buttons work
- visual quality is non-generic

## Subagent G — Landing page / design system
**Mission:** build the premium shell.

**Deliverables:**
- `landing/index.html`
- CSS tokens/layout/components
- screenshots/GIF integration
- CTA bridge to app

**Acceptance criteria:**
- page feels editorial and premium
- first screen immediately communicates value
- mobile responsive enough for links and screenshots

## Subagent H — Memo + QA
**Mission:** LLM synthesis and evidence validation.

**Deliverables:**
- `app/services/memo.py`
- `app/services/critic.py`
- exportable memo format

**Acceptance criteria:**
- memo contains no fabricated numbers
- every statement can be traced to structured outputs

## Subagent I — Demo packaging
**Mission:** admissions-facing polish.

**Deliverables:**
- `scripts/export_screenshots.py`
- hero screenshots
- 60–90 second demo script
- README demo section

**Acceptance criteria:**
- reviewer can understand the project in under 90 seconds
- screenshots look publication-ready

---

## 20. Suggested prompts for AI coder subagents

### Prompt for Subagent C

```text
You are the NLP and audience intelligence engineer for StageSignal.
Build a pipeline that:
1. ingests audience_text.csv and survey_responses.csv
2. extracts topics/themes
3. creates 3–5 interpretable audience segments
4. outputs JSON summaries with motivations, barriers, channel preferences, and price sensitivity
Constraints:
- prioritize interpretability over complexity
- support the hero case: immersive Beethoven launch in NYC
- every output must be usable in Streamlit cards and Plotly charts
Deliver code, model artifacts, and a brief explanation of segmentation logic.
```

### Prompt for Subagent E

```text
You are the pricing science engineer for StageSignal.
Build a pricing module for live arts launches that combines:
- Van Westendorp acceptable price range
- Gabor-Granger purchase probability modeling
- scenario simulation for GA/premium/student/bundle pricing
Constraints:
- prioritize explainability
- outputs must include charts and a ranked recommendation ladder
- expose clean functions that can be called by Streamlit
Deliver pricing.py, tests, model artifacts if needed, and usage examples.
```

### Prompt for Subagent G

```text
You are the front-end design engineer for the StageSignal landing page.
Build a static landing page inspired by editorial minimalism and the reference impeccable-style site.
Requirements:
- strong hierarchy
- large whitespace
- section numbering
- premium typography
- dark theme with restrained accent color
- CTA to Streamlit demo
- sections: Hero, Problem, Agent Stack, Demo Screens, Methodology, Why It Matters
Avoid generic SaaS gradients and cluttered cards.
Deliver HTML/CSS/JS that can deploy on GitHub Pages.
```

---

## 21. Demo-mode data bundle

The app must ship with a **hero demo bundle** so the reviewer never needs to upload anything.

Include:
- `hero_event_brief.json`
- `hero_segments.json`
- `hero_demand_scenarios.json`
- `hero_pricing_recommendation.json`
- `hero_memo.md`

This lets the app load instantly.

---

## 22. What the reviewer should feel

After 60 seconds, the reviewer should conclude:

1. This applicant understands that marketing science is not just content creation.
2. They can define a decision problem clearly.
3. They understand segmentation, demand estimation, and pricing.
4. They are translating arts-domain experience into analytical reasoning.
5. They are exactly the kind of person who would benefit from Columbia MSM.

If the project instead makes the reviewer think “nice dashboard,” it underperformed.

---

## 23. Methodology page copy skeleton

Use this structure inside the app:

### Data Sources
Comparable events, public audience text, and a rapid-response pricing survey.

### Research Logic
Qualitative and quantitative signals are combined: public language reveals motivations and barriers; survey responses estimate purchase intent and willingness-to-pay; comparable event data anchors scenario planning.

### Modeling Logic
Audience segmentation groups respondents by behavior, preference, and price sensitivity. An intent model estimates attendance likelihood. Pricing recommendations combine acceptable-range analysis and purchase-probability modeling.

### Limitations
This is a decision-support prototype, not a guaranteed forecasting engine. Results depend on data quality, sample size, and the assumptions encoded in scenario simulation.

### Why this matters
The purpose is not to automate taste. It is to make cultural launch decisions more rigorous, interpretable, and testable.

---

## 24. 7-day execution plan

## Day 1
- finalize product scope
- define data schema
- build repo skeleton
- create landing wireframe
- create Streamlit page stubs

## Day 2
- collect comparable events data
- design and launch survey
- collect initial audience text corpus

## Day 3
- preprocess data
- build topic extraction
- build first segmentation pass
- draft segment cards

## Day 4
- build intent model
- build demand simulator
- implement Demand Lab charts

## Day 5
- build Van Westendorp + Gabor-Granger pricing module
- implement Pricing Studio
- connect recommendation ranking logic

## Day 6
- implement memo + critic agents
- finish landing page
- integrate screenshots / CTA / copy polish

## Day 7
- QA
- export screenshots
- finalize README
- rehearse demo script
- align copy with essays and resume bullets

---

## 25. README positioning

The README should open with this framing:

> StageSignal is an audience intelligence and pricing prototype for live arts launches. Built around a demo case in immersive classical performance, it combines audience text mining, survey-based willingness-to-pay estimation, demand simulation, and recommendation synthesis to support launch decisions under uncertainty.

Then immediately show:
- 3 screenshots
- 3 bullets on why it matters
- architecture diagram
- methodology
- how to run

---

## 26. Resume bullet suggestion

**Built StageSignal, an agentic marketing intelligence prototype for live arts launches that combined audience text mining, survey-based segmentation, demand simulation, and pricing optimization to generate launch recommendations for immersive performance concepts.**

---

## 27. Interview explanation (30-second version)

> I built StageSignal because I kept seeing the same gap in cultural marketing: we can often generate interest creatively, but we rarely formalize audience targeting, willingness-to-pay, and launch pricing with enough rigor. So I built a prototype that takes comparable events, public audience language, and survey data, then turns them into segments, demand scenarios, and pricing recommendations for a live performance launch.

---

## 28. Hard constraints to keep the project honest

1. Never claim real ticket-sales prediction accuracy unless validated.
2. Never present simulated revenue as audited truth.
3. Never let the LLM invent metrics.
4. Never let the landing page promise enterprise capability.
5. Always present the system as a decision-support prototype.
6. Keep the scope centered on **live arts launch planning**.

---

## 29. Final recommendation

If resources are constrained, prioritize in this order:

1. **Pricing Studio**
2. **Audience Intelligence**
3. **Executive Memo**
4. **Landing page polish**
5. **Demand Lab**
6. **Custom upload mode**

If only one page can be exceptional, make it **Pricing Studio**.

That is the single most Columbia-aligned signal in this build.

