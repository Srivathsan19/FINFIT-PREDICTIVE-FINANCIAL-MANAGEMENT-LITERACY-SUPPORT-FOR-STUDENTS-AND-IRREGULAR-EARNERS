"""
Analytics API routes
"""
from flask import Blueprint, jsonify, request
from models import Transaction, Goal, db
from sqlalchemy import func
from datetime import datetime, timedelta
from utils.helpers import login_required, get_current_user
from ml.analytics_ml import PersonalityClassifier, SurvivalDaysPredictor, SmartRecommendationsEngine

analytics_bp = Blueprint('analytics', __name__)


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
    
    # Convert transactions to dict format
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
            'amount': t.amount,
            'category': t.category or 'Other',
            'date': date_str
        })
    
    # Use ML classifier
    classifier = PersonalityClassifier()
    result = classifier.classify(transactions_data, float(total_income), float(total_expense))
    
    return jsonify(result)


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
    
    # Get transactions
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
            'amount': t.amount,
            'category': t.category or 'Other',
            'date': date_str
        })
    
    # Use ML predictor
    predictor = SurvivalDaysPredictor()
    result = predictor.predict(transactions_data, float(current_balance))
    
    return jsonify(result)


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
    
    # Convert to dict format
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
            'amount': t.amount,
            'category': t.category or 'Other',
            'date': date_str
        })
    
    goals_data = [
        {
            'name': g.name,
            'target_amount': g.target_amount,
            'current_amount': g.current_amount
        }
        for g in goals
    ]
    
    # Use ML recommendation engine
    engine = SmartRecommendationsEngine()
    recommendations = engine.generate(
        transactions_data,
        float(total_income),
        float(total_expense),
        goals_data
    )
    
    return jsonify({'recommendations': recommendations})

