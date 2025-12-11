from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, send_from_directory, send_file, session
from flask_cors import CORS
from models import db, Transaction, Goal, User, PaymentRequest, GmailConnection
from sqlalchemy import func
import requests
import os
from datetime import datetime, timedelta
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import qrcode
import io
import base64
import re
from threading import Thread
import time

# Get the directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__, 
            static_folder=FRONTEND_DIR,
            static_url_path='')
CORS(app)
# Database path - ensure it's in the backend directory
DB_PATH = os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'finfit-secret-key-2024'  # For session management
db.init_app(app)

# Register blueprints
from routes.analytics import analytics_bp
app.register_blueprint(analytics_bp)

# Email configuration (using Gmail SMTP as default)
# To configure email:
# 1. For Gmail: Create an App Password (https://myaccount.google.com/apppasswords)
# 2. Set environment variables:
#    - Windows: set SMTP_EMAIL=your-email@gmail.com
#    - Windows: set SMTP_PASSWORD=your-app-password
#    - Linux/Mac: export SMTP_EMAIL=your-email@gmail.com
#    - Linux/Mac: export SMTP_PASSWORD=your-app-password
# 3. Or modify the default values below (not recommended for production)
# For other email providers, adjust SMTP_SERVER and SMTP_PORT accordingly
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')  # Your email
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Your app password

# --- Transactions ---
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return jsonify([{
        'id': t.id,
        'type': t.type,
        'category': t.category,
        'amount': t.amount,
        'date': t.date,
        'note': t.note
    } for t in transactions])

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    t = Transaction(
        user_id=user.id,
        type=data['type'],
        category=data['category'],
        amount=data['amount'],
        date=data['date'],
        note=data.get('note', '')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'message': 'Transaction added'}), 201

@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    t = Transaction.query.filter_by(id=id, user_id=user.id).first()
    if t:
        db.session.delete(t)
        db.session.commit()
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Not found'}), 404

# --- Goals ---
@app.route('/api/goals', methods=['GET'])
def get_goals():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    goals = Goal.query.filter_by(user_id=user.id).all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'target_amount': g.target_amount,
        'current_amount': g.current_amount,
        'deadline': g.deadline
    } for g in goals])

@app.route('/api/goals', methods=['POST'])
def add_goal():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    g = Goal(
        user_id=user.id,
        name=data['name'],
        target_amount=data['target_amount'],
        current_amount=data.get('current_amount', 0),
        deadline=data['deadline']
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'message': 'Goal added'}), 201

@app.route('/api/goals/<int:id>', methods=['PATCH'])
def update_goal(id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    g = Goal.query.filter_by(id=id, user_id=user.id).first()
    if not g:
        return jsonify({'error': 'Goal not found'}), 404
    data = request.json
    if 'amount' in data:
        g.current_amount = min(g.current_amount + data['amount'], g.target_amount)
    db.session.commit()
    return jsonify({
        'id': g.id,
        'name': g.name,
        'target_amount': g.target_amount,
        'current_amount': g.current_amount,
        'deadline': g.deadline
    })

@app.route('/api/goals/<int:id>', methods=['DELETE'])
def delete_goal(id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    g = Goal.query.filter_by(id=id, user_id=user.id).first()
    if g:
        db.session.delete(g)
        db.session.commit()
        return jsonify({'message': 'Goal deleted'})
    return jsonify({'error': 'Goal not found'}), 404

# --- Analytics (example: summary) ---
@app.route('/api/summary', methods=['GET'])
def get_summary():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'income'
    ).scalar() or 0
    expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'expense'
    ).scalar() or 0
    return jsonify({'income': float(income), 'expense': float(expense), 'savings': float(income - expense)})


@app.route('/api/prediction', methods=['GET'])
def predict_next_month():
    """
    Very simple predictive model for next-month expenses.
    - Groups past expenses by month (YYYY-MM)
    - Fits a straight line (month_index -> total_expense)
    - Extrapolates one step ahead
    This is NOT a full ML model, but it is a real, data-driven forecast.
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    expenses = Transaction.query.filter_by(user_id=user.id, type='expense').all()
    if not expenses:
        return jsonify({
            'history': [],
            'next_month_label': None,
            'next_month_total': 0.0
        })

    monthly_totals = defaultdict(float)
    for t in expenses:
        try:
            dt = datetime.strptime(t.date, '%Y-%m-%d')
        except Exception:
            # Skip malformed dates
            continue
        key = dt.strftime('%Y-%m')
        monthly_totals[key] += float(t.amount)

    if not monthly_totals:
        return jsonify({
            'history': [],
            'next_month_label': None,
            'next_month_total': 0.0
        })

    # Sort months chronologically
    sorted_items = sorted(monthly_totals.items(), key=lambda x: x[0])
    months = [m for m, _ in sorted_items]
    totals = [v for _, v in sorted_items]

    n = len(totals)
    # If we have only one month, predict the same amount
    if n == 1:
        predicted = totals[0]
    else:
        # Simple linear regression y = a*x + b on indices 0..n-1
        x_vals = list(range(n))
        sum_x = sum(x_vals)
        sum_y = sum(totals)
        sum_xx = sum(x * x for x in x_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, totals))
        denom = n * sum_xx - sum_x * sum_x
        if denom == 0:
            slope = 0.0
            intercept = totals[-1]
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / n
        next_x = n  # index of next month
        predicted = slope * next_x + intercept

    # Clamp negative predictions to zero
    predicted = max(predicted, 0.0)

    # Compute next month label based on latest month we have
    last_month_str = months[-1]  # 'YYYY-MM'
    try:
        last_dt = datetime.strptime(last_month_str + '-01', '%Y-%m-%d')
        # Add one month (roughly) by incrementing month and year
        year = last_dt.year
        month = last_dt.month + 1
        if month == 13:
            month = 1
            year += 1
        next_dt = datetime(year, month, 1)
        next_label = next_dt.strftime('%Y-%m')
    except Exception:
        next_label = None

    history = [
        {'month': m, 'total': float(v)}
        for m, v in sorted_items
    ]

    return jsonify({
        'history': history,
        'next_month_label': next_label,
        'next_month_total': float(predicted)
    })

# --- Chatbot ---
SYSTEM_PROMPT = """You are a helpful financial assistant for FinFit, a personal finance management app. 
You help users with budgeting, saving money, tracking expenses, setting financial goals, and general financial advice.
Be friendly, concise, and practical. Focus on actionable advice. If asked about specific features, explain how they work in FinFit. Note: If it isnt anything about finance or FinFit, respond with I'm here to help with your financial questions!."""


