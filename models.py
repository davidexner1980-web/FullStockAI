from app import db
from datetime import datetime
from flask_login import UserMixin
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    profile_type = db.Column(db.String(20), default='moderate')  # conservative, moderate, aggressive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlists = db.relationship('Watchlist', backref='user', lazy='dynamic')
    portfolios = db.relationship('Portfolio', backref='user', lazy='dynamic')
    alerts = db.relationship('Alert', backref='user', lazy='dynamic')

class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_crypto = db.Column(db.Boolean, default=False)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_crypto = db.Column(db.Boolean, default=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # price_above, price_below, prediction_change
    target_value = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    triggered_at = db.Column(db.DateTime)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    model_type = db.Column(db.String(20), nullable=False)  # random_forest, lstm, xgboost
    prediction_value = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    features_used = db.Column(db.Text)  # JSON string of features
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_crypto = db.Column(db.Boolean, default=False)

class BacktestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy_name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    initial_capital = db.Column(db.Float, nullable=False)
    final_value = db.Column(db.Float, nullable=False)
    total_return = db.Column(db.Float, nullable=False)
    max_drawdown = db.Column(db.Float, nullable=False)
    sharpe_ratio = db.Column(db.Float)
    num_trades = db.Column(db.Integer)
    win_rate = db.Column(db.Float)
    results_data = db.Column(db.Text)  # JSON string of detailed results
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemHealth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    api_status = db.Column(db.String(20))
    data_freshness = db.Column(db.Integer)  # minutes since last update
    overall_status = db.Column(db.String(20))  # OK, WARNING, ERROR
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
