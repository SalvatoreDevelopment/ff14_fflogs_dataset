import re


_non_alnum = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = _non_alnum.sub("-", s)
    s = s.strip("-")
    return s

