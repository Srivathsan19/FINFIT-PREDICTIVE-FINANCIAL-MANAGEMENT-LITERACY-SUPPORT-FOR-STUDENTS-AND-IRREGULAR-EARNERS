"""
Behavioral momentum for spending profile stability.

Stores recent cluster assignments in `UserProfileHistory` and only marks
the displayed behavior as stable when the last 3 assignments agree.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from models import db, UserProfileHistory
from ml.spending_behavior_kmeans import classify_spending_behavior


def _compute_stable_label_from_history(history_rows: List[UserProfileHistory], raw_label: str) -> str:
    # history_rows should be ordered oldest->newest
    if len(history_rows) < 3:
        return raw_label
    last_three = history_rows[-3:]
    a, b, c = last_three[0].cluster_label, last_three[1].cluster_label, last_three[2].cluster_label
    if a == b == c:
        return c
    return raw_label


def get_stable_spending_behavior_from_history(user_id: int, raw_label: str = "Balanced") -> str:
    history_rows = (
        UserProfileHistory.query.filter_by(user_id=user_id)
        .order_by(UserProfileHistory.id.desc())
        .limit(9)
        .all()
    )
    history = list(reversed(history_rows))
    return _compute_stable_label_from_history(history, raw_label=raw_label)


def update_profile_history_and_get_stable(
    user_id: int,
    transactions_data: List[Dict[str, Any]],
    window_days: int = 60,
    recency_double_days: int = 30,
) -> Dict[str, Any]:
    raw = classify_spending_behavior(
        transactions_data,
        window_days=window_days,
        recency_double_days=recency_double_days,
    )
    raw_label = raw.get("behavior", "Balanced")
    conf = float(raw.get("confidence") or 0.0)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        db.session.add(
            UserProfileHistory(
                user_id=user_id,
                cluster_label=raw_label,
                confidence=conf,
                created_at=now_str,
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    stable_label = get_stable_spending_behavior_from_history(user_id, raw_label=raw_label)

    return {
        **raw,
        "behavior": stable_label,
        "raw_behavior": raw_label,
    }

