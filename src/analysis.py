"""Pure analysis functions. Loading never changes the original CSV."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "ai_student_impact_dataset.csv"
SOURCE_URL = "https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students"
REFERENCE_URL = "https://www.kaggle.com/code/laveshjadon/data-exploration-and-cleaning-ipynb"
YEAR_ORDER = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"]
BURNOUT_ORDER = ["Low", "Medium", "High"]
CATEGORIES = {
    "Major_Category": ["STEM", "Business", "Humanities", "Medical", "Arts"],
    "Year_of_Study": YEAR_ORDER,
    "Primary_Use_Case": ["Copywriting/Drafting", "Summarizing_Reading", "Debugging/Troubleshooting", "Ideation", "Direct_Answer_Generation"],
    "Prompt_Engineering_Skill": ["Beginner", "Intermediate", "Advanced"],
    "Institutional_Policy": ["Allowed_With_Citation", "Strict_Ban", "Actively_Encouraged"],
    "Burnout_Risk_Level": BURNOUT_ORDER,
}
RANGES = {
    "Pre_Semester_GPA": (0, 4), "Post_Semester_GPA": (0, 4),
    "Weekly_GenAI_Hours": (0, 40), "Traditional_Study_Hours": (0, 168),
    "Tool_Diversity": (1, 5), "Perceived_AI_Dependency": (1, 10),
    "Anxiety_Level_During_Exams": (1, 10), "Skill_Retention_Score": (0, 100),
}
REQUIRED = ["Student_ID", *CATEGORIES, *RANGES, "Paid_Subscription"]
INTEGER_COLUMNS = ["Student_ID", "Tool_Diversity", "Perceived_AI_Dependency", "Anxiety_Level_During_Exams"]
OUTCOMES = ["GPA_Change", "Skill_Retention_Score", "Perceived_AI_Dependency"]
COMPARISON_FACTORS = [
    "Primary_Use_Case", "Major_Category", "Year_of_Study", "Prompt_Engineering_Skill", "Institutional_Policy",
    "Paid_Subscription", "Tool_Diversity", "Weekly_GenAI_Hours", "Traditional_Study_Hours",
    "Perceived_AI_Dependency", "Anxiety_Level_During_Exams", "Burnout_Risk_Level", "Pre_Semester_GPA",
]
# Left-closed intervals. nextafter includes the valid maximum in the final band.
COMPARISON_BINS = {
    "Weekly_GenAI_Hours": ([0, 5, 10, 15, 20, 25, 30, 35, np.nextafter(40., np.inf)],
                           ["0–<5", "5–<10", "10–<15", "15–<20", "20–<25", "25–<30", "30–<35", "35–40"]),
    "Traditional_Study_Hours": ([0, 5, 10, 15, 20, 25, 30, np.inf],
                                ["0–<5", "5–<10", "10–<15", "15–<20", "20–<25", "25–<30", "30+"]),
    "Pre_Semester_GPA": ([0, 2, 2.5, 3, 3.5, np.nextafter(4., np.inf)],
                         ["0–<2.0", "2.0–<2.5", "2.5–<3.0", "3.0–<3.5", "3.5–4.0"]),
}
FACTOR_NOTES = {
    "Weekly_GenAI_Hours": "AI hours are grouped in five-hour bands; exactly 40 hours is included in the final band. These are display ranges, not risk thresholds.",
    "Traditional_Study_Hours": "Non-AI study hours are grouped in five-hour bands up to 30, then 30 or more. These ranges describe the data, not recommended study times.",
    "Pre_Semester_GPA": "Starting GPA is grouped below 2.0, then in half-point bands through 4.0. GPA change includes starting GPA in its calculation, so this comparison can reflect ceiling effects and regression to the mean.",
    "Paid_Subscription": "Compare records with and without a paid AI subscription. Subscription status does not measure ability to afford one.",
    "Tool_Diversity": "Number of distinct AI tools used, from 1 to 5.",
    "Perceived_AI_Dependency": "Self-rated dependency, from 1 (low) to 10 (high). The same measure is excluded from the outcome selector.",
    "Anxiety_Level_During_Exams": "Self-reported exam anxiety, from 1 to 10; measurement validation is undocumented.",
    "Burnout_Risk_Level": "The supplied Low, Medium, and High burnout labels are comparison groups, not diagnoses or causal explanations.",
}
LABELS = {
    "GPA_Change": "GPA change (points)", "Skill_Retention_Score": "Skill retention score",
    "Perceived_AI_Dependency": "AI dependency (1–10)", "Weekly_GenAI_Hours": "Weekly AI hours",
    "Traditional_Study_Hours": "Weekly non-AI study hours", "Major_Category": "Major",
    "Year_of_Study": "Year of study", "Primary_Use_Case": "Primary AI use case",
    "Prompt_Engineering_Skill": "Prompting skill", "Institutional_Policy": "Institutional policy",
    "Burnout_Risk_Level": "Burnout category", "Pre_Semester_GPA": "Pre-semester GPA",
    "Post_Semester_GPA": "Post-semester GPA", "Anxiety_Level_During_Exams": "Exam anxiety (1–10)",
    "Paid_Subscription": "Paid AI subscription", "Tool_Diversity": "Number of AI tools",
}


def friendly(value):
    return LABELS.get(value, str(value).replace("_", " "))


def load_data(path=DATA_PATH):
    return pd.read_csv(path)


def validate_data(df):
    """Report issues; do not silently impute, drop, clamp, or recode observations."""
    checks = []

    def add(check, count, detail):
        checks.append({"Check": check, "Issues": int(count), "Status": "Pass" if count == 0 else "Review", "Detail": detail})

    missing = sorted(set(REQUIRED) - set(df.columns))
    add("Required columns", len(missing), ", ".join(missing) or "All 16 required columns present")
    add("Nonempty dataset", int(df.empty), f"{len(df):,} rows")
    add("Missing values", df.isna().sum().sum(), "Missing cells across all columns")
    add("Duplicate rows", df.duplicated().sum(), "Exact duplicates; original records retained")
    if "Student_ID" in df:
        add("Duplicate student IDs", df.Student_ID.duplicated().sum(), "Expected one row per student")
    for column, (low, high) in RANGES.items():
        if column not in df:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        invalid = values.isna() | ~np.isfinite(values) | ~values.between(low, high)
        add(f"Range: {friendly(column)}", invalid.sum(), f"Expected {low}–{high}; not automatically corrected")
    for column in INTEGER_COLUMNS:
        if column in df:
            values = pd.to_numeric(df[column], errors="coerce")
            invalid = values.isna() | ~np.isfinite(values) | (values % 1 != 0)
            if column == "Student_ID":
                invalid |= values <= 0
            add(f"Integer: {column}", invalid.sum(), "Finite whole numbers; student IDs must be positive")
    for column, choices in CATEGORIES.items():
        if column in df:
            add(f"Categories: {friendly(column)}", (~df[column].isin(choices)).sum(), "Unexpected or missing labels require review")
    if "Paid_Subscription" in df:
        values = df.Paid_Subscription.astype(str).str.lower()
        add("Subscription boolean", (~values.isin(["true", "false"])).sum(), "True/False values only")
    return pd.DataFrame(checks)


def prepare_data(raw):
    report = validate_data(raw)
    failed = report.loc[report.Issues > 0, "Check"].tolist()
    if failed:
        raise ValueError("Data validation needs review: " + "; ".join(failed))
    df = raw.copy(deep=True)
    for column in RANGES:
        df[column] = pd.to_numeric(df[column])
    df["Paid_Subscription"] = df.Paid_Subscription.astype(str).str.lower().eq("true")
    df["GPA_Change"] = df.Post_Semester_GPA - df.Pre_Semester_GPA
    return df


def filter_data(df, selections=None, hours=None):
    mask = pd.Series(True, index=df.index)
    for column, values in (selections or {}).items():
        mask &= df[column].isin(values)
    if hours is not None:
        mask &= df.Weekly_GenAI_Hours.between(*hours, inclusive="both")
    return df.loc[mask].copy()


def selection_comparison(group_a, group_b):
    """Independent descriptive summaries. Empty groups have no outcome estimate."""
    measures = [
        ("Records", "count", None),
        ("Mean GPA change", "GPA points", "GPA_Change"),
        ("Mean skill retention", "score / 100", "Skill_Retention_Score"),
        ("High burnout share", "% (difference in percentage points)", None),
        ("Mean baseline GPA", "GPA points", "Pre_Semester_GPA"),
        ("Mean weekly AI hours", "hours / week", "Weekly_GenAI_Hours"),
        ("Mean non-AI study hours", "hours / week", "Traditional_Study_Hours"),
        ("Mean AI dependency", "score / 10", "Perceived_AI_Dependency"),
    ]
    rows = []
    for label, unit, column in measures:
        values = []
        for df in [group_a, group_b]:
            if label == "Records":
                value = len(df)
            elif df.empty:
                value = np.nan
            elif label == "High burnout share":
                value = 100 * df.Burnout_Risk_Level.eq("High").mean()
            else:
                value = df[column].mean()
            values.append(value)
        rows.append({"Measure": label, "Unit": unit, "Group A": values[0], "Group B": values[1], "B minus A": values[1] - values[0]})
    return pd.DataFrame(rows)


def selection_overlap(group_a, group_b):
    """Count shared student IDs; a shared record contributes to each group's stats."""
    return len(set(group_a.Student_ID) & set(group_b.Student_ID))


