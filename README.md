# Saudi Football Infrastructure Study

Mapping the supply of football infrastructure across Saudi Arabia against demand to identify where SAFF investment will most effectively grow participation under Vision 2030.

**Prepared for SAFF management** · Author: Abdulrahman Bajunaid · v4.0, May 2026

---

## What this is

A four-week analytical study covering all 13 administrative regions of Saudi Arabia, methodologically aligned with UK Sport England and ONS conventions so the findings are internationally comparable. It answers ten research questions and benchmarks Saudi against Germany, Japan, and Türkiye.

The work integrates:
- **1,997 facilities** collected via the Google Places API across ~10 categories
- **GASTAT 2024 demographics** + **GASTAT 2025 physical activity statistics**
- **SAFF Accredited Clubs & Academies** (October 2023, OCR'd from the Arabic PDF)
- **Ministry of Sport** open data — 3,116 commercial halls, 1,175 women-flagged

All data is loaded into a Postgres database hosted on Supabase, with pre-joined views the dashboard and notebook can query directly.

## Six headline findings

1. **SAFF accreditation** — only 4.6% of clubs and academies are SAFF accredited (22 of 473). Six regions show zero.
2. **Density gap** — pitches per 10,000 vary 5×. Megaregions (Riyadh, Makkah) sit at 0.23, one quarter of the UEFA 1.0 benchmark.
3. **Inverted correlation** — Saudi r = −0.24 between pitch density and PA. UK ONS reports r = +0.49. Saudi inverts the international pattern.
4. **Women's PA already at target** — national women's PA = 43.1%, above Vision 2030's 40% target. But the gender gap is 23.4 points.
5. **Pitch deserts inside megacities** — 55% of Riyadh's and 56% of Makkah's urban area sits more than 2 km from any pitch.
6. **Sector mix** — 52% commercial, 37% public, 11% mixed. Commercial-led, padel-heavy.

## What's in this repo

| File | What it is |
|---|---|
| `Saudi_Football_Study.pptx` | 30-slide presentation deck for SAFF management |
| `Saudi_Football_Documentation.docx` | Full process documentation (this is the long-form companion to the deck) |
| `Saudi_Football_Analysis.ipynb` | Colab notebook — pulls live from Supabase, reproduces every chart in the deck plus deeper cuts |
| `README.md` | You are here |

The notebook, deck, and documentation are kept in sync — same numbers, same sources, same conclusions.

## How to run the notebook

The notebook reads from a public Supabase REST endpoint with a read-only publishable key, so it runs end-to-end on Google Colab without setup.

1. Open `Saudi_Football_Analysis.ipynb` in Colab.
2. Run **Section 1** (Setup) once per session — it pip-installs `folium`, `scikit-learn`, `statsmodels`, etc.
3. Run **Section 2** (Data load) — pulls all 13 tables/views from Supabase.
4. From there each section is self-contained. Run them in any order.

The notebook produces:
- Every chart used in the deck (Q1, Q3, Q4, Q6, Q9, Q10, benchmark)
- An interactive folium map of all 1,997 facilities
- A correlation matrix on regional indicators
- K-means clustering on the 13 regions
- Vision 2030 target tracking
- CSV exports of every analytical table

## Database

| Setting | Value |
|---|---|
| Project | `Football_Fields_Mapping_SA` |
| Project ID | `hdcqusmfyovcvtdlawbm` |
| Region | `ap-southeast-1` |
| Postgres | 15 |
| REST base | `https://hdcqusmfyovcvtdlawbm.supabase.co/rest/v1/` |
| Publishable key | `sb_publishable_uhXX_xRAVZ2s6nKtJiWCmw_8UPPQQTu` (read-only, safe to embed) |

### Primary tables and views

| Object | Rows | Purpose |
|---|---|---|
| `facilities` | 1,997 | All Google-Places-derived football facilities |
| `regional_demographics` | 13 | Population, youth under 21 per region |
| `regional_pa_2025` | 13 | PA total / women / men estimates per region |
| `saff_accredited` | 69 | SAFF Oct 2023 list, mapped to facilities (22 matched) |
| `regional_women_facilities` | 13 | MOS halls women / total / per 100k |
| `q2_sample_coding` | 106 | Hand-coded sample with rationale per row |
| `q3_pitch_deserts` | 15 | 5 cities × 3 thresholds, % desert + area km² |
| `q9_correlations` | 7 | Pearson + Spearman + weighted r per hypothesis |
| `v_regional_master` | 13 | Pre-joined master with all 30+ region metrics |
| `v_q10_priorities` | 13 | Tier classification per region |
| `v_data_quality` | 8 | Data quality scorecard |

## Methodology in one paragraph

Per-10k denominators throughout (Sport England / UEFA convention). 13 administrative regions for cross-sectional analyses; 5 cities for the geospatial pitch-desert analysis. Women's PA per region uses a hybrid 2025 × 2021 estimate calibrated to GASTAT national 43.06%. Q2 (sector mix) uses a hand-coded stratified sample of 106 facilities with Wilson 95% CI and finite-population correction. Q3 (pitch deserts) uses scipy's ConvexHull + 1 km buffer + 500 m grid + Haversine distance via cKDTree. Q9 runs seven hypothesis tests, both unweighted and population-weighted, with and without megaregions, separately for men and women.

## Limitations worth knowing

- **Google Places undercounts** informal and school pitches, especially in lower-income areas. Facility counts are conservative.
- **SAFF list is from October 2023** — the most recent published. SAFF may have expanded accreditation since.
- **32% match rate** between the SAFF list and the facilities table. The unmatched 47 entries are mostly small commercial academies and women's clubs not visible in Google Maps — a real coverage gap, not a fuzzy-matcher failure.
- **Q3 uses Euclidean distance**, not network distance. Real walking is 1.2–1.4× longer.
- **n = 13 regions for Q9** is a coarser grain than ONS UK's hundreds of Local Authorities. Confidence intervals on the correlation are wide.
- **Q2, Q3, Q5, Q7 are Saudi-specific** — comparable benchmark data isn't published in Germany, Japan, or Türkiye in 2024-25 reporting.

## Recommendations (summary)

1. **Re-tag, don't build.** Q1 + Q9 show new construction will not lift PA. Convert under-utilized capacity for women's hours.
2. **Lead with women's programming in 3 regions** — Eastern, Madinah, Aseer (Q10 Tier 1). Recruit 50 female coaches there in 24 months.
3. **Treat SAFF accreditation as a market-shaping lever.** Refresh the 2023 list with 2025-26 data, then set a 5-year 25% target.
4. **Fill desert pockets in Riyadh and Makkah.** Re-tag and add school partnerships before greenfield builds.
5. **Build the female coach pipeline.** Concentrate the existing 1,000+ coaches and 90 referees in Tier 1 regions.
6. **Use Google ratings as a soft quality signal — 50+ reviews only.** Build SAFF-verified badges to displace noise.
7. **Don't replicate Riyadh's hall density everywhere.** Prioritize Northern Borders and Aseer.

## Sources at a glance

- **Demand**: GASTAT Census 2022 + 2024 estimates; GASTAT Physical Activity Statistics 2025; GASTAT Sports Practice Survey 2021
- **Supply**: Google Places API (Apr 2026); SAFF Accredited Clubs PDF (Oct 2023, OCR'd); MOS Open Data — commercial halls (2024)
- **Methodology**: UK ONS Sport Participation methodology; UK Sport England / UEFA per-10k denominators
- **Benchmark**: DFB Mitgliederstatistik 2024/25; JFA registered players March 2024; TFF licensed players; SAFF / Saudipedia 2024
- **Saudi women's football**: SAFF VP Lamia Bahaian (FIFA Women's Football Convention 2023); NEOM/SAFF Women's Football Report (Jan 2025)

---

*Saudi Football Infrastructure Study  ·  v4.0  ·  May 2026  ·  Prepared by Abdulrahman Bajunaid*
