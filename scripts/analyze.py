"""Produce reproducible derived outputs, without changing the source CSV."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analysis import DATA_PATH, SOURCE_URL, load_data, validate_data, prepare_data, correlation_table, group_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = load_data()
    report = validate_data(raw)
    report.to_csv(args.output_dir / "validation_report.csv", index=False)
    df = prepare_data(raw)
    df.to_csv(args.output_dir / "prepared_student_data.csv", index=False)
    correlation_table(df).to_csv(args.output_dir / "correlations.csv", index=False)
    for outcome in ["GPA_Change", "Skill_Retention_Score"]:
        group_summary(df, "Primary_Use_Case", outcome).to_csv(args.output_dir / f"use_case_{outcome}.csv", index=False)
    metadata = {"source_url": SOURCE_URL, "source_sha256": hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
                "rows": len(df), "original_columns": len(raw.columns), "removed_rows": 0,
                "imputed_cells": 0, "provenance": "Unverified collection methodology and real-versus-synthetic status"}
    (args.output_dir / "analysis_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Validated {len(df):,} records. Outputs: {args.output_dir}")
    print(correlation_table(df).to_string(index=False))


if __name__ == "__main__":
    main()
