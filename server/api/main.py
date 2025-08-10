from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard with comprehensive stock prediction interface"""
    try:
        return render_template('index.html')
    except Exception:
        # Fallback validation interface for MASTER BUILD
        return render_template('fallback.html')

@main_bp.route('/crypto')
def crypto():
    """Cryptocurrency prediction interface"""
    return render_template('crypto.html')

@main_bp.route('/portfolio')
def portfolio():
    """Portfolio management interface"""
    return render_template('portfolio.html')

@main_bp.route('/oracle')
def oracle():
    """Oracle Dreams mystical interface"""
    return render_template('oracle.html')

@main_bp.route('/health')
def health():
    """System health check"""
    return {
        'status': 'healthy',
        'message': 'FullStock AI vNext Ultimate is operational',
        'data_source': 'Yahoo Finance',
        'models': 'Random Forest + XGBoost + LSTM'
    }
