# AI & Student Learning

INFO4125 · Fall 2026 · Team 2

Explore how AI usage relates to GPA change, skill retention, and reported dependency in the supplied dataset. Includes an executable Jupyter notebook, a Streamlit dashboard, shared analysis functions, and reproducible CSV outputs.

## Start

Run from the repository root (Python 3.12 recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`. Open the local address printed by Streamlit, usually http://localhost:8501. No Kaggle credentials or Google Drive access are required. `requirements.txt` defines supported dependency ranges; `requirements-lock.txt` records the verified environment.

## Analysis and verification

```bash
jupyter lab notebooks/01_exploration.ipynb
python scripts/analyze.py
python -m pytest
```

Restart the notebook kernel and run all cells. The notebook and dashboard import the same analysis and chart functions. The analysis script creates ignored `outputs/` files: validation report, prepared data, correlations, use-case summaries, and source SHA-256 metadata. Rerunning replaces only derived outputs. Dashboard downloads reflect current filters.

## Research questions

1. How do GPA change and skill retention vary with weekly AI hours?
2. How do outcomes differ by AI use case, major, year, and prompting skill?
3. How do burnout categories vary with perceived AI dependency?

All comparisons are exploratory and unadjusted. Weak or absent relationships are valid findings. Adjusted modeling is a possible extension, not part of this first version.

## Data and preparation

- [Dataset: lavesh Jadon, Impact of Ai on Students](https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students), version 1. Metadata reviewed September 30, 2026; source lists CC0: Public Domain.
- Original file: `data/ai_student_impact_dataset.csv`, initially 50,000 records and 16 columns. No missing cells, duplicate rows, or duplicate IDs were found. Validation runs again whenever data changes.
- Original records are retained. No imputation, outlier deletion, winsorization, or forced category correction.
- `GPA_Change = Post_Semester_GPA - Pre_Semester_GPA`, in GPA points. Lower change may mean a smaller gain, not a decline.
- Dependency and anxiety: 1–10. Skill retention: 0–100. GPA: 0–4. AI hours: documented 0–40. Traditional study hours: physical plausibility bound 0–168 hours/week, not the observed sample maximum.
- The source description says `Strictly_Ban`; the CSV says `Strict_Ban`. The CSV label is preserved. Display labels replace underscores only.
- Invalid values, missing columns, unknown categories, and duplicates stop analysis for review rather than silently changing data.

## Dashboard

Choose **Explore a selection** to combine selected categories into one group, or **Compare selections** to define Group A and Group B independently. Each comparison group has its own major, year, AI use case, and inclusive weekly-hours range. Choices within one filter use OR; separate filters use AND. Comparison filters use the full dataset, not the exploration subset.

The comparison displays counts, GPA change, retention, burnout share, baseline GPA, and study habits side by side, with **B minus A** differences. Burnout differences use percentage points. It reports shared records without dropping them, preserves selections while switching views, and supports copying the exploration filters into either group. Empty-group estimates remain unavailable. Download the results and selection definitions to reproduce a comparison. Default hour ranges are examples, not risk thresholds.

- **AI use & outcomes:** five-hour group means, scatterplot, Pearson/Spearman correlations, GPA-change distribution. Exactly 40 hours belongs in the last band. Summaries use all filtered records; scatterplots show at most 3,000 with a fixed random seed.
- **Compare groups:** means, medians, standard deviations, and counts. Standard deviation describes observed spread, not a confidence interval.
  Group by use case, major, year, prompting skill, policy, paid subscription, number of AI tools, AI hours, non-AI study hours, dependency, exam anxiety, burnout category, or starting GPA. Hours and GPA use fixed, labeled display bands; numeric scales and ordered categories appear in order. Empty bands are omitted. The outcome cannot be the grouping factor itself.
- **Wellbeing:** burnout percentages calculated within groups, with counts and denominators.
- **Data & methods:** source limitations, full-file validation, filtered correlations, and downloads.
- Clearing a filter selects no records; reset restores all records. Tiny groups receive a caution. Undefined correlations remain blank instead of zero.
- Five-hour bins are presentation choices, not evidence of safe or harmful thresholds.

## Evidence limits

Recruitment, collection dates, geography, and measurement methods are undocumented. Real-versus-synthetic provenance is unverified. Complete data does not establish authenticity or representativeness.

Age, country, standardized-test scores, and a verified intervention/control design are absent. Graduate records are included. Do not describe the data as a verified U.S. sample ages 18–22, or pre/post GPA as pre/post AI adoption. Associations and unadjusted comparisons do not establish causation. Burnout categories are not clinical diagnoses.

## Structure and teamwork

```text
app.py                         Dashboard
data/                          Original CSV (unchanged)
notebooks/01_exploration.ipynb  Executable analysis and interpretation
src/analysis.py                Validation and shared calculations
src/charts.py                  Shared Plotly figures
scripts/analyze.py             Reproducible analysis outputs
tests/                         Analysis and dashboard checks
outputs/                       Derived files (Git-ignored)
```

Assign one notebook editor at a time, use branches, and run all cells before review. Include the original CSV in the team repository so everyone uses the same input.

Thematic inspiration: [lavesh Jadon's exploration notebook](https://www.kaggle.com/code/laveshjadon/data-exploration-and-cleaning-ipynb). This implementation uses original code and does not adopt its claimed thresholds or conclusions without verification.

This project runs locally. No Google Drive files are changed and nothing is published automatically.
