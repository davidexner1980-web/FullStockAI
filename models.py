from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

class StockPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    current_price = db.Column(db.Float, nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    model_type = db.Column(db.String(20), nullable=False)
    features = db.Column(db.Text)  # JSON string of features used

class PriceAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    alert_type = db.Column(db.String(10), nullable=False)  # 'above' or 'below'
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    triggered_date = db.Column(db.DateTime)
    user_email = db.Column(db.String(120))

class SystemHealth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    component = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'healthy', 'warning', 'error'
    metrics = db.Column(db.Text)  # JSON string of health metrics
    message = db.Column(db.Text)

class ModelPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(30), nullable=False)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy_score = db.Column(db.Float)
    mse_score = db.Column(db.Float)
    mae_score = db.Column(db.Float)
    r2_score = db.Column(db.Float)
    test_samples = db.Column(db.Integer)
    training_samples = db.Column(db.Integer)
    hyperparameters = db.Column(db.Text)  # JSON string

class TradingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    ticker = db.Column(db.String(10), nullable=False)
    strategy = db.Column(db.String(50), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer, nullable=False)
    pnl = db.Column(db.Float)
    status = db.Column(db.String(20), default='open')  # 'open', 'closed', 'cancelled'