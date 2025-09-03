Architectural Decisions (ADR-0001)

Context
- Objective: ML dataset to learn optimal class play (start with SAM) from FF Logs.
- Scope: raid/savage/ultimate, patch 7.3x, multi-fight selection via filters.

Decisions
1) Storage: Parquet + DuckDB views. Rationale: fast local analytics, simple ops.
2) Layers: raw → staging → curated/features with lineage and versioning.
3) Time model: retain event stream + build tick sequences at 100 ms.
4) Orchestration: Prefect (Windows-friendly). Airflow can be considered later.
5) GUI: PySide6, launched via Poetry; package .exe at the end.
6) Quality filters: kills only and percentile ≥95% for ML mode; exploratory toggle can relax.
7) Partitions: game_patch/encounter_name/job/report_date=YYYY-MM.

Status
- Accepted. Initial skeleton implements configuration and placeholders.

