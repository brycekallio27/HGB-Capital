"""
photizo.sentiment — lightweight headline sentiment + risk-flag scorer.

Purpose: take a list of news items (already fetched by app.py) and produce a
per-ticker sentiment score and a list of risk flags. Designed to be
zero-dependency (no NLTK/VADER/transformers) so it works on a fresh install
without extra packages.

The lexicon is intentionally finance-flavored. It's not state-of-the-art
sentiment, but it's a useful signal for cross-referencing allocation
candidates with the news cycle.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Finance-flavored sentiment lexicons
# ---------------------------------------------------------------------------
POSITIVE_TERMS = {
    "beat", "beats", "beating", "outperform", "outperforms", "outperformed",
    "upgrade", "upgrades", "upgraded", "raises", "raised", "boost", "boosts",
    "boosted", "surge", "surges", "surged", "rally", "rallied", "rallies",
    "record", "soars", "soared", "jumps", "jumped", "strong", "stronger",
    "growth", "expansion", "expanding", "expand", "approve", "approved",
    "approval", "wins", "win", "won", "secures", "secured", "exceeds",
    "exceeded", "tops", "topped", "breakthrough", "milestone", "tailwind",
    "bullish", "buyback", "buybacks", "dividend",
}
NEGATIVE_TERMS = {
    "miss", "misses", "missed", "downgrade", "downgrades", "downgraded",
    "cuts", "cut", "lowers", "lowered", "slumps", "slump", "slumped",
    "crash", "crashes", "crashed", "tumble", "tumbles", "tumbled", "drop",
    "drops", "dropped", "fall", "falls", "fell", "weak", "weaker", "decline",
    "declines", "declined", "loss", "losses", "lost", "warns", "warning",
    "warned", "guidance cut", "layoffs", "layoff", "fired", "fires", "firing",
    "investigation", "investigated", "lawsuit", "subpoena", "fraud",
    "bankrupt", "bankruptcy", "default", "defaulted", "downturn", "recession",
    "headwind", "headwinds", "bearish", "selloff", "sell-off", "plunges",
    "plunged",
}
RISK_TERMS = {
    "fraud", "investigation", "lawsuit", "subpoena", "sec probe", "doj",
    "recall", "recalled", "delisting", "delisted", "going concern",
    "bankruptcy", "default", "downgrade", "fired ceo", "fires ceo",
    "ceo resigns", "cfo resigns", "audit", "restatement", "guidance cut",
}


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")]


def score_text(text: str) -> dict:
    """Score a single string. Returns {pos, neg, score, label, risks}."""
    if not text:
        return {"pos": 0, "neg": 0, "score": 0.0, "label": "neutral", "risks": []}
    tokens = _tokenize(text)
    pos = sum(1 for t in tokens if t in POSITIVE_TERMS)
    neg = sum(1 for t in tokens if t in NEGATIVE_TERMS)
    total = pos + neg
    score = (pos - neg) / total if total else 0.0
    if score >= 0.25:
        label = "positive"
    elif score <= -0.25:
        label = "negative"
    else:
        label = "neutral"
    lower = text.lower()
    risks = [r for r in RISK_TERMS if r in lower]
    return {
        "pos": pos,
        "neg": neg,
        "score": score,
        "label": label,
        "risks": risks,
    }


def score_news_items(news_items: list[dict]) -> dict:
    """Aggregate sentiment across a list of news items.

    Each item is expected to have a `title` field (and optional `summary`).
    Returns aggregate {pos, neg, score, label, risks, n_items}.
    """
    if not news_items:
        return {
            "pos": 0, "neg": 0, "score": 0.0, "label": "no_data",
            "risks": [], "n_items": 0,
        }
    pos = neg = 0
    risks: set[str] = set()
    for item in news_items:
        text = " ".join([
            str(item.get("title", "")),
            str(item.get("summary", "")),
        ])
        s = score_text(text)
        pos += s["pos"]
        neg += s["neg"]
        risks.update(s["risks"])
    total = pos + neg
    score = (pos - neg) / total if total else 0.0
    if score >= 0.20:
        label = "positive"
    elif score <= -0.20:
        label = "negative"
    else:
        label = "neutral"
    return {
        "pos": pos,
        "neg": neg,
        "score": score,
        "label": label,
        "risks": sorted(risks),
        "n_items": len(news_items),
    }


def headline_emoji(label: str) -> str:
    return {
        "positive": "🟢",
        "negative": "🔴",
        "neutral":  "🟡",
        "no_data":  "⚪",
    }.get(label, "⚪")
