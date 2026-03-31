"""
Need vs Wants classification using a lightweight logistic regression.

Designed to be consistent with earlier bug-fixes:
- Normalize category variations to standard buckets
- Default unknown/unmatched categories to WANT (and mark unclassified)
- Provide debug logs for each transaction classification
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def normalize_category_and_need(category: Optional[str], amount: float) -> Tuple[str, int, bool]:
    """
    Returns (normalized_category, label, is_unclassified)
    label: 1 => NEED, 0 => WANT
    """
    if not category:
        return "Unclassified", 0, True

    c = str(category).lower().strip()
    amt = float(amount or 0.0)

    food_keywords = ["food", "eating", "restaurant", "zomato", "swiggy"]
    if any(kw in c for kw in food_keywords):
        if amt < 500:
            return "dining_out", 0, False
        return "groceries", 1, False

    if any(kw in c for kw in ["grocer", "grocery", "groceries"]):
        return "groceries", 1, False

    if any(kw in c for kw in ["rent", "housing", "hostel", "home", "room"]):
        return "rent", 1, False
    if any(kw in c for kw in ["utility", "utilities", "electric", "water", "gas"]):
        return "utilities", 1, False
    if any(kw in c for kw in ["health", "medical", "medicine"]):
        return "healthcare", 1, False
    if any(kw in c for kw in ["transport", "commute", "travel", "uber", "ola", "metro"]):
        return "transportation", 1, False
    if any(kw in c for kw in ["education", "school", "college", "tuition"]):
        return "education", 1, False
    if any(kw in c for kw in ["debt", "loan", "emi", "credit", "card_payment"]):
        return "debt_payments", 1, False
    if "insurance" in c:
        return "insurance", 1, False

    # Unknown category => WANT and mark it.
    return "Unclassified", 0, True


def _sigmoid(z: Any) -> Any:
    return 1.0 / (1.0 + np.exp(-z))


def _train_logreg_onehot(categories: List[str], labels: List[int], lr: float = 0.2, steps: int = 600, l2: float = 1e-3) -> Dict[str, Any]:
    unique_cats = sorted(list({c for c in categories}))
    cat_to_idx = {c: i for i, c in enumerate(unique_cats)}
    x = np.zeros((len(categories), len(unique_cats)), dtype=float)
    for i, c in enumerate(categories):
        x[i, cat_to_idx[c]] = 1.0

    y = np.array(labels, dtype=float).reshape(-1, 1)
    w = np.zeros((x.shape[1], 1), dtype=float)
    b = 0.0

    for _ in range(steps):
        logits = x @ w + b
        p = _sigmoid(logits)
        grad_w = (x.T @ (p - y)) / len(categories) + l2 * w
        grad_b = float(np.mean(p - y))
        w -= lr * grad_w
        b -= lr * grad_b

    return {"weights": w.reshape(-1), "bias": float(b), "cat_to_idx": cat_to_idx, "unique_cats": unique_cats}


def _predict_proba_for_categories(model: Dict[str, Any], categories: List[str]) -> Dict[str, float]:
    weights = model.get("weights", np.array([]))
    bias = float(model.get("bias", 0.0))
    cat_to_idx = model.get("cat_to_idx", {})
    if getattr(weights, "size", 0) == 0:
        return {c: 0.5 for c in categories}

    out: Dict[str, float] = {}
    for c in categories:
        idx = cat_to_idx.get(c)
        if idx is None:
            out[c] = 0.5
        else:
            out[c] = float(_sigmoid(weights[idx] + bias))
    return out


def classify_need_want(transactions_data: List[Dict[str, Any]], threshold: float = 0.5) -> Dict[str, Any]:
    expenses = [t for t in transactions_data if t.get("type") == "expense"]
    if not expenses:
        return {
            "need_ratio": None,
            "want_ratio": None,
            "needs_amount_total": 0.0,
            "wants_amount_total": 0.0,
            "category_need_prob": {},
            "threshold": threshold,
            "unclassified_count": 0,
            "reason": "No expense transactions available",
        }

    categories: List[str] = []
    labels: List[int] = []
    amounts: List[float] = []
    unclassified_count = 0
    heuristic_need_total = 0.0
    heuristic_want_total = 0.0

    for t in expenses:
        raw_cat = t.get("category") or "Other"
        amt = float(t.get("amount", 0.0) or 0.0)
        norm_cat, y, is_unclassified = normalize_category_and_need(raw_cat, amt)
        categories.append(norm_cat)
        labels.append(int(y))
        amounts.append(amt)

        if is_unclassified:
            unclassified_count += 1

        if y == 1:
            heuristic_need_total += amt
        else:
            heuristic_want_total += amt

        # Debug log
        print(
            f"[need_want] txn category='{raw_cat}' amount={amt:.2f} -> normalized='{norm_cat}' "
            f"=> classification={'NEED' if y == 1 else 'WANT'}"
        )

    total_amount = float(sum(amounts))
    if total_amount <= 0:
        return {
            "need_ratio": None,
            "want_ratio": None,
            "needs_amount_total": 0.0,
            "wants_amount_total": 0.0,
            "category_need_prob": {},
            "threshold": threshold,
            "unclassified_count": unclassified_count,
            "reason": "Expense amounts are zero",
        }

    # Degenerate: if heuristics only produce one class.
    if len(set(labels)) < 2:
        need_ratio = heuristic_need_total / total_amount
        want_ratio = 1.0 - need_ratio
        return {
            "need_ratio": float(need_ratio),
            "want_ratio": float(want_ratio),
            "needs_amount_total": float(heuristic_need_total),
            "wants_amount_total": float(heuristic_want_total),
            "category_need_prob": {},
            "threshold": threshold,
            "unclassified_count": unclassified_count,
            "reason": "Degenerate heuristic labels (only one class in data)",
        }

    model = _train_logreg_onehot(categories=categories, labels=labels)
    unique_cats = sorted(list({c for c in categories}))
    category_need_prob = _predict_proba_for_categories(model, unique_cats)

    needs_total = 0.0
    wants_total = 0.0
    for cat, amt in zip(categories, amounts):
        p_need = category_need_prob.get(cat, 0.5)
        if p_need >= threshold:
            needs_total += amt
        else:
            wants_total += amt

    denom = needs_total + wants_total
    need_ratio = needs_total / denom if denom > 0 else None
    want_ratio = wants_total / denom if denom > 0 else None

    return {
        "need_ratio": float(need_ratio) if need_ratio is not None else None,
        "want_ratio": float(want_ratio) if want_ratio is not None else None,
        "needs_amount_total": float(needs_total),
        "wants_amount_total": float(wants_total),
        "category_need_prob": category_need_prob,
        "threshold": threshold,
        "unclassified_count": unclassified_count,
    }

