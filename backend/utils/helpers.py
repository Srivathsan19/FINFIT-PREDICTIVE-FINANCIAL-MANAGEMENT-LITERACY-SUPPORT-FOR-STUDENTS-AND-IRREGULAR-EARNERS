"""
Helper functions for the application
"""
from functools import wraps
from flask import session, jsonify
from models import User


def get_current_user():
    """Get current logged-in user from session"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

