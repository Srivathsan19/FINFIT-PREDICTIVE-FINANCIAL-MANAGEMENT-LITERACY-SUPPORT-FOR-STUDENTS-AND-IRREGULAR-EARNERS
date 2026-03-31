"""
Analytics API routes
"""
from flask import Blueprint, jsonify, request
from models import Transaction, Goal, db, UserProfileHistory
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict
import math
import statistics
import numpy as np
from utils.helpers import login_required, get_current_user
from ml.analytics_ml import PersonalityClassifier, SurvivalDaysPredictor, SmartRecommendationsEngine
from ml.spending_behavior_kmeans import classify_spending_behavior
from ml.spending_behavior_momentum import update_profile_history_and_get_stable
from ml.need_want_logreg import classify_need_want

analytics_bp = Blueprint('analytics', __name__)


def _parse_date_maybe(date_value):
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            return None
    try:
        return date_value.date() if hasattr(date_value, 'date') else None
    except Exception:
        return None


def _get_transactions_data(user):
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    transactions_data = []
    for t in transactions:
        date_str = t.date
        if isinstance(t.date, datetime):
            date_str = t.date.strftime('%Y-%m-%d')
        elif isinstance(t.date, str):
            date_str = t.date
        else:
            date_str = str(t.date) if t.date else datetime.now().strftime('%Y-%m-%d')

        transactions_data.append({
            'type': t.type,
            'amount': float(t.amount or 0.0),
            'category': t.category or 'Other',
            'date': date_str,
        })
    return transactions_data


def _increment_month(ym: str) -> str:
    dt = datetime.strptime(ym + '-01', '%Y-%m-%d').date()
    year = dt.year
    month = dt.month + 1
    if month == 13:
        month = 1
        year += 1
    return f'{year:04d}-{month:02d}'


def _forecast_expense_next_month_2mo(transactions_data: list) -> dict:
    """Forecast next-month total expense using last 1..6 expense months."""
    expenses = [t for t in transactions_data if t.get('type') == 'expense']
    monthly = {}
    for t in expenses:
        dt = _parse_date_maybe(t.get('date'))
        if dt is None:
            continue
        mk = dt.strftime('%Y-%m')
        monthly[mk] = monthly.get(mk, 0.0) + float(t.get('amount', 0.0))

    months_sorted = sorted(monthly.keys())
    if not months_sorted:
        return {
            'forecasted_amount': None,
            'next_month_label': None,
            'data_months_used': 0,
            'confidence_level': 'unknown',
            'message': 'No expense months available',
            'months_used': [],
            'regression_used': False,
        }

    if len(months_sorted) == 1:
        last_m = months_sorted[-1]
        next_m = _increment_month(last_m)
        last_val = float(monthly[last_m])
        forecasted = max(0.0, last_val * 1.05)
        return {
            'forecasted_amount': forecasted,
            'next_month_label': next_m,
            'data_months_used': 1,
            'confidence_level': 'low',
            'message': 'Estimated projection using 1 month of expense history (conservative +5% growth).',
            'months_used': [last_m],
            'regression_used': False,
        }

    months_used = months_sorted[-min(len(months_sorted), 6):]
    y = np.array([monthly[m] for m in months_used], dtype=float)
    x = np.arange(len(months_used), dtype=float)

    x_mean = float(x.mean())
    y_mean = float(y.mean())
    denom = float(np.sum((x - x_mean) ** 2))
    if denom == 0:
        slope = 0.0
        intercept = y_mean
    else:
        slope = float(np.sum((x - x_mean) * (y - y_mean)) / denom)
        intercept = float(y_mean - slope * x_mean)

    next_x = float(len(months_used))
    y_next = max(0.0, float(slope * next_x + intercept))
    next_m = _increment_month(months_used[-1])

    data_months_used = int(len(months_used))
    if 2 <= data_months_used <= 4:
        confidence_level = 'medium'
    elif data_months_used >= 5:
        confidence_level = 'high'
    else:
        confidence_level = 'medium'

    return {
        'forecasted_amount': y_next,
        'next_month_label': next_m,
        'data_months_used': data_months_used,
        'confidence_level': confidence_level,
        'message': f'Linear regression forecast using {data_months_used} expense months.',
        'months_used': months_used,
        'regression_used': True,
        'slope': slope,
        'intercept': intercept,
    }


