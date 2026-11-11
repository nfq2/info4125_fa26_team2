# AI & Student Learning Dashboard

A Streamlit dashboard for exploring how students' AI usage relates to GPA changes, skill retention, and wellbeing. Filter the dataset, compare student groups, and view interactive charts to explore patterns in student learning.

## Setup

From the project folder, use Python 3.12 and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Launch

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Data source

[Impact of AI on Students — Kaggle](https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students)
