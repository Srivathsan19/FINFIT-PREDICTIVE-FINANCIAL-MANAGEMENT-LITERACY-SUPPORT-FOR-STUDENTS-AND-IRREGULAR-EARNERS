"""
Expense forecast helper used by `/api/prediction`.

Implements linear regression based forecast of next-month total expenses.
Response schema is designed to match what `backend/app.py` and the frontend
expect: `forecasted_amount`, `confidence_level`, `data_months_used`,
`message`, plus some legacy convenience keys.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

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


def _increment_month(ym: str) -> str:
    dt = datetime.strptime(ym + "-01", "%Y-%m-%d").date()
    year = dt.year
    month = dt.month + 1
    if month == 13:
        month = 1
        year += 1
    return f"{year:04d}-{month:02d}"


def forecast_expense_next_month_lr2mo(transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Aggregate expense amounts by month: YYYY-MM
    monthly: Dict[str, float] = {}
    for t in transactions_data:
        if t.get("type") != "expense":
            continue
        dt = _parse_date_maybe(t.get("date"))
        if dt is None:
            continue
        mk = dt.strftime("%Y-%m")
        monthly[mk] = monthly.get(mk, 0.0) + float(t.get("amount", 0.0) or 0.0)

    months_sorted = sorted(monthly.keys())
    if not months_sorted:
        return {
            "forecasted_amount": None,
            "confidence_level": "unknown",
            "data_months_used": 0,
            "message": "No expense months available",
            "next_month_label": None,
            "months_used": [],
        }

    # Use 1..6 most recent months
    months_used = months_sorted[-min(len(months_sorted), 6) :]

    # 1 month => conservative +5%
    if len(months_used) == 1:
        last_m = months_used[-1]
        next_m = _increment_month(last_m)
        last_val = float(monthly[last_m])
        forecasted = max(0.0, last_val * 1.05)
        return {
            "forecasted_amount": forecasted,
            "confidence_level": "low",
            "data_months_used": 1,
            "message": "Estimated projection using 1 month of expense history (last_month * 1.05).",
            "next_month_label": next_m,
            "months_used": months_used,
            "regression_used": False,
        }

    # 2+ months => linear regression on month index -> monthly expense
    y = np.array([monthly[m] for m in months_used], dtype=float)
    x = np.arange(len(months_used), dtype=float)

    # Fit y = slope*x + intercept using least squares
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

    next_x = float(len(months_used))
    y_next = float(slope * next_x + intercept)
    forecasted = max(0.0, y_next)
    next_m = _increment_month(months_used[-1])

    data_months_used = int(len(months_used))
    if 2 <= data_months_used <= 4:
        confidence_level = "medium"
    else:
        confidence_level = "high"

    return {
        "forecasted_amount": forecasted,
        "confidence_level": confidence_level,
        "data_months_used": data_months_used,
        "message": f"Linear regression forecast using {data_months_used} expense months.",
        "next_month_label": next_m,
        "months_used": months_used,
        "regression_used": True,
        "slope": float(slope),
        "intercept": float(intercept),
    }