def _compute_survival_days_forecast(transactions_data: list, current_balance: float) -> dict:
    forecast = _forecast_expense_next_month_2mo(transactions_data)
    forecasted_monthly_expense = forecast.get('forecasted_amount')
    if forecasted_monthly_expense is None:
        return {
            'survival_days': None,
            'status': 'unknown',
            'message': 'Insufficient expense data. Start tracking your expenses!',
            'current_balance': current_balance,
            'average_daily_expense': 0,
        }

    try:
        forecasted_daily_expense = float(forecasted_monthly_expense) / 30.0 if forecasted_monthly_expense > 0 else 0.0
    except Exception:
        forecasted_daily_expense = 0.0

    if forecasted_daily_expense <= 0:
        return {
            'survival_days': None,
            'status': 'unknown',
            'message': 'Insufficient expense data for stable forecast.',
            'current_balance': current_balance,
            'average_daily_expense': 0,
        }

    survival_days = int(math.floor(float(current_balance) / forecasted_daily_expense))

    if survival_days < 7:
        status = 'critical'
        message = f'⚠️ Critical: At current spend forecast, your balance lasts {survival_days} days.'
    elif survival_days < 14:
        status = 'warning'
        message = f'⚠️ Warning: At current spend forecast, your balance lasts {survival_days} days.'
    elif survival_days < 30:
        status = 'moderate'
        message = f'✓ Moderate: At current spend forecast, your balance lasts {survival_days} days.'
    else:
        status = 'safe'
        message = f'✓ Safe: At current spend forecast, your balance lasts {survival_days} days.'

    if not forecast.get('regression_used'):
        message += ' (Estimated projection due to limited expense history.)'

    return {
        'survival_days': survival_days,
        'status': status,
        'message': message,
        'current_balance': current_balance,
        'average_daily_expense': forecasted_daily_expense,
        'forecast_confidence_level': forecast.get('confidence_level'),
    }


def _normalize_category_and_need(category: str | None, amount: float) -> tuple[str, int, bool]:
    """Normalize categories and map them to need (1) vs want (0)."""
    if not category:
        return 'Unclassified', 0, True

    c = str(category).lower().strip()
    amt = float(amount or 0.0)

    food_keywords = ['food', 'eating', 'restaurant', 'zomato', 'swiggy']
    if any(kw in c for kw in food_keywords):
        if amt < 500:
            return 'dining_out', 0, False
        return 'groceries', 1, False

    if any(kw in c for kw in ['grocer', 'grocery', 'groceries']):
        return 'groceries', 1, False

    if any(kw in c for kw in ['rent', 'housing', 'hostel', 'home', 'room']):
        return 'rent', 1, False
    if any(kw in c for kw in ['utility', 'utilities', 'electric', 'water', 'gas']):
        return 'utilities', 1, False
    if any(kw in c for kw in ['health', 'medical', 'medicine']):
        return 'healthcare', 1, False
    if any(kw in c for kw in ['transport', 'commute', 'travel', 'uber', 'ola', 'metro']):
        return 'transportation', 1, False
    if any(kw in c for kw in ['education', 'school', 'college', 'tuition']):
        return 'education', 1, False
    if any(kw in c for kw in ['debt', 'loan', 'emi', 'credit', 'card_payment']):
        return 'debt_payments', 1, False
    if 'insurance' in c:
        return 'insurance', 1, False

    # Unknown category => default want (0) and flag unclassified.
    return 'Unclassified', 0, True


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def _train_logreg_onehot(categories: list[str], labels: list[int], lr: float = 0.2, steps: int = 600, l2: float = 1e-3) -> dict:
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

    return {'weights': w.reshape(-1), 'bias': float(b), 'cat_to_idx': cat_to_idx, 'unique_cats': unique_cats}


def _predict_proba_for_categories(model: dict, categories: list[str]) -> dict[str, float]:
    weights = model.get('weights', np.array([]))
    bias = float(model.get('bias', 0.0))
    cat_to_idx = model.get('cat_to_idx', {})
    if weights.size == 0:
        return {c: 0.5 for c in categories}
    out = {}
    for c in categories:
        idx = cat_to_idx.get(c)
        if idx is None:
            out[c] = 0.5
        else:
            out[c] = float(_sigmoid(weights[idx] + bias))
    return out


