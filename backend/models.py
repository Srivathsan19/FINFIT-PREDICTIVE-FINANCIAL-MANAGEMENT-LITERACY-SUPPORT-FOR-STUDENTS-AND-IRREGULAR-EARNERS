from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.String(20))
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10))  # 'income' or 'expense'
    category = db.Column(db.String(50))
    amount = db.Column(db.Float)
    date = db.Column(db.String(20))
    note = db.Column(db.String(200))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50))
    target_amount = db.Column(db.Float)
    current_amount = db.Column(db.Float)
    deadline = db.Column(db.String(20))

class PaymentRequest(db.Model):
    """Merchant payment request for UPI QR codes"""
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    upi_id = db.Column(db.String(100))  # Merchant UPI ID (e.g., merchant@paytm)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PAID, EXPIRED, CANCELLED
    token = db.Column(db.String(100), unique=True, nullable=False)  # Unique token for tracking
    created_at = db.Column(db.String(20))
    paid_at = db.Column(db.String(20))
    payer_email = db.Column(db.String(100))  # Email of payer (from transaction email)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)  # Linked FinFit transaction
    
    merchant = db.relationship('User', foreign_keys=[merchant_id], backref='payment_requests')
    transaction = db.relationship('Transaction', foreign_keys=[transaction_id], backref='payment_request')

class GmailConnection(db.Model):
    """Gmail OAuth connection for auto-logging transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    access_token = db.Column(db.Text)  # Encrypted OAuth access token
    refresh_token = db.Column(db.Text)  # Encrypted OAuth refresh token
    token_expiry = db.Column(db.String(20))  # Token expiry timestamp
    connected_at = db.Column(db.String(20))
    last_sync_at = db.Column(db.String(20))  # Last time emails were synced
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='gmail_connection')


# -----------------------------
# Adaptive Learning (Persistence)
# -----------------------------

class LearningModuleCompletion(db.Model):
    """
    Tracks which learning modules the user has completed so they don't show up again.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    module_key = db.Column(db.String(80), nullable=False, index=True)
    completed_at = db.Column(db.String(30), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_key', name='uq_learning_module_completion'),
    )


class LearningRecommendationCache(db.Model):
    """
    Stores the ranked recommendation list (module keys + metadata) for a user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    recommendations_json = db.Column(db.Text, nullable=False, default='[]')
    updated_at = db.Column(db.String(30), nullable=False)


class ModuleContentCache(db.Model):
    """
    Stores Ollama-generated module content per user/module with a profile fingerprint and timestamp.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    module_key = db.Column(db.String(80), nullable=False, index=True)
    profile_fingerprint = db.Column(db.String(120), nullable=False, index=True)
    generated_content = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.String(30), nullable=False)
    content_source = db.Column(db.String(20), nullable=False, default='ollama')  # 'ollama' | 'fallback'

    __table_args__ = (
        db.Index('idx_module_content_cache_user_module_fp', 'user_id', 'module_key', 'profile_fingerprint'),
    )


# -----------------------------
# Analytics Momentum (Stability)
# -----------------------------

class UserProfileHistory(db.Model):
    """
    Stores recent spending profile evaluations so the displayed KMeans label doesn't flip on single outliers.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    cluster_label = db.Column(db.String(30), nullable=False, index=True)  # Saver | Balanced | High-Spender
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.String(30), nullable=False)