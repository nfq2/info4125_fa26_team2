from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_additional_comparison_factors_render_and_use_filtered_records():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.multiselect(key="major_filter").set_value(["Arts"]).run()
    app.selectbox(key="compare_outcome").select("Perceived_AI_Dependency").run()
    for factor in ["Paid_Subscription", "Tool_Diversity", "Weekly_GenAI_Hours", "Traditional_Study_Hours",
                   "Perceived_AI_Dependency", "Anxiety_Level_During_Exams", "Burnout_Risk_Level", "Pre_Semester_GPA"]:
        app.selectbox(key="compare_group").select(factor).run()
        assert not app.exception, factor
        assert app.selectbox(key="compare_outcome").value != factor
        # The downloadable table's counts must total the selected group, not the whole dataset.
        tables = [element.value for element in app.dataframe if "Records" in element.value.columns and "Mean" in element.value.columns]
        assert len(tables) == 1
        assert tables[0]["Records"].sum() == 5933


def test_dashboard_filter_compare_empty_and_reset():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert app.metric[0].value == "50,000"
    app.multiselect(key="major_filter").set_value(["STEM"]).run()
    assert not app.exception
    assert app.metric[0].value == "15,059"
    app.selectbox(key="compare_group").select("Year_of_Study").run()
    app.selectbox(key="hours_outcome").select("Skill_Retention_Score").run()
    app.slider(key="hours_filter").set_value((10.0, 20.0)).run()
    assert not app.exception
    assert 0 < int(app.metric[0].value.replace(",", "")) < 15059
    app.multiselect(key="major_filter").set_value([]).run()
    assert not app.exception
    assert any("No records" in message.value for message in app.info)
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "50,000"


def test_independent_selections_persist_and_handle_empty_groups():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    app.multiselect(key="major_filter").set_value(["STEM"]).run()
    app.radio(key="view_mode").set_value("Compare selections").run()
    assert not app.exception
    group_b_count = app.metric[1].value
    app.multiselect(key="selection_a_major").set_value(["Arts"]).run()
    assert not app.exception
    assert app.metric[1].value == group_b_count
    app.button(key="copy_exploration_a").click().run()
    assert app.multiselect(key="selection_a_major").value == ["STEM"]
    assert app.metric[0].value == "15,059"
    app.radio(key="view_mode").set_value("Explore a selection").run()
    assert app.multiselect(key="major_filter").value == ["STEM"]
    app.radio(key="view_mode").set_value("Compare selections").run()
    assert app.multiselect(key="selection_a_major").value == ["STEM"]
    app.button(key="copy_exploration_b").click().run()
    assert any("15,059 records belong to both" in message.value for message in app.info)
    app.multiselect(key="selection_a_major").set_value([]).run()
    assert not app.exception
    assert app.metric[0].value == "0"
    assert app.metric[1].value == "15,059"
    assert any("Group A has no matching records" in message.value for message in app.info)
    app.button(key="reset_comparison").click().run()
    assert not app.exception
    assert app.slider(key="selection_a_hours").value == (0.0, 5.0)
    assert app.slider(key="selection_b_hours").value == (10.0, 20.0)