def _kmeans_classify_spending_behavior(transactions_data: list, window_days: int = 60, recency_double_days: int = 30) -> dict:
    """
    Dependency-light KMeans classification for:
      Saver / Balanced / High-Spender
    Uses weekly buckets and features:
      expense_intensity, variance_index, spending_velocity
    """
    today = datetime.now().date()
    window_cutoff = today - timedelta(days=window_days)
    # Only consider expenses/incomes inside the 60-day window
    parsed = []
    for t in transactions_data:
        dt = _parse_date_maybe(t.get('date'))
        if dt is None:
            continue
        if dt < window_cutoff:
            continue
        wt = 2.0 if dt >= (today - timedelta(days=recency_double_days)) else 1.0
        parsed.append({
            'type': t.get('type'),
            'amount': float(t.get('amount', 0.0)),
            'date': dt,
            'weight': wt,
        })

    if len(parsed) < 6:
        return {'behavior': 'Balanced', 'confidence': 0.0, 'cluster_map': {}, 'spending_velocity': 0.0, 'reason': 'Not enough data'}

    # Weekly buckets
    bucket_size_days = 7
    num_buckets = max(1, window_days // bucket_size_days)
    start_day = today - timedelta(days=window_days) + timedelta(days=1)

    buckets = []
    for b in range(num_buckets):
        b_start = start_day + timedelta(days=b * bucket_size_days)
        b_end = min(today, b_start + timedelta(days=bucket_size_days - 1))
        buckets.append((b_start, b_end))

    expenses = [p for p in parsed if p['type'] == 'expense']
    incomes = [p for p in parsed if p['type'] == 'income']

    x_raw = []
    bucket_feats = []
    for (b_start, b_end) in buckets:
        daily_exp = defaultdict(float)
        total_exp = 0.0

        for e in expenses:
            if b_start <= e['date'] <= b_end:
                total_exp += e['amount'] * e['weight']
                daily_exp[e['date']] += e['amount'] * e['weight']

        days_span = max(1, (b_end - b_start).days + 1)
        expense_intensity = float(total_exp / days_span)

        if daily_exp:
            vals = np.array(list(daily_exp.values()), dtype=float)
            mean_val = float(np.mean(vals))
            var_val = float(np.var(vals)) if len(vals) > 1 else 0.0
            variance_index = (var_val / (mean_val ** 2)) if mean_val > 0 else 0.0
        else:
            variance_index = 0.0

        # spending velocity
        bucket_incomes = [inc for inc in incomes if b_start <= inc['date'] <= b_end]
        total_income = float(sum(inc['amount'] * inc['weight'] for inc in bucket_incomes))
        if total_income <= 0:
            spending_velocity = 0.0
        else:
            used_expense_ids = set()
            num = 0.0
            for inc in bucket_incomes:
                for ex_idx, ex in enumerate(expenses):
                    if b_start <= ex['date'] <= b_end:
                        # count only expenses within 3 days of income date
                        if inc['date'] <= ex['date'] <= (inc['date'] + timedelta(days=3)):
                            if ex_idx not in used_expense_ids:
                                used_expense_ids.add(ex_idx)
                                num += ex['amount'] * ex['weight']
            spending_velocity = float(num / total_income)

        x_raw.append([expense_intensity, variance_index, spending_velocity])
        bucket_feats.append({'expense_intensity': expense_intensity, 'variance_index': variance_index, 'spending_velocity': spending_velocity})

    x_raw_arr = np.array(x_raw, dtype=float)
    # Standardize
    mean = x_raw_arr.mean(axis=0)
    std = x_raw_arr.std(axis=0)
    std[std == 0] = 1.0
    x = (x_raw_arr - mean) / std

    # KMeans (k=3)
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

    # Assign labels by cluster_score = avg(spending_velocity)
    cluster_scores = {}
    for c in range(k):
        idxs = np.where(labels == c)[0]
        if len(idxs) == 0:
            cluster_scores[c] = 0.0
        else:
            vals = x_raw_arr[idxs]
            cluster_scores[c] = 0.7 * float(vals[:, 2].mean()) + 0.3 * float(vals[:, 0].mean())

    ordered = sorted(cluster_scores.items(), key=lambda kv: kv[1])  # low->high
    cluster_map = {}
    if len(ordered) >= 3:
        cluster_map[ordered[0][0]] = 'Saver'
        cluster_map[ordered[1][0]] = 'Balanced'
        cluster_map[ordered[-1][0]] = 'High-Spender'
    else:
        for cid, _ in ordered:
            cluster_map[cid] = 'Balanced'
        if ordered:
            cluster_map[ordered[0][0]] = 'Saver'
            cluster_map[ordered[-1][0]] = 'High-Spender'

    newest_idx = len(x_raw_arr) - 1
    assigned_cluster = int(labels[newest_idx])
    raw_behavior = cluster_map.get(assigned_cluster, 'Balanced')
    raw_velocity = float(bucket_feats[newest_idx]['spending_velocity'])

    # velocity override
    behavior = 'High-Spender' if raw_velocity >= 0.70 else raw_behavior
    dist = float(np.linalg.norm(x[newest_idx] - centroids[assigned_cluster])) if k > 0 else 0.0
    confidence = float(1.0 / (1.0 + dist)) if dist >= 0 else 0.0

    return {
        'behavior': behavior,
        'confidence': confidence,
        'cluster_map': cluster_map,
        'spending_velocity': raw_velocity,
        'reason': 'Rolling window KMeans classification'
    }


@analytics_bp.route('/api/personality-test', methods=['GET'])
@login_required
def personality_test():
    """Get spending personality analysis"""
    user = get_current_user()
    
    # Get user transactions
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    
    # Calculate totals
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'income'
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'expense'
    ).scalar() or 0
    
    transactions_data = _get_transactions_data(user)

    # Use momentum-stabilized spending profile so it can't flip on one transaction.
    kmeans = update_profile_history_and_get_stable(
        user.id,
        transactions_data,
        window_days=60,
        recency_double_days=30,
    )
    stable_label = kmeans.get('behavior', 'Balanced')
    raw_velocity = float(kmeans.get('spending_velocity') or 0.0)
    confidence = float(kmeans.get('confidence') or 0.0) * 100.0
    savings_rate = ((float(total_income) - float(total_expense)) / float(total_income)) if float(total_income) > 0 else 0.0

    # Keep response shape compatible with the existing frontend.
    return jsonify({
        'personality': stable_label,
        'confidence': f"{confidence:.1f}%",
        'savings_rate': f"{savings_rate * 100:.1f}",
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'traits': [
            f"Spending profile: {stable_label}",
            f"Spending velocity: {raw_velocity:.2f}",
        ],
        'recommendations': [],
    })


