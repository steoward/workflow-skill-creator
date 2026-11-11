"""Data Processing Pipeline Template.

Use this pattern when distilling workflows that ingest, transform, filter,
or analyze local files (CSV, TSV, JSON, JSONL, FASTA, logs, or reports).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List


class DataPipeline:
    def process_records(self, input_file: str, filter_key: str | None = None, min_value: float = 0.0) -> list[dict]:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        results = []
        with open(input_file, "r", encoding="utf-8") as f:
            if input_file.endswith(".json"):
                data = json.load(f)
                records = data if isinstance(data, list) else data.get("records", [data])
            elif input_file.endswith(".csv") or input_file.endswith(".tsv"):
                delimiter = "\t" if input_file.endswith(".tsv") else ","
                reader = csv.DictReader(f, delimiter=delimiter)
                records = list(reader)
            else:
                records = [{"line_no": i, "content": line.strip()} for i, line in enumerate(f, start=1)]

        for rec in records:
            if filter_key and filter_key in rec:
                try:
                    val = float(rec[filter_key])
                    if val < min_value:
                        continue
                except (ValueError, TypeError):
                    pass
            results.append(rec)

        return results


def main():
    parser = argparse.ArgumentParser(description="Data processing pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: transform
    p_trans = subparsers.add_parser("transform", help="Filter and transform structured records")
    p_trans.add_argument("--input-file", required=True, help="Path to input data file")
    p_trans.add_argument("--filter-key", help="Key or column to filter by")
    p_trans.add_argument("--min-value", type=float, default=0.0, help="Minimum threshold value")
    p_trans.add_argument("--output", required=True, help="Destination JSON file path")

    args = parser.parse_args()
    pipeline = DataPipeline()

    try:
        if args.command == "transform":
            transformed = pipeline.process_records(args.input_file, args.filter_key, args.min_value)
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({"total": len(transformed), "records": transformed}, f, indent=2)
            print(f"Success! Processed {len(transformed)} records to: {args.output}")
        else:
            sys.exit(f"Unknown command: {args.command}")
    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
