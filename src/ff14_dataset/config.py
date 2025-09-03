from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    dataset_version: str
    schema_version: str
    game_patch: str
    tick_ms: int
    language: str
    exploratory_mode: bool


@dataclass
class PathsConfig:
    data_root: Path
    raw: str
    staging: str
    curated: str
    duckdb_file: str
    presets_dir: Path


@dataclass
class IngestionQuality:
    kills_only: bool
    min_percentile: int


@dataclass
class IngestionFilters:
    jobs: list[str]
    encounters: list[str]
    patches: list[str]


@dataclass
class IngestionConfig:
    concurrency: int
    sleep_ms: int
    quality_filters: IngestionQuality
    filters: IngestionFilters


@dataclass
class FeaturesLabels:
    next_gcd: bool
    ogcd_list: bool
    time_to_next_action: bool


@dataclass
class FeaturesConfig:
    labels: FeaturesLabels
    include_action_mask: bool


@dataclass
class PartitionsConfig:
    scheme: str  # "game_patch/encounter_name/job/report_date"


@dataclass
class Settings:
    app: AppConfig
    paths: PathsConfig
    ingestion: IngestionConfig
    features: FeaturesConfig
    partitions: PartitionsConfig


def _deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _deep_update(base[k], v)
        else:
            base[k] = v
    return base


def load_settings(config_path: str | Path = "config/default.yaml") -> Settings:
    load_dotenv(override=False)

    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)

    # Allow overrides from env for some keys
    env_overrides: Dict[str, Any] = {}
    data_root = os.getenv("DATA_ROOT")
    if data_root:
        env_overrides.setdefault("paths", {})["data_root"] = data_root
    conc = os.getenv("FFLOGS_CONCURRENCY")
    sleep_ms = os.getenv("FFLOGS_SLEEP_MS")
    if conc or sleep_ms:
        env_overrides.setdefault("ingestion", {})
        if conc:
            env_overrides["ingestion"]["concurrency"] = int(conc)
        if sleep_ms:
            env_overrides["ingestion"]["sleep_ms"] = int(sleep_ms)

    if env_overrides:
        raw_cfg = _deep_update(raw_cfg, env_overrides)

    app = AppConfig(**raw_cfg["app"])  # type: ignore[arg-type]
    paths = raw_cfg["paths"]
    paths_cfg = PathsConfig(
        data_root=Path(paths["data_root"]).resolve(),
        raw=paths["raw"],
        staging=paths["staging"],
        curated=paths["curated"],
        duckdb_file=paths["duckdb_file"],
        presets_dir=Path(paths["presets_dir"]).resolve(),
    )
    iq = IngestionQuality(**raw_cfg["ingestion"]["quality_filters"])  # type: ignore[arg-type]
    ifilt = IngestionFilters(**raw_cfg["ingestion"]["filters"])  # type: ignore[arg-type]
    ing = IngestionConfig(
        concurrency=int(raw_cfg["ingestion"]["concurrency"]),
        sleep_ms=int(raw_cfg["ingestion"]["sleep_ms"]),
        quality_filters=iq,
        filters=ifilt,
    )
    fl = FeaturesLabels(**raw_cfg["features"]["labels"])  # type: ignore[arg-type]
    feat = FeaturesConfig(labels=fl, include_action_mask=raw_cfg["features"]["include_action_mask"])  # type: ignore[arg-type]
    part = PartitionsConfig(**raw_cfg["partitions"])  # type: ignore[arg-type]

    return Settings(app=app, paths=paths_cfg, ingestion=ing, features=feat, partitions=part)