@analytics_bp.route('/api/survival-days', methods=['GET'])
@login_required
def survival_days():
    """Calculate survival days based on current balance and spending patterns"""
    user = get_current_user()
    
    # Get current balance
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'income'
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'expense'
    ).scalar() or 0
    
    current_balance = total_income - total_expense
    
    transactions_data = _get_transactions_data(user)
    # Forecast-based survival days (uses forecasted daily expense)
    survival_result = _compute_survival_days_forecast(transactions_data, float(current_balance))
    if survival_result.get('survival_days') is None:
        # fallback to historical predictor for robustness
        predictor = SurvivalDaysPredictor()
        result = predictor.predict(transactions_data, float(current_balance))
        return jsonify(result)

    return jsonify(survival_result)


@analytics_bp.route('/api/daily-target', methods=['POST'])
@login_required
def daily_target():
    """Calculate daily earning target for irregular income earners"""
    user = get_current_user()
    
    data = request.get_json()
    monthly_expenses = data.get('monthly_expenses', 0)
    savings_goal = data.get('savings_goal', 0)
    working_days = data.get('working_days', 20)
    
    if monthly_expenses <= 0:
        return jsonify({'error': 'Monthly expenses must be greater than 0'}), 400
    
    if working_days <= 0 or working_days > 31:
        return jsonify({'error': 'Working days must be between 1 and 31'}), 400
    
    # Calculate targets
    total_needed = monthly_expenses + savings_goal
    daily_target = total_needed / working_days
    weekly_target = daily_target * 7
    monthly_target = daily_target * working_days
    
    # Breakdown
    expenses_portion = monthly_expenses / working_days
    savings_portion = savings_goal / working_days
    
    return jsonify({
        'daily_target': daily_target,
        'weekly_target': weekly_target,
        'monthly_target': monthly_target,
        'total_needed': total_needed,
        'breakdown': {
            'expenses_portion': expenses_portion,
            'savings_portion': savings_portion
        }
    })


@analytics_bp.route('/api/recommendations', methods=['GET'])
@login_required
def recommendations():
    """Get smart recommendations based on spending patterns"""
    user = get_current_user()
    
    # Get user data
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    goals = Goal.query.filter_by(user_id=user.id).all()
    
    # Calculate totals
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'income'
    ).scalar() or 0
    
    total_expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'expense'
    ).scalar() or 0
    
    transactions_data = _get_transactions_data(user)
    
    goals_data = [
        {
            'name': g.name,
            'target_amount': g.target_amount,
            'current_amount': g.current_amount
        }
        for g in goals
    ]
    
    current_balance = float(total_income) - float(total_expense)
    survival_result = _compute_survival_days_forecast(transactions_data, current_balance)
    survival_days = survival_result.get('survival_days')

    classifier = PersonalityClassifier()
    personality_result = classifier.classify(
        transactions_data,
        float(total_income),
        float(total_expense),
    )
    personality = personality_result.get('personality')

    # Use ML recommendation engine (align with survival + personality)
    engine = SmartRecommendationsEngine()
    recommendations = engine.generate(
        transactions_data,
        float(total_income),
        float(total_expense),
        goals_data
    )
    
    return jsonify({'recommendations': recommendations})


