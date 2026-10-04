import pandas as pd
import pytest
from src.analysis import load_data, prepare_data, validate_data, filter_data, burnout_summary, correlation_table, hours_summary
from src.analysis import selection_comparison, selection_overlap
from src.analysis import group_summary


@pytest.fixture
def raw():
    return load_data().head(5).copy()


def test_preparation_preserves_source_and_gpa_sign(raw):
    original = raw.copy(deep=True)
    raw.loc[raw.index[0], ["Pre_Semester_GPA", "Post_Semester_GPA"]] = [3.0, 3.2]
    before = raw.copy(deep=True)
    prepared = prepare_data(raw)
    assert prepared.iloc[0].GPA_Change == pytest.approx(.2)
    pd.testing.assert_frame_equal(raw, before)
    assert len(prepared) == len(original)
    assert prepared.Paid_Subscription.dtype == bool


@pytest.mark.parametrize("column,value", [("Post_Semester_GPA", 4.1), ("Perceived_AI_Dependency", 11), ("Tool_Diversity", 1.5), ("Weekly_GenAI_Hours", -1), ("Skill_Retention_Score", float("inf")), ("Paid_Subscription", "maybe"), ("Major_Category", "STEM ")])
def test_invalid_data_cannot_silently_enter_analysis(raw, column, value):
    raw[column] = raw[column].astype(object)
    raw.loc[raw.index[0], column] = value
    assert (validate_data(raw).Issues > 0).any()
    with pytest.raises(ValueError):
        prepare_data(raw)


def test_missing_schema_and_duplicates_rejected(raw):
    with pytest.raises(ValueError):
        prepare_data(raw.drop(columns="Post_Semester_GPA"))
    with pytest.raises(ValueError):
        prepare_data(pd.concat([raw, raw.iloc[[0]]]))


def test_filter_boundaries_and_empty_selection(raw):
    data = prepare_data(raw)
    data["Weekly_GenAI_Hours"] = [0, 5, 10, 20, 40]
    assert filter_data(data, hours=(5, 20)).Weekly_GenAI_Hours.tolist() == [5, 10, 20]
    assert filter_data(data, {"Major_Category": []}).empty
    assert hours_summary(data, "GPA_Change").n.sum() == 5


def test_burnout_uses_within_group_denominator(raw):
    data = prepare_data(raw)
    data["Major_Category"] = ["Arts", "Arts", "STEM", "STEM", "STEM"]
    data["Burnout_Risk_Level"] = ["High", "Low", "High", "High", "High"]
    summary = burnout_summary(data, "Major_Category")
    high = summary[summary["Burnout category"] == "High"].set_index("Major_Category")
    assert high.loc["Arts", "Percent"] == 50
    assert high.loc["STEM", "Percent"] == 100
    assert summary.groupby("Major_Category").Percent.sum().eq(100).all()


def test_constant_or_tiny_groups_have_undefined_correlations(raw):
    data = prepare_data(raw)
    data["Weekly_GenAI_Hours"] = 5
    assert correlation_table(data).Correlation.isna().all()
    assert correlation_table(data.head(1)).Correlation.isna().all()


def test_selection_comparison_uses_independent_denominators_and_overlap(raw):
    df = prepare_data(raw)
    df["GPA_Change"] = [.1, .3, -.2, -.4, .5]
    df["Burnout_Risk_Level"] = ["High", "Low", "High", "High", "Low"]
    a, b = df.iloc[:2], df.iloc[1:4]
    result = selection_comparison(a, b).set_index("Measure")
    assert result.loc["Records", "Group A"] == 2
    assert result.loc["Records", "Group B"] == 3
    assert result.loc["Mean GPA change", "Group A"] == pytest.approx(.2)
    assert result.loc["Mean GPA change", "B minus A"] == pytest.approx(-.3)
    assert result.loc["High burnout share", "B minus A"] == pytest.approx(100 * (2 / 3 - .5))
    assert selection_overlap(a, b) == 1
    empty = selection_comparison(a, df.iloc[:0]).set_index("Measure")
    assert empty.loc["Records", "Group B"] == 0
    assert pd.isna(empty.loc["High burnout share", "Group B"])
    assert pd.isna(empty.loc["Mean GPA change", "B minus A"])


@pytest.mark.parametrize("factor,values,labels,counts", [
    ("Weekly_GenAI_Hours", [0, 4.99, 5, 35, 40], ["0–<5", "5–<10", "35–40"], [2, 1, 2]),
    ("Traditional_Study_Hours", [0, 5, 29.99, 30, 168], ["0–<5", "5–<10", "25–<30", "30+"], [1, 1, 1, 2]),
    ("Pre_Semester_GPA", [0, 2, 2.5, 3, 3.5, 4], ["0–<2.0", "2.0–<2.5", "2.5–<3.0", "3.0–<3.5", "3.5–4.0"], [1, 1, 1, 1, 2]),
    ("Paid_Subscription", [True, False, False], ["No paid subscription", "Paid subscription"], [2, 1]),
    ("Perceived_AI_Dependency", [10, 2, 1, 2], [1, 2, 10], [1, 2, 1]),
    ("Burnout_Risk_Level", ["High", "Low", "Medium"], ["Low", "Medium", "High"], [1, 1, 1]),
])
def test_comparison_factor_boundaries_order_and_source_preservation(factor, values, labels, counts):
    df = pd.DataFrame({factor: values, "GPA_Change": [.25] * len(values)})
    original = df.copy(deep=True)
    table = group_summary(df, factor, "GPA_Change")
    assert table[factor].tolist() == labels
    assert table.n.tolist() == counts
    assert table.n.sum() == len(df)
    assert table["mean"].eq(.25).all()
    pd.testing.assert_frame_equal(df, original)
