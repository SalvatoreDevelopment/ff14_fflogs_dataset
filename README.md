ff14_dataset

Dataset builder for FFXIV combat logs aimed at ML training. Focused on event-driven timelines and tick-based state reconstruction. Includes a Windows GUI (PySide6) to ingest, process, and preview data.

Key points
- Sources: FF Logs v2 (GraphQL) + XIVAPI mapping.
- Scope: raid/savage/ultimate, patch 7.3x; multi-fight with filters.
- Layers: raw → staging → curated/features in Parquet with DuckDB views.
- Labels: next GCD action, oGCD list per weave window, time-to-next-action; action mask.
- Quality filters: kills only and percentile ≥95% (ML mode), toggleable in exploratory mode.
- Orchestration: Prefect flows wrapped by a PySide6 GUI.

Quick start (no data fetch)
- Create `.env` from `.env.example` and fill FF Logs credentials.
- Launch GUI: `poetry run ff14ds-gui` (once dependencies installed).

Project status
- This is a skeleton. Ingestion, normalization, metrics, features, and GUI wiring are scaffolded but not fully implemented yet.

