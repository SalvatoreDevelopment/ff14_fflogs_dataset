from __future__ import annotations

import argparse
from ff14_dataset.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="ff14ds", description="FFXIV dataset builder CLI")
    parser.add_argument("command", choices=["version", "paths"], help="Command to run")
    args = parser.parse_args()

    if args.command == "version":
        s = load_settings()
        print(f"dataset_version={s.app.dataset_version} schema_version={s.app.schema_version}")
    elif args.command == "paths":
        s = load_settings()
        print(f"data_root={s.paths.data_root}")