def build_user_context(user):
    """Build a compact, safe snapshot of the user's profile and finances."""
    income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'income'
    ).scalar() or 0
    expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == 'expense'
    ).scalar() or 0
    balance = income - expense

    # Active goals with progress
    goals = Goal.query.filter_by(user_id=user.id).all()
    goal_summaries = []
    for g in goals:
        if g.target_amount:
            progress = (g.current_amount / g.target_amount) * 100
        else:
            progress = 0
        goal_summaries.append(
            f"{g.name}: {g.current_amount:.2f}/{g.target_amount:.2f} ({progress:.0f}%){f' due {g.deadline}' if g.deadline else ''}"
        )
    goal_text = "; ".join(goal_summaries[:3]) if goal_summaries else "None"

    # Recent activity for better personalization
    recent_transactions = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.date.desc())
        .limit(5)
        .all()
    )
    txn_text = "; ".join(
        f"{t.date} {t.type} {t.category}: {t.amount:.2f}" for t in recent_transactions
    ) or "No transactions recorded"

    lines = [
        f"Name: {user.name or 'Unknown'}",
        f"Email: {user.email}",
        f"Member since: {user.created_at or 'unknown'}",
        f"Financial snapshot: income {income:.2f}, expense {expense:.2f}, balance {balance:.2f}",
        f"Active goals (max 3): {goal_text}",
        f"Recent transactions (max 5): {txn_text}",
    ]
    return "\n".join(lines)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"reply": "Please type something first 🙂"})
    
    user = get_current_user()
    user_context = build_user_context(user) if user else "No authenticated user; provide general help."
    
    # Build prompt for Ollama
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"User context:\n{user_context}\n\n"
        f"User: {user_message}\nAssistant:"
    )
    
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:latest",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        print("STATUS:", r.status_code)
        print("BODY:", r.text)
        r.raise_for_status()
        data = r.json()
        reply = data.get("response", "").strip()
    except Exception as e:
        reply = f"Error talking to model: {e}"
    
    return jsonify({"reply": reply})

