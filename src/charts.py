"""Figures shared by the notebook and dashboard."""
import plotly.express as px
import plotly.graph_objects as go
from src.analysis import friendly, group_summary, burnout_summary, hours_summary, LABELS

BLUE = "#2563EB"
TEAL = "#087F8C"
COLORS = {"Low": "#0F766E", "Medium": "#D97706", "High": "#BE123C"}


def style(fig):
    fig.update_layout(template="plotly_white", font=dict(family="Arial, sans-serif", size=14, color="#172554"),
                      margin=dict(l=15, r=20, t=35, b=25), height=400,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend_title_text="", colorway=[BLUE, TEAL, "#7C3AED", "#D97706", "#BE123C"])
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2E8F0")
    return fig


def hours_plot(df, outcome):
    table = hours_summary(df, outcome)
    fig = px.scatter(table, x="Hours band", y="mean", size="n", size_max=28,
                     hover_data={"n": True, "mean": ":.3f", "median": ":.3f", "sd": ":.3f"},
                     labels={"mean": friendly(outcome), "n": "Records", "sd": "Standard deviation", "median": "Median"})
    fig.update_traces(marker_color=BLUE)
    if outcome == "GPA_Change":
        fig.add_hline(y=0, line_dash="dot", line_color="#64748B")
    return style(fig)


def comparison_plot(df, group, outcome):
    table = group_summary(df, group, outcome)
    table["Group"] = table[group].astype(str).map(friendly)
    fig = px.bar(table, y="Group", x="mean", orientation="h", text="n",
                 hover_data={"mean": ":.3f", "median": ":.3f", "sd": ":.3f", "n": True},
                 labels={"mean": friendly(outcome), "Group": friendly(group), "n": "Records", "sd": "Standard deviation"})
    fig.update_traces(marker_color=TEAL, texttemplate="n=%{text:,}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(autorange="reversed", type="category", categoryorder="array", categoryarray=table["Group"].tolist())
    style(fig)
    fig.update_layout(height=max(400, 46 * len(table) + 90), margin=dict(r=85))
    return fig


def burnout_plot(df, group):
    table = burnout_summary(df, group)
    table["Group"] = table[group].astype(str).map(friendly)
    fig = px.bar(table, x="Group", y="Percent", color="Burnout category", color_discrete_map=COLORS,
                 category_orders={"Burnout category": ["Low", "Medium", "High"]},
                 hover_data={"Count": True, "Group size": True, "Percent": ":.1f"}, labels={"Group": friendly(group)})
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return style(fig)


def gpa_distribution(df):
    fig = px.histogram(df, x="GPA_Change", nbins=60, labels=LABELS, color_discrete_sequence=[BLUE])
    fig.add_vline(x=0, line_dash="dot", line_color="#64748B")
    fig.update_yaxes(title="Records")
    return style(fig)


def relationship_plot(df, outcome):
    sample = df.sample(min(len(df), 3000), random_state=42)
    fig = px.scatter(sample, x="Weekly_GenAI_Hours", y=outcome, color="Major_Category", opacity=.4,
                     labels=LABELS, render_mode="webgl")
    fig.update_traces(marker_size=5)
    return style(fig)


def correlation_plot(df):
    columns = ["Weekly_GenAI_Hours", "Traditional_Study_Hours", "Perceived_AI_Dependency", "GPA_Change", "Skill_Retention_Score", "Anxiety_Level_During_Exams"]
    corr = df[columns].corr()
    fig = go.Figure(go.Heatmap(z=corr.values, x=[friendly(c) for c in columns], y=[friendly(c) for c in columns],
                             zmin=-1, zmax=1, zmid=0, colorscale="RdBu", reversescale=True,
                             text=corr.round(2).values, texttemplate="%{text}", hovertemplate="%{x}<br>%{y}<br>r=%{z:.3f}<extra></extra>"))
    return style(fig)
