from __future__ import annotations

from pathlib import Path
import duckdb

from ff14_dataset.config import Settings
from ff14_dataset.io.storage import ensure_paths


def connect_duck(settings: Settings) -> duckdb.DuckDBPyConnection:
    paths = ensure_paths(settings)
    con = duckdb.connect(str(paths.duckdb_file))
    # Suggested pragmas for local analytics
    con.execute("PRAGMA threads=auto;")
    con.execute("PRAGMA memory_limit='60%';")
    return con


def register_parquet_view(con: duckdb.DuckDBPyConnection, name: str, glob_path: Path) -> None:
    # Glob path should be like /.../staging/**.parquet
    con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM parquet_scan('{glob_path.as_posix()}');")

