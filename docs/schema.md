Schema overview (v0.1.0)

- fights: fight-level metadata with lineage
  - fight_id, report_id, encounter_id, encounter_name, zone_id, boss_name, pull_ts_utc_ms,
    duration_ms, kill, game_patch, source_hash

- participants: actors in a fight
  - participant_id, fight_id, actor_id, name, job, role, server, party_index, gear_score

- events (event-driven, source: FF Logs)
  - event_id, fight_id, report_id, ts_ms, event_type (cast/damage/heal/buff/debuff),
    source_id, target_id, ability_id, amount, overheal, overkill, crit, dh, hit_type,
    absorbed, stack, status_id, resources (json), x, y, original_json (raw)

- ticks (quantized state at app.tick_ms)
  - tick_id, fight_id, report_id, ts_ms, state (json) [cooldowns, gcd, resources, buffs, combo, target, mask]

- abilities (lookup from XIVAPI)
  - ability_id, name, school, xivapi_id

- status (lookup from XIVAPI)
  - status_id, name, stackable, xivapi_id, duration_ms

- metrics_fight_job (derived)
  - fight_id, actor_id, rDPS, aDPS, gcd_uptime_pct, dot_uptime_pct, buff_window_uptime_pct,
    deaths, mitigation_events, resource_issues, windows_json

Partitions
- Parquet layout: game_patch/encounter_name/job/report_date=YYYY-MM/
  - encounter_name: slugified (lowercase, hyphens)

Standards
- Time: UTC, integer ms timestamps
- IDs: internal surrogate keys + original FF Logs IDs for lineage
- Versions: game_patch, dataset_version, schema_version, source_hash

