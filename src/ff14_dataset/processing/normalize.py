from __future__ import annotations

"""Transform raw JSON into normalized staging Parquet (skeleton)."""

from pathlib import Path

import polars as pl


def normalize_events(raw_files: list[Path]) -> pl.DataFrame:
    # Placeholder: return empty schema with expected columns
    return pl.DataFrame(
        schema={
            "event_id": pl.Int64,
            "fight_id": pl.Int64,
            "report_id": pl.Utf8,
            "ts_ms": pl.Int64,
            "event_type": pl.Utf8,
            "source_id": pl.Int64,
            "target_id": pl.Int64,
            "ability_id": pl.Int64,
            "amount": pl.Int64,
            "crit": pl.Boolean,
            "dh": pl.Boolean,
            "x": pl.Float64,
            "y": pl.Float64,
        }
    )