@analytics_bp.route('/api/metrics/summary', methods=['GET'])
@login_required
def analytics_metrics_summary():
    """
    Analytics metrics summary used for learning triggers.
    Returns key metrics as JSON.
    """
    user = get_current_user()
    window_days = int(request.args.get('window_days', 30))
    working_days = int(request.args.get('working_days', 20))
    savings_goal = float(request.args.get('savings_goal', 0))

    cutoff = datetime.now().date() - timedelta(days=window_days)
    transactions_data = _get_transactions_data(user)

    recent = []
    for t in transactions_data:
        dt = _parse_date_maybe(t.get('date'))
        if dt is None:
            continue
        if dt >= cutoff:
            recent.append((t, dt))

    income_amounts = [float(t.get('amount', 0.0)) for t, _dt in recent if t.get('type') == 'income']
    expense_amounts = [float(t.get('amount', 0.0)) for t, _dt in recent if t.get('type') == 'expense']

    total_income = float(sum(income_amounts)) if income_amounts else 0.0
    total_expense = float(sum(expense_amounts)) if expense_amounts else 0.0

    savings_rate_percent = None
    expense_ratio = None
    if total_income > 0:
        savings_rate_percent = ((total_income - total_expense) / total_income) * 100.0
        expense_ratio = total_expense / total_income

    income_stability_score = None
    income_variability_index = None
    if income_amounts and statistics.mean(income_amounts) > 0:
        mean_val = statistics.mean(income_amounts)
        std_val = statistics.pstdev(income_amounts)
        income_variability_index = std_val / mean_val if mean_val > 0 else None
        if income_variability_index is not None:
            income_stability_score = max(0.0, 1.0 - income_variability_index)

    dominant_category = None
    dominant_category_share = None
    if total_expense > 0:
        cat_totals = defaultdict(float)
        for t, _dt in recent:
            if t.get('type') != 'expense':
                continue
            cat = t.get('category') or 'Other'
            cat_totals[cat] += float(t.get('amount', 0.0))
        if cat_totals:
            dominant_category, dominant_amt = max(cat_totals.items(), key=lambda kv: kv[1])
            dominant_category_share = dominant_amt / total_expense

    daily_earning_target_expense_only = None
    daily_earning_target_with_savings = None
    if total_expense > 0 and recent:
        days_with_expenses = set()
        for t, dt in recent:
            if t.get('type') == 'expense':
                days_with_expenses.add(dt)
        num_days = max(len(days_with_expenses), 1)
        avg_daily_expense = total_expense / num_days
        estimated_monthly_expense = avg_daily_expense * 30.0
        daily_earning_target_expense_only = estimated_monthly_expense / max(working_days, 1)
        total_needed = estimated_monthly_expense + max(savings_goal, 0.0)
        daily_earning_target_with_savings = total_needed / max(working_days, 1)

    return jsonify({
        'window_days': window_days,
        'working_days': working_days,
        'savings_rate_percent': savings_rate_percent,
        'expense_ratio': expense_ratio,
        'income_stability_score': income_stability_score,
        'income_variability_index': income_variability_index,
        'dominant_category': dominant_category,
        'dominant_category_share': dominant_category_share,
        'daily_earning_target_expense_only': daily_earning_target_expense_only,
        'daily_earning_target_with_savings': daily_earning_target_with_savings,
    })


@analytics_bp.route('/api/classification/spending-behavior-kmeans', methods=['GET'])
@login_required
def spending_behavior_kmeans():
    user = get_current_user()
    transactions_data = _get_transactions_data(user)
    result = update_profile_history_and_get_stable(
        user.id,
        transactions_data,
        window_days=60,
        recency_double_days=30,
    )
    return jsonify(result)


@analytics_bp.route('/api/classification/need-want', methods=['GET'])
@login_required
def need_want_logreg_endpoint():
    user = get_current_user()
    transactions_data = _get_transactions_data(user)
    threshold = float(request.args.get('threshold', 0.5))
    result = classify_need_want(transactions_data, threshold=threshold)
    return jsonify(result)


@analytics_bp.route('/api/forecast/expense-2mo', methods=['GET'])
@login_required
def expense_forecast_2mo():
    user = get_current_user()
    transactions_data = _get_transactions_data(user)
    result = _forecast_expense_next_month_2mo(transactions_data)
    return jsonify(result)

