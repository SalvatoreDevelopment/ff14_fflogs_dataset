from __future__ import annotations

import argparse
from ff14_dataset.config import load_settings
from ff14_dataset.scraper.jobguide import fetch_jobguide_html, parse_job_actions, get_job_abbr
from ff14_dataset.tagging.actions import derive_tags
from pathlib import Path
import orjson
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(prog="ff14ds", description="FFXIV dataset builder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="Show versions")
    sub.add_parser("paths", help="Show important paths")

    p_build_tags = sub.add_parser(
        "build-actions-tags",
        help="Scrape Job Guide and build consolidated actions with tags",
    )
    p_build_tags.add_argument("--jobs", nargs="+", default=["paladin"], help="Job slugs to scrape (e.g. paladin)")
    p_build_tags.add_argument(
        "--base",
        default="config/presets/actions-7.3x-combat-all.json",
        help="Base actions JSON to merge",
    )
    p_build_tags.add_argument(
        "--out",
        default="config/presets/actions-7.3x-combat-all+tags.json",
        help="Output JSON path",
    )
    p_build_tags.add_argument(
        "--delete-old",
        action="store_true",
        help="Delete legacy preset files after generating the new one",
    )

    args = parser.parse_args()

    if args.command == "version":
        s = load_settings()
        print(f"dataset_version={s.app.dataset_version} schema_version={s.app.schema_version}")
    elif args.command == "paths":
        s = load_settings()
        print(f"data_root={s.paths.data_root}")
    elif args.command == "build-actions-tags":
        base_path = Path(args.base)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        base = orjson.loads(base_path.read_bytes())
        base_records: list[dict[str, Any]] = base.get("records", [])

        # Scrape each requested job
        scraped_by_job: dict[str, dict[str, dict[str, str | None]]] = {}
        for job_slug in args.jobs:
            html = fetch_jobguide_html(job_slug)
            actions = parse_job_actions(html)
            # Build name->details map (name_en normalized)
            scraped_by_job[job_slug] = {a.name_en: {
                "cast": a.cast,
                "recast": a.recast,
                "range": a.range,
                "radius": a.radius,
                "tooltip": a.tooltip,
            } for a in actions}

        # Merge: for records in base matching job_abbr, apply derived tags
        updated_records: list[dict[str, Any]] = []
        jobs_abbr = {get_job_abbr(j): j for j in args.jobs}
        for rec in base_records:
            job_abbr = rec.get("job_abbr")
            name_en = rec.get("name_en") or rec.get("name")
            category = rec.get("category")

            # Keep original tags if present
            tags = list(rec.get("tags") or [])

            if job_abbr in jobs_abbr and name_en:
                job_slug = jobs_abbr[job_abbr]
                details = scraped_by_job.get(job_slug, {}).get(name_en)
                if details:
                    derived = derive_tags(
                        name_en=name_en,
                        tooltip=details.get("tooltip"),
                        category=category,
                        cast=details.get("cast"),
                        recast=details.get("recast"),
                    )
                    # merge unique
                    merged = sorted({*tags, *derived})
                    rec = {**rec, "tags": merged}

            updated_records.append(rec)

        # Write output
        out_doc = {
            "schema": base.get("schema", "ff14_dataset.actions/1"),
            "game_patch": base.get("game_patch", "7.3x"),
            "language": base.get("language", "en"),
            "generated_at": base.get("generated_at"),
            "records": updated_records,
        }
        out_path.write_bytes(orjson.dumps(out_doc))
        print(f"Wrote {out_path} ({len(updated_records)} records)")

        if args.delete_old:
            # Remove known legacy preset files if they exist (except the new one)
            to_delete = [
                Path("config/presets/actions-7.3x.json"),
                Path("config/presets/actions-7.3x-combat.json"),
                Path("config/presets/actions-7.3x-combat-all.json"),
                Path("config/presets/actions-7.3x-combat-all+tags-sch.json"),
            ]
            for p in to_delete:
                try:
                    if p.resolve() == out_path.resolve():
                        continue
                except Exception:
                    pass
                if p.exists():
                    p.unlink()
                    print(f"Deleted {p}")
