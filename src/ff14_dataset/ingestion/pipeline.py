from __future__ import annotations

"""
High-level ingestion pipeline entrypoints (skeleton).

Responsibilities
- Accept filters (encounter names/IDs, patches, percentile, jobs)
- Query FF Logs v2 for reports/fights/events with pagination
- Save raw JSON (events + metadata) partitioned by patch/encounter/job/report_date
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import orjson

from ff14_dataset.config import Settings
from ff14_dataset.io.storage import partition_path


@dataclass
class IngestionRequest:
    encounters: list[str]
    patches: list[str]
    jobs: list[str]
    min_percentile: int
    kills_only: bool


def save_raw_json(base: Path, name: str, payload: dict) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    p = base / f"{name}.json"
    p.write_bytes(orjson.dumps(payload))
    return p


def compute_report_month(ts_ms: int) -> str:
    dt = datetime.utcfromtimestamp(ts_ms / 1000.0)
    return f"{dt.year:04d}-{dt.month:02d}"


async def ingest_encounters(settings: Settings, req: IngestionRequest) -> None:
    """Skeleton: this will use FFLogsClient to pull reports/fights/events and save raw JSON.
    Implementation intentionally omitted here (to be filled in subsequent steps).
    """
    # Example of target path computation (placeholder values)
    for enc in req.encounters or ["aac-cruiserweight-m4-savage"]:
        report_month = "2025-01"
        out = partition_path(settings, "raw", settings.app.game_patch, enc, req.jobs[0] if req.jobs else "SAM", report_month)
        save_raw_json(out, "_placeholder_readme", {"note": "raw json files will be stored here"})