def correlation_table(df):
    records = []
    for outcome in ["GPA_Change", "Skill_Retention_Score"]:
        for method in ["pearson", "spearman"]:
            pair = df[["Weekly_GenAI_Hours", outcome]].dropna()
            r = np.nan
            if len(pair) >= 3 and pair.nunique().min() > 1:
                # Ranking then Pearson avoids an optional scipy dependency.
                values = pair.rank() if method == "spearman" else pair
                r = values.iloc[:, 0].corr(values.iloc[:, 1])
            records.append({"Outcome": friendly(outcome), "Method": method.title(), "Correlation": r, "Records": len(pair)})
    return pd.DataFrame(records)


def group_summary(df, group, outcome):
    if group == outcome:
        raise ValueError("Choose an outcome different from the grouping factor.")
    # Only alter the temporary grouping key; the original measurements stay intact.
    values = df[group]
    if group in COMPARISON_BINS:
        bins, labels = COMPARISON_BINS[group]
        values = pd.cut(values, bins=bins, labels=labels, right=False)
    elif group == "Paid_Subscription":
        values = pd.Categorical(values.map({False: "No paid subscription", True: "Paid subscription"}),
                                categories=["No paid subscription", "Paid subscription"], ordered=True)
    elif group in ["Year_of_Study", "Prompt_Engineering_Skill", "Burnout_Risk_Level"]:
        values = pd.Categorical(values, categories=CATEGORIES[group], ordered=True)
    result = df.assign(**{group: values}).groupby(group, observed=True, sort=True)[outcome].agg(
        n="count", mean="mean", median="median", sd="std").reset_index()
    return result


def burnout_summary(df, group):
    counts = pd.crosstab(df[group], df.Burnout_Risk_Level).reindex(columns=BURNOUT_ORDER, fill_value=0)
    if group == "Year_of_Study":
        counts = counts.reindex([v for v in YEAR_ORDER if v in counts.index])
    total = counts.sum(axis=1)
    result = counts.reset_index().melt(id_vars=group, var_name="Burnout category", value_name="Count")
    result["Group size"] = result[group].map(total)
    result["Percent"] = result.Count.div(result["Group size"]).mul(100)
    return result


def hours_summary(df, outcome):
    """Fixed display bins only; these boundaries are not learned risk thresholds."""
    copy = df.copy()
    copy["Hours band"] = pd.cut(copy.Weekly_GenAI_Hours, [0, 5, 10, 15, 20, 25, 30, 35, 40.001], right=False,
                                labels=["0–<5", "5–<10", "10–<15", "15–<20", "20–<25", "25–<30", "30–<35", "35–40"])
    return group_summary(copy, "Hours band", outcome)
