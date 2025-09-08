from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup


@dataclass
class JobAction:
    anchor_id: str
    name_en: str
    cast: Optional[str]
    recast: Optional[str]
    range: Optional[str]
    radius: Optional[str]
    tooltip: Optional[str]


JOB_SLUG_TO_ABBR: Dict[str, str] = {
    "paladin": "PLD",
    "warrior": "WAR",
    "darkknight": "DRK",
    "gunbreaker": "GNB",
    "monk": "MNK",
    "dragoon": "DRG",
    "ninja": "NIN",
    "samurai": "SAM",
    "viper": "VPR",
    "reaper": "RPR",
    "bard": "BRD",
    "machinist": "MCH",
    "dancer": "DNC",
    "blackmage": "BLM",
    "summoner": "SMN",
    "redmage": "RDM",
    "pictomancer": "PCT",
    "whitemage": "WHM",
    "scholar": "SCH",
    "sage": "SGE",
    "astrologian": "AST",
}


def fetch_jobguide_html(job_slug: str, *, timeout_s: float = 20.0) -> str:
    url = f"https://na.finalfantasyxiv.com/jobguide/{job_slug}/"
    headers = {
        "User-Agent": "ff14-dataset/0.1 (+https://example.com)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(timeout=timeout_s, headers=headers, follow_redirects=True, http2=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def _clean_text(s: str | None) -> Optional[str]:
    if not s:
        return None
    # Collapse whitespace and HTML breaks remnants.
    s = re.sub(r"\s+", " ", s)
    return s.strip() or None


def parse_job_actions(html: str) -> List[JobAction]:
    soup = BeautifulSoup(html, "html.parser")

    # Collect mapping from anchor (e.g., #pve_action__01) to action names via the icon grid.
    anchor_to_name: Dict[str, str] = {}
    for a in soup.select('a.job__skill_icon[href^="#pve_action__"]'):
        href = a.get("href") or ""
        if not href.startswith("#"):
            continue
        name = a.get("data-tooltip") or ""
        if name:
            anchor_to_name[href[1:]] = name.strip()

    actions: List[JobAction] = []
    for anchor_id, name in anchor_to_name.items():
        # The details row usually is <tr id="pve_action__XX"> with subsequent tds for cast/recast/range/radius
        row = soup.select_one(f"tr#{anchor_id}")
        cast = recast = rng = radius = tooltip = None

        if row:
            # Try to pick cells in this row
            cast_el = row.select_one("td.cast")
            recast_el = row.select_one("td.recast")
            dist_el = row.select_one("td.distant_range")

            cast = _clean_text(cast_el.get_text(" ") if cast_el else None)
            recast = _clean_text(recast_el.get_text(" ") if recast_el else None)

            if dist_el:
                # The distance cell may contain Range and Radius separated by hr/divs
                # Extract numeric-looking pieces in order: Range then Radius, if present
                text = dist_el.get_text(" ")
                text = re.sub(r"\s+", " ", text)
                parts = [p.strip() for p in re.split(r"\s*\bRange\b|\bRadius\b\s*", text) if p.strip()]
                # Fallback: just capture numbers with units
                nums = re.findall(r"\b\d+\s*(?:y|malms?|yalm|yalms)\b", text, flags=re.I)
                if len(nums) >= 1:
                    rng = nums[0]
                if len(nums) >= 2:
                    radius = nums[1]

            # Try to grab tooltip/effect text from the following rows until next action anchor
            tooltip_texts: List[str] = []
            nxt = row.find_next_sibling("tr")
            while nxt is not None:
                if nxt.has_attr("id") and str(nxt["id"]).startswith("pve_action__"):
                    break
                # Pull all td text in this row
                for td in nxt.find_all("td"):
                    t = _clean_text(td.get_text(" "))
                    if t:
                        tooltip_texts.append(t)
                nxt = nxt.find_next_sibling("tr")
            tooltip = _clean_text(" ".join(tooltip_texts))

        actions.append(
            JobAction(
                anchor_id=anchor_id,
                name_en=name,
                cast=cast,
                recast=recast,
                range=rng,
                radius=radius,
                tooltip=tooltip,
            )
        )

    return actions


def get_job_abbr(job_slug: str) -> Optional[str]:
    return JOB_SLUG_TO_ABBR.get(job_slug.lower())

