"""Streamlit view for comparing two independently filtered selections."""
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import (
    YEAR_ORDER, BURNOUT_ORDER, filter_data, friendly,
    selection_comparison, selection_overlap,
)
from src.charts import style, COLORS, BLUE, TEAL


def reset_comparison():
    st.session_state.pop("comparison_selections", None)
    for group in ["a", "b"]:
        for field in ["major", "year", "use", "hours"]:
            st.session_state.pop(f"selection_{group}_{field}", None)


def use_exploration(group, defaults):
    copied = {}
    for field in ["major", "year", "use", "hours"]:
        # Keep the exploration snapshot when its widgets are not on the current page.
        value = st.session_state.get("exploration_selection", {}).get(field, defaults[field])
        copied[field] = value
        st.session_state.pop(f"selection_{group}_{field}", None)
    saved = dict(st.session_state.get("comparison_selections", {}))
    saved[group] = copied
    st.session_state["comparison_selections"] = saved


def render_comparison(data):
    st.subheader("Compare two selections")
    st.write("Build each group separately. Multiple choices within a filter are combined; different filters must all match.")
    st.caption("These filters use the full dataset independently of the exploration view. Starting hour ranges are examples, not recommended limits.")
    st.button("Reset comparison", on_click=reset_comparison, key="reset_comparison")
    options = {
        "major": sorted(data.Major_Category.unique()),
        "year": [y for y in YEAR_ORDER if y in data.Year_of_Study.unique()],
        "use": sorted(data.Primary_Use_Case.unique()),
        "hours": (0.0, 40.0),
    }
    groups, definitions = {}, {}
    saved = st.session_state.get("comparison_selections", {})
    current = {}
    for group, column, default_hours in zip(["a", "b"], st.columns(2), [(0.0, 5.0), (10.0, 20.0)]):
        label = f"Group {group.upper()}"
        defaults = saved.get(group, {**options, "hours": default_hours})
        with column:
            with st.container(border=True):
                st.markdown(f"### {label}")
                st.button("Use exploration selection", key=f"copy_exploration_{group}",
                          on_click=use_exploration, args=(group, options),
                          help="Copy the most recent filters from Explore a selection.")
                majors = st.multiselect("Major", options["major"], default=defaults["major"], key=f"selection_{group}_major")
                years = st.multiselect("Year of study", options["year"], default=defaults["year"], key=f"selection_{group}_year")
                uses = st.multiselect("Primary AI use case", options["use"], default=defaults["use"], format_func=friendly, key=f"selection_{group}_use")
                hours = st.slider("Weekly AI hours", 0.0, 40.0, defaults["hours"], step=.5, key=f"selection_{group}_hours")
                current[group] = {"major": majors, "year": years, "use": uses, "hours": hours}
                definitions[label] = {"Major_Category": majors, "Year_of_Study": years, "Primary_Use_Case": uses,
                                      "Weekly_GenAI_Hours_inclusive": list(hours)}
                selected = filter_data(data, {"Major_Category": majors, "Year_of_Study": years, "Primary_Use_Case": uses}, hours)
                groups[label] = selected
                st.metric(f"{label} records", f"{len(selected):,}")
                if selected.empty:
                    st.info(f"{label} has no matching records. Expand its filters to compare outcomes.")
                elif len(selected) < 30:
                    st.warning(f"{label} contains fewer than 30 records; summaries may be unstable.")

    st.session_state["comparison_selections"] = current
    a, b = groups["Group A"], groups["Group B"]
    overlap = selection_overlap(a, b)
    if overlap:
        st.info(f"{overlap:,} records belong to both groups and are included in both summaries. The groups are not independent samples.")
        if overlap == len(a) == len(b):
            st.caption("Both selections contain exactly the same records. Change one group's filters to compare different selections.")
    else:
        st.caption("The selections share no records. Different group composition may still explain outcome differences.")

    result = selection_comparison(a, b)
    st.subheader("Results side by side")
    st.caption("Differences are Group B minus Group A. Positive means B is numerically higher, not necessarily better. A smaller GPA gain is not a GPA decline.")
    st.dataframe(result, hide_index=True, width="stretch", column_config={
        name: st.column_config.NumberColumn(format="%.3f") for name in ["Group A", "Group B", "B minus A"]
    })
    st.caption("Empty-group outcomes are unavailable, not zero. Burnout differences are percentage points. Baseline GPA and study hours help show how the groups differ before interpreting outcomes.")

    if not a.empty and not b.empty:
        left, right = st.columns(2)
        with left:
            measure = st.selectbox("Compare outcome", ["Mean GPA change", "Mean skill retention", "Mean AI dependency"], key="selection_outcome")
            row = result.set_index("Measure").loc[measure]
            chart = pd.DataFrame({"Selection": ["Group A", "Group B"], "Mean": [row["Group A"], row["Group B"]], "Records": [len(a), len(b)]})
            fig = px.bar(chart, x="Selection", y="Mean", color="Selection", text_auto=".3f", hover_data=["Records"],
                         color_discrete_map={"Group A": BLUE, "Group B": TEAL}, labels={"Mean": f"{measure} ({row['Unit']})"})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(rangemode="tozero")
            st.plotly_chart(style(fig), width="stretch")
        with right:
            st.markdown("**Burnout categories**")
            records = []
            for name, df in groups.items():
                for category in BURNOUT_ORDER:
                    count = int(df.Burnout_Risk_Level.eq(category).sum())
                    records.append({"Selection": name, "Category": category, "Percent": 100 * count / len(df), "Count": count, "Group size": len(df)})
            fig = px.bar(pd.DataFrame(records), x="Selection", y="Percent", color="Category", color_discrete_map=COLORS,
                         category_orders={"Category": BURNOUT_ORDER}, hover_data=["Count", "Group size"])
            fig.update_yaxes(range=[0, 100], ticksuffix="%")
            st.plotly_chart(style(fig), width="stretch")
        st.caption("These are descriptive, unadjusted comparisons. They do not isolate an effect of AI use or establish statistical significance.")

    st.download_button("Download comparison results", result.to_csv(index=False), "selection_comparison.csv", "text/csv", key="download_comparison")
    st.download_button("Download selection definitions", json.dumps({"selections": definitions, "shared_records": overlap}, indent=2),
                       "selection_definitions.json", "application/json", key="download_definitions")
