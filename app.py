"""Run from the repository root: streamlit run app.py."""
import pandas as pd
import streamlit as st

from src.analysis import (
    DATA_PATH, SOURCE_URL, REFERENCE_URL, YEAR_ORDER, OUTCOMES, COMPARISON_FACTORS, FACTOR_NOTES,
    load_data, validate_data, prepare_data, filter_data, friendly,
    correlation_table, group_summary, burnout_summary,
)
from src.charts import hours_plot, comparison_plot, burnout_plot, gpa_distribution, relationship_plot, correlation_plot
from src.comparison import render_comparison

st.set_page_config(page_title="AI & Student Learning | INFO4125", page_icon="📊", layout="wide")
st.markdown("""<style>
    .block-container {padding-top:2rem; max-width:1500px;}
    [data-testid="stMetric"] {background:white; border:1px solid #e2e8f0;
        border-radius:12px; padding:18px;}
    [data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
    h1 {letter-spacing:-.035em;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def read_dataset(path, modified_ns):
    # Timestamp participates in the cache key when the source file changes.
    return load_data(path)


def reset_filters():
    st.session_state.pop("exploration_selection", None)
    for key in ["major_filter", "year_filter", "use_filter", "hours_filter"]:
        st.session_state.pop(key, None)


st.caption("INFO4125 · TEAM 2")
st.title("AI & student learning")
st.write("Explore how AI use relates to GPA change, skill retention, and reported dependency.")

try:
    raw = read_dataset(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
except (OSError, pd.errors.ParserError) as exc:
    st.error(f"The dataset could not be loaded: {exc}")
    st.stop()

report = validate_data(raw)
try:
    data = prepare_data(raw)
except ValueError as exc:
    st.error(str(exc))
    st.dataframe(report, hide_index=True, width="stretch")
    st.stop()

view = st.radio("View", ["Explore a selection", "Compare selections"], horizontal=True, key="view_mode")
if view == "Compare selections":
    render_comparison(data)
    with st.sidebar:
        st.header("Compare selections")
        st.write("Group A and Group B have their own filters in the main view.")
        st.caption("Exploratory associations. Collection methods, location, and real-versus-synthetic status are unverified.")
    st.stop()

with st.sidebar:
    st.header("Explore a group")
    st.caption("Selections here are combined into one group. Use Compare selections to keep two groups separate.")
    majors = sorted(data.Major_Category.unique())
    years = [y for y in YEAR_ORDER if y in data.Year_of_Study.unique()]
    uses = sorted(data.Primary_Use_Case.unique())
    previous = st.session_state.get("exploration_selection", {})
    selected_majors = st.multiselect("Major", majors, default=previous.get("major", majors), key="major_filter")
    selected_years = st.multiselect("Year of study", years, default=previous.get("year", years), key="year_filter")
    selected_uses = st.multiselect("Primary AI use case", uses, default=previous.get("use", uses), format_func=friendly, key="use_filter")
    hours = st.slider("Weekly AI hours", 0.0, 40.0, previous.get("hours", (0.0, 40.0)), step=.5, key="hours_filter")
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.divider()
    st.caption("Source: Kaggle · lavesh Jadon")
    st.caption("Exploratory associations. Collection methods, location, and real-versus-synthetic status are unverified.")

st.session_state["exploration_selection"] = {"major": selected_majors, "year": selected_years, "use": selected_uses, "hours": hours}
filtered = filter_data(data, {"Major_Category": selected_majors, "Year_of_Study": selected_years,
                              "Primary_Use_Case": selected_uses}, hours)
st.caption(f"{len(filtered):,} of {len(data):,} records selected · Findings describe this dataset, not a verified U.S. student population.")
if filtered.empty:
    st.info("No records match these filters. Expand the selection or reset the filters.")
    st.stop()
if len(filtered) < 30:
    st.warning("Fewer than 30 records are selected. Small-group summaries can be unstable; avoid broad conclusions.")

metrics = st.columns(4)
metrics[0].metric("Records selected", f"{len(filtered):,}")
metrics[1].metric("Mean GPA change", f"{filtered.GPA_Change.mean():+.3f}", help="Post-semester GPA minus pre-semester GPA. A smaller gain is not necessarily a decline.")
metrics[2].metric("Mean skill retention", f"{filtered.Skill_Retention_Score.mean():.1f} / 100")
metrics[3].metric("High burnout category", f"{filtered.Burnout_Risk_Level.eq('High').mean():.1%}", help="Dataset label, not a clinical assessment or an individual risk prediction.")

overview, compare, wellbeing, methods = st.tabs(["AI use & outcomes", "Compare groups", "Wellbeing", "Data & methods"])
with overview:
    outcome = st.selectbox("Outcome", ["GPA_Change", "Skill_Retention_Score"], format_func=friendly, key="hours_outcome")
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Outcomes across AI hours")
        st.plotly_chart(hours_plot(filtered, outcome), width="stretch")
        st.caption("Each dot is a group mean; dot size represents group size. Five-hour bands are display choices, not risk thresholds. Hover for counts and spread.")
    with right:
        st.subheader("Individual records")
        st.plotly_chart(relationship_plot(filtered, outcome), width="stretch")
        st.caption(f"Displays a reproducible sample of up to 3,000 records. All {len(filtered):,} selected records contribute to summaries and correlations.")
    st.subheader("How strong is the relationship?")
    correlations = correlation_table(filtered)
    st.dataframe(correlations, hide_index=True, width="stretch",
                 column_config={"Correlation": st.column_config.NumberColumn(format="%.3f")})
    st.caption("Pearson measures linear association; Spearman measures rank association. Values near zero indicate little association of that type. Undefined correlations appear blank. Neither demonstrates causation.")
    with st.expander("View the distribution of GPA change"):
        st.plotly_chart(gpa_distribution(filtered), width="stretch")
        st.write("Positive change means GPA increased. Negative change means GPA decreased. Zero means no change.")

with compare:
    st.subheader("Compare academic outcomes")
    col1, col2 = st.columns(2)
    group = col1.selectbox("Compare by", COMPARISON_FACTORS, format_func=friendly, key="compare_group")
    measures = [outcome for outcome in OUTCOMES if outcome != group]
    if st.session_state.get("compare_outcome") not in measures:
        st.session_state.pop("compare_outcome", None)
    metric = col2.selectbox("Measure", measures, format_func=friendly, key="compare_outcome")
    if group in FACTOR_NOTES:
        st.caption(FACTOR_NOTES[group])
    st.plotly_chart(comparison_plot(filtered, group, metric), width="stretch")
    summary = group_summary(filtered, group, metric)
    st.dataframe(summary.rename(columns={group: friendly(group), "n": "Records", "mean": "Mean", "median": "Median", "sd": "Standard deviation"}), hide_index=True, width="stretch")
    st.caption("These are unadjusted group comparisons. Starting GPA, study habits, and other differences may explain a pattern. Standard deviation describes variation among records, not uncertainty in the mean.")
    st.download_button("Download group summary", summary.to_csv(index=False), "group_summary.csv", "text/csv")

with wellbeing:
    st.subheader("Burnout categories within groups")
    burnout_group = st.selectbox("Group records by", ["Perceived_AI_Dependency", "Primary_Use_Case", "Major_Category", "Institutional_Policy"], format_func=friendly, key="burnout_group")
    st.plotly_chart(burnout_plot(filtered, burnout_group), width="stretch")
    st.caption("Percentages are calculated within each group, so different group sizes do not distort comparisons. Hover to see the denominator and count.")
    st.dataframe(burnout_summary(filtered, burnout_group), hide_index=True, width="stretch")
    st.info("Burnout and anxiety measurements are not documented sufficiently to interpret these labels as validated health measures. This dashboard does not diagnose or predict individual burnout.")

with methods:
    st.subheader("What this dataset can tell us")
    st.write("The analysis describes relationships within the supplied dataset. It cannot establish that AI causes a GPA change, identify a universal safe number of AI hours, or verify results for U.S. students ages 18–22.")
    st.markdown(f"[Dataset and column descriptions]({SOURCE_URL}) · [Notebook used for inspiration]({REFERENCE_URL})")
    st.write("The source describes 50,000 records and 16 variables. It does not document recruitment, geography, collection dates, or how skill retention and burnout were assessed. Real-versus-synthetic provenance remains unverified. Age, country, and standardized-test scores are absent.")
    st.subheader("Validation before analysis")
    st.dataframe(report, hide_index=True, width="stretch")
    st.caption("Validation describes the complete source file. No rows are deleted or imputed. Valid extreme values are retained. Non-AI study hours use a physical plausibility bound of 168 hours/week; other score bounds follow the source description.")
    st.write("GPA change is calculated as post-semester minus pre-semester GPA. Dependency and anxiety use 1–10 scales. The CSV uses Strict_Ban, although the source description spells it Strictly_Ban; the original CSV label is preserved.")
    st.subheader("Relationships among numeric variables")
    st.plotly_chart(correlation_plot(filtered), width="stretch")
    st.caption("Full selected group, Pearson correlations. Undefined values remain blank.")
    st.download_button("Download selected records", filtered.to_csv(index=False), "selected_student_records.csv", "text/csv")
    st.download_button("Download validation report", report.to_csv(index=False), "validation_report.csv", "text/csv")
