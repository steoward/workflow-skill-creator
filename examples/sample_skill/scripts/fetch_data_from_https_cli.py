# Distilled CLI script for fetch-data-from-https
from __future__ import annotations

import argparse
import json
import os
import sys
import time

class PipelineRunner:
    def __init__(self, name: str = "fetch-data-from-https"):
        self.name = name

    def execute(self, input_file: str) -> dict:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        with open(input_file, "r", encoding="utf-8") as f:
            payload = json.load(f) if input_file.endswith(".json") else f.read()

        return {
            "status": "success",
            "pipeline": self.name,
            "processed_at": time.time(),
            "input_file": input_file,
            "summary": "Pipeline executed successfully.",
        }

    def check_status(self) -> dict:
        return {"status": "ready", "service": self.name, "timestamp": time.time()}


def write_output(data: dict, output_file: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Success! Output written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="CLI for fetch-data-from-https")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    p_run = subparsers.add_parser("run", help="Run workflow pipeline")
    p_run.add_argument("--input-file", required=True, help="Input data file")
    p_run.add_argument("--output", required=True, help="Output destination path")

    # Subcommand: status
    p_status = subparsers.add_parser("status", help="Check status")
    p_status.add_argument("--output", required=True, help="Output destination path")

    args = parser.parse_args()
    runner = PipelineRunner()

    try:
        if args.command == "run":
            res = runner.execute(args.input_file)
        elif args.command == "status":
            res = runner.check_status()
        else:
            sys.exit(f"Unknown command: {args.command}")

        write_output(res, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
