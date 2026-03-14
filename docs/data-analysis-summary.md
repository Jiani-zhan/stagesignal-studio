# Data Analysis Summary

## Build context
- Script: `scripts/build_demo_data.py`
- Deterministic seed: `20260314`
- Parser: XLSX zip+xml (shared strings + sheet XML)
- XLT handling: binary `.xlt` kept as fallback-only source and documented in source health report

## Output inventory
- Comparable events rows: `124`
- Audience text rows: `528`
- Survey responses rows: `140`
- Channel metrics rows: `7`
- Hero segments: `4`

## Hero-case findings (Beethoven After Dark, NYC)
- Recommended GA price: `$74.92`
- Recommended premium price: `$118.37`
- Acceptable range: `$49.99` to `$100.38`
- Base expected attendance: `274` / 280
- Base expected occupancy: `0.9786`
- Base expected revenue: `$23861.56`
- Top conversion channels: `instagram_reels, youtube_trailer, spotify_audio_teaser`

## Assumptions and synthetic labels
- `is_synthetic`: marks generated rows introduced to complete demo-ready schemas
- `assumption_note`: explains why synthetic data was required and how it was grounded
- Synthetic counts by table:
  - events_comps: `0`
  - audience_text: `520`
  - survey_responses: `140`
  - channel_metrics: `3`

## Provenance policy
- Every table includes `source_file` and `source_sheet` fields
- Hero artifacts trace numeric claims back to segment, demand, and pricing JSON assets

## Limitations
- Survey and parts of channel metrics are deterministic synthetic placeholders for demo mode
- Demand and revenue are simulation outputs; they are not validated ticket-sales forecasts
