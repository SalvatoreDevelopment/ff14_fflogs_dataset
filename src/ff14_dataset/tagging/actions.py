from __future__ import annotations

import re
from typing import List, Optional


def derive_tags(
    *,
    name_en: str,
    tooltip: Optional[str],
    category: Optional[str],
    cast: Optional[str],
    recast: Optional[str],
) -> List[str]:
    t = (tooltip or "").lower()
    name_l = name_en.lower()
    tags: list[str] = []

    # Base: gcd/ogcd
    if category:
        if category.lower() in ("weaponskill", "spell"):
            tags.append("gcd")
        elif category.lower() == "ability":
            tags.append("ogcd")

    # Common mechanics
    if "reduces damage taken" in t or "damage taken is reduced" in t:
        if "party" in t or "nearby party" in t:
            tags.append("mitigation_party")
        else:
            tags.append("mitigation_self")
    if "hp cannot be reduced below 1" in t or "renders you impervious" in t:
        tags.append("invuln")
    if "increases damage dealt" in t:
        if "party" in t:
            tags.append("raid_buff")
        else:
            tags.append("personal_buff")
    if "increases healing" in t:
        tags.append("healing_buff")
    if "restores own hp" in t or "restores target's hp" in t or "restores hp" in t or "cure potency" in t:
        tags.append("heal")
    if "barrier" in t or "shield" in t:
        tags.append("barrier")
    if "stun" in t:
        tags.append("stun")
    if "interrupt" in t:
        tags.append("interrupt")
    if "silence" in t:
        tags.append("silence")
    if "increased enmity" in t or "enmity is increased" in t or "additional effect: increased enmity" in t:
        tags.append("tank_enmity")
    if re.search(r"damage over time|dot", t):
        tags.append("dot")
    if re.search(r"to all nearby enemies|all nearby enemies|all enemies in a straight line|in a cone", t):
        tags.append("aoe")
    else:
        # crude single-target hint
        if re.search(r"delivers an attack with a potency of", t):
            tags.append("st")
    if "combo action" in t:
        tags.append("combo_step")

    # Heuristics by name for PLD specifics
    if name_l in {"provoke"}:
        tags.append("taunt")
    if name_l in {"interject"}:
        tags.append("interrupt")
    if name_l in {"low blow"}:
        tags.append("stun")
    if name_l == "sheltron":
        tags.append("block")

    # Charges inference: recast text like "30s" doesn't convey charges; skip for now.
    return sorted(set(tags))

