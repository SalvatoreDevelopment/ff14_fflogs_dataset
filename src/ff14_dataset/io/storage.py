from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ff14_dataset.config import Settings
from ff14_dataset.utils.slug import slugify


Layer = Literal["raw", "staging", "curated"]


@dataclass
class DataPaths:
    root: Path
    raw: Path
    staging: Path
    curated: Path
    duckdb_file: Path


def ensure_paths(settings: Settings) -> DataPaths:
    root = settings.paths.data_root
    raw = root / settings.paths.raw
    staging = root / settings.paths.staging
    curated = root / settings.paths.curated
    duck = root / settings.paths.duckdb_file
    for p in (raw, staging, curated):
        p.mkdir(parents=True, exist_ok=True)
    return DataPaths(root=root, raw=raw, staging=staging, curated=curated, duckdb_file=duck)


def partition_path(
    settings: Settings,
    layer: Layer,
    game_patch: str,
    encounter_name: str,
    job: str,
    report_yyyymm: str,
) -> Path:
    base = ensure_paths(settings)
    enc = slugify(encounter_name)
    sub = Path(game_patch) / enc / job / f"report_date={report_yyyymm}"
    if layer == "raw":
        return base.raw / sub
    if layer == "staging":
        return base.staging / sub
    return base.curated / sub

