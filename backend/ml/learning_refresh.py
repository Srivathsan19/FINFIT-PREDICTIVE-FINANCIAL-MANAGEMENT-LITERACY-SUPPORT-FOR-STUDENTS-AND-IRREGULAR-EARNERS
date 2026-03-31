"""
Compute and persist learning recommendations after every transaction.

This function is called synchronously from `backend/app.py` after:
- POST /api/transactions
- Gmail sync inserting transactions

It updates `LearningRecommendationCache` so GET /api/learning/recommendations
can quickly return ranked module cards.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from models import db, Transaction, LearningRecommendationCache, LearningModuleCompletion

from ml.learning_recommender import get_recommendations


def _get_transactions_data_for_user(user_id: int) -> List[Dict[str, Any]]:
    txs = Transaction.query.filter_by(user_id=user_id).all()
    out: List[Dict[str, Any]] = []
    for t in txs:
        date_val = t.date
        date_str = date_val
        out.append({
            "type": t.type,
            "amount": float(t.amount or 0.0),
            "category": t.category or "Other",
            "date": date_str,
        })
    return out


def _compute_metrics_30d(transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Keep the same metrics names expected by learning_recommender.
    cutoff_date = datetime.now().date() - timedelta(days=30)

    def _parse_date(d) -> Any:
        if isinstance(d, datetime):
            return d.date()
        if isinstance(d, str):
            # Supports YYYY-MM-DD as used by the app.
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except Exception:
                return None
        return None

    recent = []
    for t in transactions_data:
        dt = _parse_date(t.get("date"))
        if dt is None:
            continue
        if dt >= cutoff_date:
            recent.append((t, dt))

    incomes = [float(t.get("amount", 0.0)) for t, _dt in recent if t.get("type") == "income"]
    expenses = [float(t.get("amount", 0.0)) for t, _dt in recent if t.get("type") == "expense"]
    total_income = float(sum(incomes)) if incomes else 0.0
    total_expense = float(sum(expenses)) if expenses else 0.0

    savings_rate_percent = None
    expense_ratio = None
    if total_income > 0:
        savings_rate_percent = ((total_income - total_expense) / total_income) * 100.0
        expense_ratio = total_expense / total_income

    # income stability / variability
    income_stability_score = None
    income_variability_index = None
    if incomes and len(incomes) >= 2:
        mean_val = sum(incomes) / len(incomes)
        variance = sum((x - mean_val) ** 2 for x in incomes) / len(incomes)
        std_val = variance ** 0.5
        income_variability_index = std_val / mean_val if mean_val > 0 else None
        if income_variability_index is not None:
            income_stability_score = max(0.0, 1.0 - income_variability_index)

    # dominant category share (expenses only)
    dominant_category = None
    dominant_category_share = None
    if total_expense > 0:
        cat_totals: Dict[str, float] = {}
        for t, _dt in recent:
            if t.get("type") != "expense":
                continue
            cat = t.get("category") or "Other"
            cat_totals[cat] = cat_totals.get(cat, 0.0) + float(t.get("amount", 0.0))
        if cat_totals:
            dominant_category, dominant_amt = max(cat_totals.items(), key=lambda kv: kv[1])
            dominant_category_share = dominant_amt / total_expense if total_expense > 0 else None

    return {
        "savings_rate_percent": savings_rate_percent,
        "expense_ratio": expense_ratio,
        "income_stability_score": income_stability_score,
        "income_variability_index": income_variability_index,
        "dominant_category": dominant_category,
        "dominant_category_share": dominant_category_share,
        "income": total_income,
        "expenses": total_expense,
        # survival_days and spending profile are computed via analytics route helpers below
    }


def refresh_user_learning_recommendations(user_id: int) -> None:
    """
    Recompute ranked module recommendations and persist them to LearningRecommendationCache.
    """
    # Ensure we only act when tables exist.
    try:
        user_id_int = int(user_id)
    except Exception:
        return

    transactions_data = _get_transactions_data_for_user(user_id_int)
    metrics = _compute_metrics_30d(transactions_data)

    # Reuse analytics helpers for survival days + spending profile.
    try:
        from routes.analytics import _compute_survival_days_forecast
        from ml.spending_behavior_momentum import update_profile_history_and_get_stable

        total_income = float(metrics.get("income") or 0.0)
        total_expense = float(metrics.get("expenses") or 0.0)
        current_balance = total_income - total_expense

        survival_res = _compute_survival_days_forecast(transactions_data, current_balance=float(current_balance))
        metrics["survival_days"] = survival_res.get("survival_days")

        spend_res = update_profile_history_and_get_stable(
            user_id_int,
            transactions_data,
            window_days=60,
            recency_double_days=30,
        )
        metrics["spending_profile"] = spend_res.get("behavior")
        metrics["spending_profile_confidence"] = spend_res.get("confidence")
    except Exception:
        # Keep core metrics even if analytics helpers fail for some reason.
        metrics["survival_days"] = None
        metrics["spending_profile"] = None
        metrics["spending_profile_confidence"] = None

    completed = LearningModuleCompletion.query.filter_by(user_id=user_id_int).all()
    completed_keys = {c.module_key for c in completed}

    personality = metrics.get("spending_profile")
    recommendations = get_recommendations(
        metrics=metrics,
        personality=personality,
        completed_module_keys=completed_keys,
        top_k=6,
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cache = LearningRecommendationCache.query.filter_by(user_id=user_id_int).first()
    if not cache:
        cache = LearningRecommendationCache(
            user_id=user_id_int,
            recommendations_json="[]",
            updated_at=now_str,
        )
        db.session.add(cache)

    # Store list of recommended modules (module_key/title/rank/etc.)
    # Keep as JSON text to avoid adding extra JSON column deps.
    import json
    cache.recommendations_json = json.dumps(recommendations, ensure_ascii=False)
    cache.updated_at = now_str
    db.session.commit()

