"""
K-Means spending behavior classifier.

Classifies spending into:
- "Saver"
- "Balanced"
- "High-Spender"

Key behaviors (aligned with earlier bug-fixes):
- Use rolling window (default 60 days).
- Apply recency weighting: last 30 days count double.
- Compute spending_velocity = (expenses within 3 days of any income) / total income.
- Force "High-Spender" if spending_velocity >= 0.70.
- Use weekly buckets and K-Means (k=3) over engineered features.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _parse_date_maybe(date_value: Any) -> Optional[datetime.date]:
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except Exception:
            return None
    try:
        return date_value.date()  # type: ignore[attr-defined]
    except Exception:
        return None


def classify_spending_behavior(
    transactions_data: List[Dict[str, Any]],
    window_days: int = 60,
    recency_double_days: int = 30,
) -> Dict[str, Any]:
    today = datetime.now().date()
    window_cutoff = today - timedelta(days=window_days)

    # Build weighted transactions inside window
    parsed: List[Dict[str, Any]] = []
    for t in transactions_data:
        dt = _parse_date_maybe(t.get("date"))
        if dt is None or dt < window_cutoff:
            continue
        wt = 2.0 if dt >= (today - timedelta(days=recency_double_days)) else 1.0
        parsed.append({
            "type": t.get("type"),
            "amount": float(t.get("amount", 0.0) or 0.0),
            "date": dt,
            "weight": wt,
        })

    if len(parsed) < 6:
        return {
            "behavior": "Balanced",
            "confidence": 0.0,
            "cluster_map": {},
            "spending_velocity": 0.0,
            "reason": "Not enough data",
        }

    # Weekly buckets
    bucket_size_days = 7
    num_buckets = max(1, window_days // bucket_size_days)
    start_day = today - timedelta(days=window_days) + timedelta(days=1)

    buckets: List[Tuple[datetime.date, datetime.date]] = []
    for b in range(num_buckets):
        b_start = start_day + timedelta(days=b * bucket_size_days)
        b_end = min(today, b_start + timedelta(days=bucket_size_days - 1))
        buckets.append((b_start, b_end))

    expenses = [p for p in parsed if p["type"] == "expense"]
    incomes = [p for p in parsed if p["type"] == "income"]

    x_raw: List[List[float]] = []
    bucket_feats: List[Dict[str, float]] = []

    for (b_start, b_end) in buckets:
        daily_exp = defaultdict(float)
        total_exp = 0.0

        for e in expenses:
            if b_start <= e["date"] <= b_end:
                total_exp += e["amount"] * e["weight"]
                daily_exp[e["date"]] += e["amount"] * e["weight"]

        days_span = max(1, (b_end - b_start).days + 1)
        expense_intensity = float(total_exp / days_span)

        if daily_exp:
            vals = np.array(list(daily_exp.values()), dtype=float)
            mean_val = float(np.mean(vals))
            var_val = float(np.var(vals)) if len(vals) > 1 else 0.0
            variance_index = (var_val / (mean_val ** 2)) if mean_val > 0 else 0.0
        else:
            variance_index = 0.0

        # Spending velocity: expenses within 3 days of any income / total income
        bucket_incomes = [inc for inc in incomes if b_start <= inc["date"] <= b_end]
        total_income = float(sum(inc["amount"] * inc["weight"] for inc in bucket_incomes))

        if total_income <= 0:
            spending_velocity = 0.0
        else:
            # Count each expense once across all income dates in the bucket
            counted_idx = set()
            num = 0.0
            for inc in bucket_incomes:
                for ex_idx, ex in enumerate(expenses):
                    if ex_idx in counted_idx:
                        continue
                    if not (b_start <= ex["date"] <= b_end):
                        continue
                    # Count if expense is within 3 days of this income date
                    if inc["date"] <= ex["date"] <= (inc["date"] + timedelta(days=3)):
                        counted_idx.add(ex_idx)
                        num += ex["amount"] * ex["weight"]
            spending_velocity = float(num / total_income)

        x_raw.append([expense_intensity, variance_index, spending_velocity])
        bucket_feats.append({
            "expense_intensity": float(expense_intensity),
            "variance_index": float(variance_index),
            "spending_velocity": float(spending_velocity),
        })

    x_raw_arr = np.array(x_raw, dtype=float)

    # Standardize
    mean = x_raw_arr.mean(axis=0)
    std = x_raw_arr.std(axis=0)
    std[std == 0] = 1.0
    x = (x_raw_arr - mean) / std

    # KMeans (k=3, but limited by n)
    rng = np.random.default_rng(42)
    n = x.shape[0]
    k = min(3, n)

    init_idx = rng.choice(n, size=k, replace=False)
    centroids = x[init_idx].copy()
    labels = np.zeros(n, dtype=int)

    for _ in range(100):
        dists = np.linalg.norm(x[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(dists, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for c in range(k):
            pts = x[labels == c]
            if len(pts) > 0:
                centroids[c] = pts.mean(axis=0)

    # Map cluster id -> Saver/Balanced/High-Spender by average features
    cluster_scores: Dict[int, float] = {}
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            cluster_scores[c] = 0.0
        else:
            vals = x_raw_arr[idxs]
            # Lower velocity & lower intensity => lower score => Saver
            cluster_scores[c] = 0.7 * float(vals[:, 2].mean()) + 0.3 * float(vals[:, 0].mean())

    ordered = sorted(cluster_scores.items(), key=lambda kv: kv[1])  # low->high
    cluster_map: Dict[int, str] = {}
    if len(ordered) >= 3:
        cluster_map[ordered[0][0]] = "Saver"
        cluster_map[ordered[1][0]] = "Balanced"
        cluster_map[ordered[-1][0]] = "High-Spender"
    else:
        for cid, _ in ordered:
            cluster_map[cid] = "Balanced"
        if ordered:
            cluster_map[ordered[0][0]] = "Saver"
            cluster_map[ordered[-1][0]] = "High-Spender"

    newest_idx = len(x_raw_arr) - 1
    assigned_cluster = int(labels[newest_idx])
    raw_behavior = cluster_map.get(assigned_cluster, "Balanced")
    raw_velocity = float(bucket_feats[newest_idx]["spending_velocity"])

    # Force override
    behavior = "High-Spender" if raw_velocity >= 0.70 else raw_behavior

    dist = float(np.linalg.norm(x[newest_idx] - centroids[assigned_cluster])) if k > 0 else 0.0
    confidence = float(1.0 / (1.0 + dist)) if dist >= 0 else 0.0

    return {
        "behavior": behavior,
        "confidence": confidence,
        "cluster_map": cluster_map,
        "spending_velocity": raw_velocity,
        "reason": "Rolling window KMeans classification",
    }