# --- Helper function to get current user ---
def get_current_user():
    """Get current logged-in user from session"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# --- User/Login ---
@app.route('/api/register', methods=['POST'])
def register():
    """Create new user account"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        
        # Validation
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            email=email,
            name=name,
            created_at=datetime.now().strftime('%Y-%m-%d')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Flush to assign ID without committing
        user_id = user.id
        
        db.session.commit()
        
        # Set session
        session['user_id'] = user_id
        session['user_email'] = user.email
        session['user_name'] = user.name
        
        return jsonify({
            'message': 'Account created successfully',
            'email': user.email,
            'name': user.name,
            'id': user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create account: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    # Find user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['user_email'] = user.email
    session['user_name'] = user.name
    
    return jsonify({
        'message': 'Login successful',
        'email': user.email,
        'name': user.name
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/user', methods=['GET'])
def get_current_user_info():
    """Get current logged-in user info"""
    user = get_current_user()
    if user:
        return jsonify({
            'email': user.email,
            'name': user.name,
            'id': user.id,
            'created_at': user.created_at,
            'authenticated': True
        })
    return jsonify({'email': None, 'authenticated': False})

@app.route('/api/user', methods=['PATCH'])
def update_user_profile():
    """Update user profile information"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.json
        updated = False
        
        if 'name' in data and data['name']:
            user.name = data['name'].strip()
            session['user_name'] = user.name
            updated = True
        
        if 'email' in data and data['email']:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                # Check if email already exists
                existing = User.query.filter_by(email=new_email).first()
                if existing and existing.id != user.id:
                    return jsonify({'error': 'Email already in use'}), 400
                user.email = new_email
                session['user_email'] = user.email
                updated = True
        
        if updated:
            db.session.commit()
            return jsonify({
                'message': 'Profile updated successfully',
                'email': user.email,
                'name': user.name
            })
        else:
            return jsonify({'error': 'No valid fields to update'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

@app.route('/api/user/password', methods=['POST'])
def change_password():
    """Change user password"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.json
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not current_password:
            return jsonify({'error': 'Current password is required'}), 400
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to change password: {str(e)}'}), 500

@app.route('/api/user/delete', methods=['DELETE'])
def delete_account():
    """Delete user account and all associated data"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_id = user.id
        user_email = user.email
        
        # Delete all user data (transactions and goals are cascade deleted)
        db.session.delete(user)
        db.session.commit()
        
        # Clear session
        session.clear()
        
        return jsonify({
            'message': 'Account deleted successfully',
            'deleted_user_id': user_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete account: {str(e)}'}), 500

# --- Report Generation ---
def generate_financial_report(user_id):
    """Generate a formatted HTML financial report"""
    # Get user-specific financial data
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    
    # Calculate summary
    income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id, Transaction.type == 'income'
    ).scalar() or 0
    expense = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id, Transaction.type == 'expense'
    ).scalar() or 0
    balance = income - expense
    
    # Category breakdown
    category_expenses = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':
            category_expenses[t.category] += t.amount
    
    # Recent transactions (last 10)
    recent_transactions = sorted(transactions, key=lambda x: x.date, reverse=True)[:10]
    
    # Goals progress
    active_goals = [g for g in goals if g.current_amount < g.target_amount]
    
    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                line-height: 1.7;
                color: #2c3e50;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                padding: 40px 20px;
                min-height: 100vh;
            }}
            @keyframes gradientShift {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
            .email-container {{
                max-width: 850px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                color: white;
                padding: 50px 40px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: pulse 4s ease-in-out infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); opacity: 0.5; }}
                50% {{ transform: scale(1.1); opacity: 0.8; }}
            }}
            .header-content {{
                position: relative;
                z-index: 1;
            }}
            .header h1 {{
                margin: 0 0 15px 0;
                font-size: 36px;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                letter-spacing: -0.5px;
            }}
            .header .subtitle {{
                font-size: 18px;
                opacity: 0.95;
                font-weight: 300;
                margin-top: 10px;
            }}
            .header .date-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.25);
                backdrop-filter: blur(10px);
                padding: 10px 20px;
                border-radius: 25px;
                margin-top: 15px;
                font-size: 14px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            .section {{
                background: white;
                padding: 35px 40px;
                margin: 0;
                border-bottom: 1px solid #f0f0f0;
            }}
            .section:last-of-type {{
                border-bottom: none;
            }}
            .section h2 {{
                color: #2c3e50;
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 3px solid;
                border-image: linear-gradient(90deg, #667eea, #764ba2, #f093fb) 1;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 25px;
                margin: 25px 0;
            }}
            .stat-box {{
                padding: 30px 25px;
                border-radius: 16px;
                text-align: center;
                position: relative;
                overflow: hidden;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            }}
            .stat-box::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
            }}
            .stat-box.income {{
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                color: white;
            }}
            .stat-box.expense {{
                background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
                color: white;
            }}
            .stat-box.balance {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .stat-label {{
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 12px;
                opacity: 0.9;
                font-weight: 600;
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: 800;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .category-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            .category-item {{
                padding: 20px;
                margin: 15px 0;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                border-radius: 14px;
                border-left: 6px solid;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
                position: relative;
                overflow: hidden;
            }}
            .category-item::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 6px;
                height: 100%;
                background: linear-gradient(180deg, #667eea, #764ba2, #f093fb);
            }}
            .category-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .category-name {{
                font-size: 17px;
                font-weight: 700;
                color: #2c3e50;
                flex: 1;
                min-width: 150px;
            }}
            .category-amount {{
                font-weight: 700;
                color: #667eea;
                font-size: 18px;
                white-space: nowrap;
            }}
            .category-percentage {{
                font-size: 14px;
                color: #7f8c8d;
                font-weight: 600;
                margin-left: 8px;
            }}
            .category-bar-container {{
                width: 100%;
                background: #e9ecef;
                height: 28px;
                border-radius: 14px;
                overflow: hidden;
                margin-top: 10px;
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
            }}
            .category-bar {{
                height: 100%;
                border-radius: 14px;
                position: relative;
                overflow: hidden;
                transition: width 0.8s ease;
                min-width: 3%;
            }}
            .category-bar::after {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2.5s infinite;
            }}
            .category-bar-1 {{
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            }}
            .category-bar-2 {{
                background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            }}
            .category-bar-3 {{
                background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            }}
            .category-bar-4 {{
                background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
            }}
            .category-bar-5 {{
                background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
            }}
            .category-bar-6 {{
                background: linear-gradient(90deg, #30cfd0 0%, #330867 100%);
            }}
            .category-bar-default {{
                background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
            }}
            .transaction-item {{
                padding: 18px 20px;
                margin: 12px 0;
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-radius: 12px;
                border-left: 5px solid #28a745;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .transaction-item.expense {{
                border-left-color: #dc3545;
            }}
            .transaction-item .transaction-info {{
                flex: 1;
                min-width: 200px;
            }}
            .transaction-item .transaction-info strong {{
                font-size: 16px;
                color: #2c3e50;
                display: block;
                margin-bottom: 5px;
            }}
            .transaction-item .transaction-info .date {{
                font-size: 13px;
                color: #7f8c8d;
            }}
            .transaction-item .transaction-amount {{
                font-weight: 700;
                font-size: 18px;
                color: #2c3e50;
            }}
            .transaction-item.expense .transaction-amount {{
                color: #dc3545;
            }}
            .goal-item {{
                padding: 25px;
                margin: 15px 0;
                background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
                border-radius: 12px;
                border-left: 5px solid #ffc107;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }}
            .goal-item strong {{
                font-size: 18px;
                color: #2c3e50;
                display: block;
                margin-bottom: 12px;
            }}
            .goal-info {{
                font-size: 14px;
                color: #7f8c8d;
                margin: 8px 0;
            }}
            .progress-bar {{
                background: #e9ecef;
                height: 25px;
                border-radius: 15px;
                overflow: hidden;
                margin: 15px 0;
                box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .progress-fill {{
                background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                height: 100%;
                transition: width 0.5s ease;
                border-radius: 15px;
                position: relative;
                overflow: hidden;
            }}
            .progress-fill::after {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            }}
            @keyframes shimmer {{
                0% {{ transform: translateX(-100%); }}
                100% {{ transform: translateX(100%); }}
            }}
            .footer {{
                text-align: center;
                color: #7f8c8d;
                margin-top: 0;
                padding: 40px;
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border-top: 3px solid;
                border-image: linear-gradient(90deg, #667eea, #764ba2) 1;
            }}
            .footer p {{
                margin: 8px 0;
                font-size: 14px;
            }}
            .footer .brand {{
                font-weight: 700;
                color: #667eea;
                font-size: 18px;
                margin-bottom: 10px;
            }}
            .insight-box {{
                background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
                border-left: 5px solid #2196F3;
                padding: 20px;
                margin: 15px 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.1);
                font-size: 15px;
                line-height: 1.8;
            }}
            .insight-box strong {{
                color: #1976d2;
            }}
            .icon {{
                font-size: 28px;
                margin-right: 8px;
            }}
            @media (max-width: 600px) {{
                .email-container {{
                    border-radius: 0;
                }}
                .header {{
                    padding: 35px 25px;
                }}
                .header h1 {{
                    font-size: 28px;
                }}
                .section {{
                    padding: 25px 20px;
                }}
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                .transaction-item {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="header-content">
                    <h1>📊 FinFit Financial Report</h1>
                    <div class="subtitle">Your comprehensive financial overview</div>
                    <div class="date-badge">📅 Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="icon">💰</span> Financial Summary</h2>
                <div class="stats-grid">
                    <div class="stat-box income">
                        <div class="stat-label">Total Income</div>
                        <div class="stat-value">₹{income:,.2f}</div>
                    </div>
                    <div class="stat-box expense">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">₹{expense:,.2f}</div>
                    </div>
                    <div class="stat-box balance">
                        <div class="stat-label">Current Balance</div>
                        <div class="stat-value">₹{balance:,.2f}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2><span class="icon">📈</span> Spending by Category</h2>
                <ul class="category-list">
    """
    
    # Add category breakdown
    sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
    if sorted_categories:
        for idx, (category, amount) in enumerate(sorted_categories):
            percentage = (amount / expense * 100) if expense > 0 else 0
            color_class = f"category-bar-{(idx % 6) + 1}" if idx < 6 else "category-bar-default"
            html += f"""
                    <li class="category-item">
                        <div class="category-header">
                            <span class="category-name">{category}</span>
                            <div style="display: flex; align-items: center;">
                                <span class="category-amount">₹{amount:,.2f}</span>
                                <span class="category-percentage">({percentage:.1f}%)</span>
                            </div>
                        </div>
                        <div class="category-bar-container">
                            <div class="category-bar {color_class}" style="width: {min(percentage, 100)}%"></div>
                        </div>
                    </li>
            """
    else:
        html += '<li style="padding: 30px; text-align: center; color: #7f8c8d; font-style: italic;">No spending categories to display yet.</li>'
    
    html += """
            </ul>
        </div>
        
        <div class="section">
            <h2><span class="icon">📝</span> Recent Transactions</h2>
    """
    
    # Add recent transactions
    if recent_transactions:
        for t in recent_transactions:
            type_icon = "💰" if t.type == "income" else "💸"
            html += f"""
            <div class="transaction-item {t.type}">
                <div class="transaction-info">
                    <strong>{type_icon} {t.category}</strong>
                    <span class="date">{t.date}</span>
                    {f'<div style="font-size: 13px; color: #7f8c8d; margin-top: 5px;">{t.note}</div>' if t.note else ''}
                </div>
                <div class="transaction-amount">₹{t.amount:,.2f}</div>
            </div>
        """
    else:
        html += '<p style="color: #7f8c8d; text-align: center; padding: 20px;">No recent transactions to display.</p>'
    
    html += """
        </div>
        
        <div class="section">
            <h2><span class="icon">🎯</span> Financial Goals</h2>
    """
    
    # Add goals
    if active_goals:
        for g in active_goals:
            progress = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            remaining = g.target_amount - g.current_amount
            progress_color = "#28a745" if progress >= 75 else "#ffc107" if progress >= 50 else "#dc3545"
            html += f"""
            <div class="goal-item">
                <strong>🎯 {g.name}</strong>
                <div class="goal-info">Target: ₹{g.target_amount:,.2f} | Current: ₹{g.current_amount:,.2f}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(progress, 100)}%"></div>
                </div>
                <div class="goal-info">
                    <strong style="color: {progress_color};">Progress: {progress:.1f}%</strong> | 
                    Remaining: ₹{remaining:,.2f} | 
                    Deadline: {g.deadline}
                </div>
            </div>
            """
    else:
        html += '<p style="color: #7f8c8d; text-align: center; padding: 20px; font-style: italic;">No active goals at the moment. Set a goal to start your financial journey! 🚀</p>'
    
    html += """
        </div>
        
        <div class="section">
            <h2><span class="icon">💡</span> Key Insights</h2>
    """
    
    # Add insights
    insights = []
    if expense > 0 and income > 0:
        savings_rate = ((income - expense) / income * 100)
        if savings_rate > 20:
            insights.append("✅ <strong>Excellent savings rate!</strong> You're saving more than 20% of your income. Keep up the fantastic work!")
        elif savings_rate > 10:
            insights.append("👍 <strong>Good savings rate.</strong> Consider increasing it to build a stronger financial foundation.")
        else:
            insights.append("⚠️ <strong>Low savings rate.</strong> Try to reduce expenses or increase income to improve your financial health.")
    
    if balance < 0:
        insights.append("⚠️ <strong>Negative balance detected.</strong> Focus on reducing expenses and increasing income to get back on track.")
    elif balance > 0:
        insights.append("✅ <strong>Positive balance!</strong> You're managing your finances well. Consider investing your surplus.")
    
    if category_expenses:
        top_category = max(category_expenses.items(), key=lambda x: x[1])
        insights.append(f"📊 <strong>Top spending category:</strong> {top_category[0]} (₹{top_category[1]:,.2f}). Consider reviewing this area for potential savings.")
    
    if active_goals:
        insights.append(f"🎯 <strong>Active goals:</strong> You have {len(active_goals)} financial goal(s). Keep up the progress and stay motivated!")
    else:
        insights.append("💡 <strong>Goal setting tip:</strong> Consider setting financial goals to stay motivated and track your progress effectively.")
    
    if not insights:
        insights.append("💡 <strong>Getting started:</strong> Start tracking your expenses and income to gain valuable insights into your financial habits.")
    
    for insight in insights:
        html += f'<div class="insight-box">{insight}</div>'
    
    html += """
        </div>
        
        <div class="footer">
            <div class="brand">FinFit</div>
            <p>Your Personal Finance Assistant</p>
            <p style="margin-top: 15px; font-size: 12px; opacity: 0.8;">This report was automatically generated for your convenience.</p>
            <p style="font-size: 12px; opacity: 0.8;">For questions or support, visit your FinFit dashboard.</p>
        </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate and email financial report"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_email = user.email
    
    # Check if email is configured
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return jsonify({
            'error': 'Email service not configured.',
            'instructions': [
                '1. For Gmail: Create an App Password at https://myaccount.google.com/apppasswords',
                '2. Set environment variables:',
                '   - Windows PowerShell: $env:SMTP_EMAIL="your-email@gmail.com"; $env:SMTP_PASSWORD="your-app-password"',
                '   - Windows CMD: set SMTP_EMAIL=your-email@gmail.com && set SMTP_PASSWORD=your-app-password',
                '   - Linux/Mac: export SMTP_EMAIL=your-email@gmail.com && export SMTP_PASSWORD=your-app-password',
                '3. Restart the Flask application'
            ]
        }), 500
    
    try:
        # Generate report HTML
        report_html = generate_financial_report(user.id)
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'FinFit Financial Report - {datetime.now().strftime("%B %Y")}'
        msg['From'] = SMTP_EMAIL
        msg['To'] = user_email
        
        # Attach HTML content
        html_part = MIMEText(report_html, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        return jsonify({
            'message': f'Financial report sent successfully to {user_email}',
            'email': user_email
        })
        
    except smtplib.SMTPAuthenticationError:
        return jsonify({'error': 'Email authentication failed. Please check SMTP credentials.'}), 500
    except smtplib.SMTPException as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error generating report: {str(e)}'}), 500

# --- PaymentRequest / Merchant QR ---
def generate_upi_deeplink(upi_id, amount, description, token):
    """Generate UPI payment deeplink"""
    # Format: upi://pay?pa=<UPI_ID>&am=<AMOUNT>&tn=<DESCRIPTION>&tr=<TOKEN>
    upi_id_encoded = upi_id.replace('@', '%40')
    description_encoded = description.replace(' ', '%20') if description else ''
    deeplink = f"upi://pay?pa={upi_id_encoded}&am={amount:.2f}&tn={description_encoded}&tr={token}"
    return deeplink

def generate_qr_code(data):
    """Generate QR code image as base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_base64}"

@app.route('/api/payment-requests', methods=['POST'])
def create_payment_request():
    """Create a new payment request and return UPI QR code"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.json
    amount = float(data.get('amount', 0))
    description = data.get('description', 'Payment')
    upi_id = data.get('upi_id', '').strip()
    payer_email = data.get('payer_email', '').strip()  # Optional: email to send dummy transaction
    
    if amount <= 0:
        return jsonify({'error': 'Amount must be greater than 0'}), 400
    if not upi_id:
        return jsonify({'error': 'UPI ID is required'}), 400
    
    # Generate unique token
    token = secrets.token_urlsafe(16)
    
    # Create payment request
    payment_req = PaymentRequest(
        merchant_id=user.id,
        amount=amount,
        description=description,
        upi_id=upi_id,
        token=token,
        status='PENDING',
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(payment_req)
    db.session.commit()
    
    # Generate UPI deeplink and QR code
    deeplink = generate_upi_deeplink(upi_id, amount, description, token)
    qr_code = generate_qr_code(deeplink)
    
    # If payer_email provided, send dummy transaction email and trigger sync
    if payer_email:
        # Send dummy transaction email in background
        Thread(target=lambda: send_dummy_transaction_email(
            user.email, payer_email, amount, description, token
        ), daemon=True).start()
        
        # Trigger immediate sync after a short delay (to allow email to be delivered)
        def delayed_sync():
            time.sleep(5)  # Wait 5 seconds for email to be delivered
            trigger_immediate_sync()
        Thread(target=delayed_sync, daemon=True).start()
    
    return jsonify({
        'id': payment_req.id,
        'token': token,
        'amount': amount,
        'description': description,
        'upi_id': upi_id,
        'status': 'PENDING',
        'deeplink': deeplink,
        'qr_code': qr_code,
        'created_at': payment_req.created_at
    }), 201

@app.route('/api/payment-requests', methods=['GET'])
def get_payment_requests():
    """Get all payment requests for current merchant"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    requests_list = PaymentRequest.query.filter_by(merchant_id=user.id).order_by(PaymentRequest.created_at.desc()).all()
    return jsonify([{
        'id': pr.id,
        'amount': pr.amount,
        'description': pr.description,
        'upi_id': pr.upi_id,
        'status': pr.status,
        'token': pr.token,
        'created_at': pr.created_at,
        'paid_at': pr.paid_at,
        'payer_email': pr.payer_email
    } for pr in requests_list])

@app.route('/api/payment-requests/<int:request_id>', methods=['GET'])
def get_payment_request_status(request_id):
    """Get payment request status by ID"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    pr = PaymentRequest.query.filter_by(id=request_id, merchant_id=user.id).first()
    if not pr:
        return jsonify({'error': 'Payment request not found'}), 404
    
    deeplink = generate_upi_deeplink(pr.upi_id, pr.amount, pr.description or '', pr.token)
    qr_code = generate_qr_code(deeplink) if pr.status == 'PENDING' else None
    
    return jsonify({
        'id': pr.id,
        'amount': pr.amount,
        'description': pr.description,
        'upi_id': pr.upi_id,
        'status': pr.status,
        'token': pr.token,
        'created_at': pr.created_at,
        'paid_at': pr.paid_at,
        'payer_email': pr.payer_email,
        'deeplink': deeplink,
        'qr_code': qr_code
    })

@app.route('/api/payment-requests/<int:request_id>/simulate-payment', methods=['POST'])
def simulate_payment(request_id):
    """Simulate payment - send transaction email and auto-log it"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    pr = PaymentRequest.query.filter_by(id=request_id, merchant_id=user.id).first()
    if not pr:
        return jsonify({'error': 'Payment request not found'}), 404
    
    if pr.status == 'PAID':
        return jsonify({'error': 'Payment already processed'}), 400
    
    # Get payer email from request or use merchant's email for testing
    data = request.json or {}
    payer_email = data.get('payer_email', '').strip() or user.email
    
    # Check if payer has Gmail connected
    payer_gmail = GmailConnection.query.filter_by(user_id=user.id, is_active=True).first()
    if not payer_gmail:
        return jsonify({
            'error': 'Gmail not connected. Please connect your Gmail account in Profile settings to enable auto-logging.'
        }), 400
    
    # Reset last_sync_at to force checking recent emails
    payer_gmail.last_sync_at = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    db.session.commit()
    
    print(f"🔄 Simulating payment: Sending email to {payer_email} for ₹{pr.amount}")
    
    # Send dummy transaction email to payer's Gmail
    email_sent = send_dummy_transaction_email(
        merchant_email=user.email,
        payer_email=payer_email,
        amount=pr.amount,
        description=pr.description or 'Payment',
        payment_token=pr.token
    )
    
    if not email_sent:
        return jsonify({
            'error': 'Failed to send transaction email. Please check SMTP configuration.'
        }), 500
    
    # Trigger immediate sync after delay to read the email (only once to avoid duplicates)
    def delayed_sync_and_check():
        print(f"⏳ Waiting 12 seconds for email delivery...")
        time.sleep(12)  # Wait for email to be delivered and indexed by Gmail
        print(f"🔄 Triggering sync...")
        trigger_immediate_sync()
        print(f"✅ Sync triggered. Check transactions.")
    
    Thread(target=delayed_sync_and_check, daemon=True).start()
    
    return jsonify({
        'message': f'Transaction email sent to {payer_email}. System will automatically detect and log the transaction within 15-20 seconds.',
        'status': 'processing',
        'email_sent': True
    })

# --- Gmail OAuth Integration ---
GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID', '')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '')
GMAIL_REDIRECT_URI = os.getenv('GMAIL_REDIRECT_URI', 'http://localhost:5000/api/gmail/callback')

@app.route('/api/gmail/connect', methods=['GET'])
def gmail_connect():
    """Initiate Gmail OAuth flow"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    if not GMAIL_CLIENT_ID:
        return jsonify({'error': 'Gmail OAuth not configured. Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET'}), 500
    
    # Generate OAuth URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GMAIL_CLIENT_ID}&"
        f"redirect_uri={GMAIL_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={user.id}"
    )
    
    return jsonify({'auth_url': auth_url})

@app.route('/api/gmail/callback', methods=['GET'])
@app.route('/api/gmail/call', methods=['GET'])  # Fallback for typo in redirect URI
def gmail_callback():
    """Handle Gmail OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')  # user_id
    error = request.args.get('error')
    
    # Debug logging
    print(f"Gmail callback received - code: {code[:20] if code else None}..., state: {state}, error: {error}")
    
    if error:
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connection Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Gmail Connection Failed</h2>
                <p>Error: {error}</p>
                <p>You can close this window and try again.</p>
                <script>
                    window.opener.postMessage({{type: "gmail_connected", success: false, error: "{error}"}}, "*");
                    setTimeout(() => window.close(), 3000);
                </script>
            </div>
        </body>
        </html>
        '''
        return error_html, 400
    
    if not code or not state:
        error_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connection Error</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Missing Authorization Code</h2>
                <p>Please try connecting again.</p>
                <script>
                    window.opener.postMessage({type: "gmail_connected", success: false, error: "Missing authorization code"}, "*");
                    setTimeout(() => window.close(), 3000);
                </script>
            </div>
        </body>
        </html>
        '''
        return error_html, 400
    
    try:
        # Use the actual request URL for redirect_uri to match what Google sent
        # This handles both /api/gmail/callback and /api/gmail/call
        actual_redirect_uri = request.url.split('?')[0]  # Get URL without query params
        
        # Exchange code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': GMAIL_CLIENT_ID,
            'client_secret': GMAIL_CLIENT_SECRET,
            'redirect_uri': actual_redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        print(f"Token exchange - redirect_uri: {actual_redirect_uri}")
        
        response = requests.post(token_url, data=token_data)
        
        if not response.ok:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error_description', error_data.get('error', response.text))
            print(f"Token exchange failed: {error_msg}")
            raise Exception(f"Token exchange failed: {error_msg}")
        
        tokens = response.json()
        
        # Store connection
        user_id = int(state)
        gmail_conn = GmailConnection.query.filter_by(user_id=user_id).first()
        
        if gmail_conn:
            gmail_conn.access_token = tokens['access_token']
            gmail_conn.refresh_token = tokens.get('refresh_token', gmail_conn.refresh_token)
            gmail_conn.token_expiry = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            gmail_conn.is_active = True
        else:
            gmail_conn = GmailConnection(
                user_id=user_id,
                access_token=tokens['access_token'],
                refresh_token=tokens.get('refresh_token', ''),
                token_expiry=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                connected_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                is_active=True
            )
            db.session.add(gmail_conn)
        
        db.session.commit()
        
        # Return success HTML page
        success_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connected Successfully</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .success-icon {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h2>Gmail Connected Successfully!</h2>
                <p>You can close this window now.</p>
                <script>
                    window.opener.postMessage({type: "gmail_connected", success: true}, "*");
                    setTimeout(() => window.close(), 2000);
                </script>
            </div>
        </body>
        </html>
        '''
        return success_html
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"OAuth error: {e.response.text if hasattr(e, 'response') else str(e)}"
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connection Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Gmail Connection Failed</h2>
                <p>{error_msg}</p>
                <p>Please check your Gmail OAuth configuration.</p>
                <script>
                    window.opener.postMessage({{type: "gmail_connected", success: false, error: "{error_msg}"}}, "*");
                    setTimeout(() => window.close(), 5000);
                </script>
            </div>
        </body>
        </html>
        '''
        return error_html, 500
    except Exception as e:
        error_msg = f"Failed to connect Gmail: {str(e)}"
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Connection Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Gmail Connection Failed</h2>
                <p>{error_msg}</p>
                <script>
                    window.opener.postMessage({{type: "gmail_connected", success: false, error: "{error_msg}"}}, "*");
                    setTimeout(() => window.close(), 5000);
                </script>
            </div>
        </body>
        </html>
        '''
        return error_html, 500

@app.route('/api/gmail/status', methods=['GET'])
def gmail_status():
    """Get Gmail connection status"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    gmail_conn = GmailConnection.query.filter_by(user_id=user.id).first()
    if not gmail_conn or not gmail_conn.is_active:
        return jsonify({'connected': False})
    
    return jsonify({
        'connected': True,
        'connected_at': gmail_conn.connected_at,
        'last_sync_at': gmail_conn.last_sync_at
    })

@app.route('/api/gmail/disconnect', methods=['POST'])
def gmail_disconnect():
    """Disconnect Gmail integration"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    gmail_conn = GmailConnection.query.filter_by(user_id=user.id).first()
    if gmail_conn:
        gmail_conn.is_active = False
        db.session.commit()
    
    return jsonify({'message': 'Gmail disconnected successfully'})

# --- Email Parsing and Transaction Matching ---
def parse_upi_transaction_email(email_body, email_subject):
    """Parse UPI/bank transaction details from email"""
    # Common patterns for Indian UPI/bank transaction emails
    text = f"{email_subject} {email_body}"
    text_upper = text.upper()
    
    # Amount patterns - more comprehensive for Indian formats
    # Priority order: most specific first
    amount_patterns = [
        r'Sent\s+Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Sent Rs.1.00 (HDFC format)
        r'Paid\s+Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Paid Rs.1.00
        r'Received\s+Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Received Rs.1.00
        r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+Sent',  # Rs.1.00 Sent
        r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+Paid',  # Rs.1.00 Paid
        r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Rs. 1,000.00 (general)
        r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',     # INR 1,000.00
        r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',       # ₹ 1,000.00
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*Rs',     # 1,000.00 Rs
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*INR',    # 1,000.00 INR
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*DEBITED', # 1,000.00 DEBITED
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*CREDITED', # 1,000.00 CREDITED
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*PAID',    # 1,000.00 PAID
        r'AMOUNT[:\s]+Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # AMOUNT: Rs. 1,000.00
        r'AMOUNT[:\s]+INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',    # AMOUNT: INR 1,000.00
        r'AMOUNT[:\s]+₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',      # AMOUNT: ₹ 1,000.00
    ]
    
    amount = None
    matched_pattern = None
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Take the first match and clean it (remove commas)
                amount_str = str(matches[0]).replace(',', '')
                amount = float(amount_str)
                matched_pattern = pattern
                print(f"Parsed amount: ₹{amount} from pattern: {pattern[:50]}")
                break
            except Exception as e:
                print(f"Error parsing amount {matches[0]}: {e}")
                continue
    
    # Transaction ID/Reference patterns - HDFC uses "Ref"
    transaction_id = None
    txn_patterns = [
        r'Ref\s+([A-Z0-9]+)',  # Ref xxxxxxxxxxxxx (HDFC format)
        r'Ref\s*No[:\s]+([A-Z0-9]+)',  # Ref No: xxxxx
        r'Reference\s*No[:\s]+([A-Z0-9]+)',  # Reference No: xxxxx
        r'Transaction\s*ID[:\s]+([A-Z0-9]+)',
        r'Txn\s*ID[:\s]+([A-Z0-9]+)',
        r'TXN\s*ID[:\s]+([A-Z0-9]+)',
        r'UPI\s*Ref\s*No[:\s]+([A-Z0-9]+)',
    ]
    
    for pattern in txn_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            transaction_id = match.group(1).strip()
            print(f"Found transaction ID: {transaction_id}")
            break
    
    # Determine if it's a payment (debit) or refund (credit)
    # HDFC format: "Sent Rs.X" = payment made (debit) - money going OUT
    # "Received/Credited" = payment received (credit) - money coming IN
    
    # Check for debit keywords (money going OUT)
    is_debit = any(keyword in text_upper for keyword in [
        'DEBITED', 'PAID', 'PAYMENT', 'SENT', 'TRANSFERRED', 
        'FROM HDFC', 'FROM BANK', 'DEBIT', 'SENT RS'
    ])
    
    # Check for credit keywords (money coming IN)
    is_credit = any(keyword in text_upper for keyword in [
        'CREDITED', 'RECEIVED', 'DEPOSITED', 'TO YOUR ACCOUNT',
        'CREDIT', 'RECEIVE', 'RECEIVED RS', 'CREDITED TO'
    ])
    
    # If both found, prioritize based on context
    # "Sent" is stronger indicator of debit
    if 'SENT' in text_upper or 'SENT RS' in text_upper:
        is_debit = True
        is_credit = False
    elif 'RECEIVED' in text_upper or 'CREDITED' in text_upper or 'CREDITED TO' in text_upper:
        is_credit = True
        is_debit = False
    
    # If amount found, log for debugging
    if amount:
        print(f"Email parse result - Amount: ₹{amount}, Debit: {is_debit}, Credit: {is_credit}")
        print(f"  Subject: {email_subject[:60]}")
        print(f"  Body preview: {email_body[:100]}")
        if transaction_id:
            print(f"  Transaction ID: {transaction_id}")
    
    return {
        'amount': amount,
        'transaction_id': transaction_id,
        'is_payment': is_debit,  # Payment made by user
        'is_credit': is_credit   # Payment received
    }

def extract_email_body(payload):
    """Recursively extract email body text from payload"""
    body = ''
    
    if payload.get('mimeType') == 'text/plain':
        if 'body' in payload and 'data' in payload['body']:
            try:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            except:
                pass
    elif payload.get('mimeType') == 'text/html':
        if 'body' in payload and 'data' in payload['body']:
            try:
                html_body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
                # Simple HTML tag removal
                body = re.sub(r'<[^>]+>', '', html_body)
            except:
                pass
    
    # Check parts recursively
    if 'parts' in payload:
        for part in payload['parts']:
            part_body = extract_email_body(part)
            if part_body:
                body += ' ' + part_body
    
    return body.strip()

def refresh_gmail_token(gmail_conn):
    """Refresh Gmail access token using refresh token"""
    if not gmail_conn.refresh_token:
        return False
    
    try:
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': GMAIL_CLIENT_ID,
            'client_secret': GMAIL_CLIENT_SECRET,
            'refresh_token': gmail_conn.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=token_data)
        if response.ok:
            tokens = response.json()
            gmail_conn.access_token = tokens['access_token']
            gmail_conn.token_expiry = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error refreshing token: {e}")
    
    return False

def fetch_gmail_messages(access_token, max_results=50, after_date=None):
    """Fetch recent emails from Gmail"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Build query - search for transaction-related emails
    # Common Indian UPI/bank email senders including HDFC
    query_parts = [
        'subject:(payment OR transaction OR "upi" OR "bank" OR "debit" OR "credit" OR "paid" OR "received" OR "sent")',
        'from:(noreply@paytm.com OR alerts@paytm.com OR no-reply@phonepe.com OR alerts@phonepe.com OR alerts@googlepay.com OR no-reply@googlepay.com OR alerts@upi OR "hdfc" OR "bank" OR "payment" OR "noreply")'
    ]
    
    # Also search in body for HDFC format
    query = ' OR '.join(query_parts) + ' OR (body:"Sent Rs" OR body:"From HDFC" OR body:"Ref ")'
    
    # Add date filter if provided
    if after_date:
        # Format: after:YYYY/MM/DD
        date_str = after_date.strftime('%Y/%m/%d')
        query += f' after:{date_str}'
    
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults={max_results}'
    
    try:
        response = requests.get(url, headers=headers)
        
        # Check if token expired
        if response.status_code == 401:
            print("Access token expired, need to refresh")
            return None  # Signal to refresh token
        
        response.raise_for_status()
        messages = response.json().get('messages', [])
        
        print(f"Found {len(messages)} transaction-related emails")
        
        email_details = []
        for msg in messages:
            try:
                msg_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg["id"]}?format=full'
                msg_response = requests.get(msg_url, headers=headers)
                msg_response.raise_for_status()
                msg_data = msg_response.json()
                
                # Extract subject
                subject = ''
                for header in msg_data.get('payload', {}).get('headers', []):
                    if header['name'].lower() == 'subject':
                        subject = header['value']
                        break
                
                # Extract body using recursive function
                body = extract_email_body(msg_data.get('payload', {}))
                
                # Extract date
                date_str = ''
                for header in msg_data.get('payload', {}).get('headers', []):
                    if header['name'].lower() == 'date':
                        date_str = header['value']
                        break
                
                email_details.append({
                    'id': msg['id'],
                    'subject': subject,
                    'body': body,
                    'date': msg_data.get('internalDate', ''),
                    'date_str': date_str
                })
            except Exception as e:
                print(f"Error processing email {msg.get('id')}: {e}")
                continue
        
        return email_details
    except Exception as e:
        print(f"Error fetching Gmail messages: {e}")
        import traceback
        traceback.print_exc()
        return []

def sync_gmail_transactions():
    """Background job to sync Gmail transactions"""
    with app.app_context():
        connections = GmailConnection.query.filter_by(is_active=True).all()
        print(f"Syncing Gmail for {len(connections)} users...")
        
        for conn in connections:
            try:
                # Determine date range - check emails from last 7 days or since last sync
                # But always check at least last 10 minutes to catch recent simulated payments
                after_date = None
                min_recent_date = datetime.now() - timedelta(minutes=10)  # Always check last 10 minutes
                
                if conn.last_sync_at:
                    try:
                        sync_date = datetime.strptime(conn.last_sync_at, '%Y-%m-%d %H:%M:%S')
                        # Use the more recent of: last sync time or 10 minutes ago
                        after_date = max(sync_date, min_recent_date)
                    except:
                        after_date = min_recent_date
                else:
                    after_date = min_recent_date
                
                print(f"📅 Checking emails after: {after_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Fetch emails
                emails = fetch_gmail_messages(conn.access_token, max_results=100, after_date=after_date)
                
                # If token expired, try to refresh
                if emails is None:
                    print(f"Token expired for user {conn.user_id}, attempting refresh...")
                    if refresh_gmail_token(conn):
                        emails = fetch_gmail_messages(conn.access_token, max_results=100, after_date=after_date)
                    else:
                        print(f"Failed to refresh token for user {conn.user_id}")
                        continue
                
                if not emails:
                    print(f"No new emails found for user {conn.user_id}")
                    conn.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    db.session.commit()
                    continue
                
                print(f"Processing {len(emails)} emails for user {conn.user_id}")
                
                processed_count = 0
                processed_email_ids = set()  # Track processed email IDs to prevent duplicates
                
                for email in emails:
                    try:
                        email_id = email.get('id')
                        if not email_id:
                            continue
                        
                        # Skip if we already processed this email in this sync run
                        if email_id in processed_email_ids:
                            print(f"   ⚠️  Skipping already processed email ID: {email_id}")
                            continue
                        
                        print(f"\n📧 Processing email ID: {email_id}")
                        print(f"   Subject: {email['subject'][:60]}")
                        print(f"   Body preview: {email['body'][:200]}")
                        
                        # Parse transaction details
                        parsed = parse_upi_transaction_email(email['body'], email['subject'])
                        
                        if not parsed['amount']:
                            print(f"   ⚠️  No amount found in email, skipping")
                            processed_email_ids.add(email_id)  # Mark as processed even if no amount
                            continue
                        
                        print(f"   ✅ Parsed: Amount=₹{parsed['amount']}, is_payment={parsed['is_payment']}, is_credit={parsed.get('is_credit', False)}")
                        
                        # Get email date
                        email_date = datetime.now().strftime('%Y-%m-%d')
                        if email.get('date_str'):
                            try:
                                from email.utils import parsedate_to_datetime
                                email_date_obj = parsedate_to_datetime(email['date_str'])
                                email_date = email_date_obj.strftime('%Y-%m-%d')
                            except:
                                pass
                        
                        # Determine transaction type based on email content
                        transaction_type = 'expense' if (parsed['is_payment'] and not parsed.get('is_credit')) else 'income'
                        
                        # Check for duplicate transaction - strict check by amount, date, AND type
                        existing = Transaction.query.filter(
                            Transaction.user_id == conn.user_id,
                            Transaction.amount == parsed['amount'],
                            Transaction.date == email_date,
                            Transaction.type == transaction_type
                        ).first()
                        
                        if existing:
                            print(f"   ⚠️  DUPLICATE SKIPPED: Transaction ₹{parsed['amount']} ({transaction_type}) on {email_date} already exists")
                            print(f"      Existing ID: {existing.id}, Note: {existing.note[:50]}")
                            processed_email_ids.add(email_id)
                            continue
                        
                        # Mark email as being processed
                        processed_email_ids.add(email_id)
                        
                        # Try to match with PaymentRequest by amount and recent time (for merchant)
                        # Check last 48 hours for payment requests
                        recent_time = datetime.now() - timedelta(hours=48)
                        payment_req = PaymentRequest.query.filter(
                            PaymentRequest.amount == parsed['amount'],
                            PaymentRequest.status == 'PENDING',
                            PaymentRequest.created_at >= recent_time.strftime('%Y-%m-%d %H:%M:%S')
                        ).first()
                        
                        print(f"  Checking payment request match: amount={parsed['amount']}, is_payment={parsed['is_payment']}, is_credit={parsed.get('is_credit', False)}, found_req={payment_req is not None}")
                        
                        # Match if: payment request exists AND (it's a credit OR it's a payment/debit from user)
                        # "Sent" emails are debits from user, which should match pending payment requests
                        if payment_req and (parsed.get('is_credit') or parsed['is_payment']):
                            print(f"   🎯 MATCHED Payment Request ID {payment_req.id} for ₹{payment_req.amount}")
                            
                            # Mark payment request as paid
                            payment_req.status = 'PAID'
                            payment_req.paid_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            payment_req.payer_email = conn.user.email
                            
                            # Classify transaction based on email content:
                            # - "Sent" = money going OUT → Expense
                            # - "Received/Credited" = money coming IN → Income
                            
                            if parsed['is_payment'] and not parsed.get('is_credit'):
                                # Email says "Sent" - money going OUT of user's account → EXPENSE
                                transaction = Transaction(
                                    user_id=conn.user_id,
                                    type='expense',
                                    category='UPI Payment',
                                    amount=parsed['amount'],
                                    date=email_date,
                                    note=f"Payment sent: {payment_req.description or 'Merchant QR'} - Token: {payment_req.token}"
                                )
                                db.session.add(transaction)
                                db.session.flush()
                                payment_req.transaction_id = transaction.id
                                print(f"   💸 Logged as EXPENSE (money sent out of account)")
                                
                            elif parsed.get('is_credit'):
                                # Email says "Received/Credited" - money coming IN to user's account → INCOME
                                transaction = Transaction(
                                    user_id=conn.user_id,
                                    type='income',
                                    category='Payment Received',
                                    amount=parsed['amount'],
                                    date=email_date,
                                    note=f"Payment received: {payment_req.description or 'Merchant QR'} - Token: {payment_req.token}"
                                )
                                db.session.add(transaction)
                                db.session.flush()
                                payment_req.transaction_id = transaction.id
                                print(f"   💰 Logged as INCOME (money received into account)")
                            
                            db.session.commit()
                            print(f"   ✅ SUCCESS: Payment request marked PAID, transaction logged!")
                            processed_count += 1
                            # Don't trigger another sync here - it causes duplicates
                        elif parsed['is_payment'] and not parsed.get('is_credit') and not payment_req:
                            # Auto-log as expense for the user (payment made by user, no matching payment request)
                            # Email says "Sent" - money going out
                            print(f"   💸 Auto-logging EXPENSE (money sent out): ₹{parsed['amount']}")
                            transaction = Transaction(
                                user_id=conn.user_id,
                                type='expense',
                                category='UPI Payment',
                                amount=parsed['amount'],
                                date=email_date,
                                note=f"Auto-logged from email: {email['subject'][:100]}"
                            )
                            db.session.add(transaction)
                            db.session.commit()
                            print(f"   ✅ SUCCESS: Expense logged: ₹{parsed['amount']} - {email['subject'][:50]}")
                            processed_count += 1
                        elif parsed.get('is_credit') and not payment_req:
                            # Auto-log as income for the user (payment received, no matching payment request)
                            # Email says "Received/Credited" - money coming in
                            print(f"   💰 Auto-logging INCOME (money received): ₹{parsed['amount']}")
                            transaction = Transaction(
                                user_id=conn.user_id,
                                type='income',
                                category='Payment Received',
                                amount=parsed['amount'],
                                date=email_date,
                                note=f"Auto-logged from email: {email['subject'][:100]}"
                            )
                            db.session.add(transaction)
                            db.session.commit()
                            print(f"   ✅ SUCCESS: Income logged: ₹{parsed['amount']} - {email['subject'][:50]}")
                            processed_count += 1
                            # Don't trigger another sync here - it causes duplicates
                            
                            # Trigger immediate sync again to catch any new emails
                            def delayed_sync_expense():
                                time.sleep(2)
                                trigger_immediate_sync()
                            Thread(target=delayed_sync_expense, daemon=True).start()
                    except Exception as e:
                        print(f"Error processing email {email.get('id')}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                # Update last sync time
                conn.last_sync_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.commit()
                print(f"✅ Sync complete for user {conn.user_id}: {processed_count} transactions processed")
                
            except Exception as e:
                print(f"Error syncing Gmail for user {conn.user_id}: {e}")
                import traceback
                traceback.print_exc()

def trigger_immediate_sync():
    """Trigger immediate Gmail sync in background"""
    thread = Thread(target=sync_gmail_transactions, daemon=True)
    thread.start()

@app.route('/api/gmail/sync', methods=['POST'])
def manual_gmail_sync():
    """Manually trigger Gmail sync"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check if user has Gmail connected
    gmail_conn = GmailConnection.query.filter_by(user_id=user.id, is_active=True).first()
    if not gmail_conn:
        return jsonify({'error': 'Gmail not connected. Please connect your Gmail account first.'}), 400
    
    # Run sync in background thread
    thread = Thread(target=sync_gmail_transactions)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Sync started. Checking your emails for transactions...',
        'status': 'processing'
    })

def send_dummy_transaction_email(merchant_email, payer_email, amount, description, payment_token):
    """Send a dummy transaction email simulating bank payment notification"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("SMTP not configured, skipping email send")
        return False
    
    try:
        # Format email body in HDFC Bank style
        current_date = datetime.now().strftime('%d/%m/%y')
        ref_number = payment_token[:12].upper()  # Use first 12 chars of token as ref
        
        email_body = f"""Sent Rs.{amount:.2f}

From HDFC Bank A/C ****

To {merchant_email[:15]}

On {current_date}

Ref {ref_number}

Not You?

Call 1800-123-1234"""
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = payer_email
        msg['Subject'] = f'Payment Alert - Rs.{amount:.2f} sent'
        msg.attach(MIMEText(email_body, 'plain'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Sent dummy transaction email to {payer_email} for ₹{amount}")
        return True
    except Exception as e:
        print(f"Error sending dummy transaction email: {e}")
        return False

def trigger_immediate_sync():
    """Trigger immediate Gmail sync in background"""
    thread = Thread(target=sync_gmail_transactions, daemon=True)
    thread.start()

# Start background sync thread (runs every 2 minutes to avoid duplicates)
def start_background_sync():
    """Background thread to periodically sync Gmail transactions"""
    while True:
        time.sleep(120)  # 2 minutes to avoid duplicate processing
        try:
            sync_gmail_transactions()
        except Exception as e:
            print(f"Background sync error: {e}")

# Background sync thread will be started when app runs

# Serve frontend files
@app.route('/')
def index():
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from frontend directory"""
    # Don't intercept API routes
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    # If file doesn't exist, serve index.html (for SPA routing)
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Start background sync thread for Gmail transactions
        sync_thread = Thread(target=start_background_sync, daemon=True)
        sync_thread.start()

    print("\n" + "="*50)
    print("🚀 FinFit is running!")
    print("="*50)
    print(f"💻 Access at: http://127.0.0.1:5000")
    print("="*50 + "\n")

    # IMPORTANT: host is now 0.0.0.0
    app.run(debug=True, host='0.0.0.0', port=5000)
