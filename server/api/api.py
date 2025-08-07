from flask import Blueprint, jsonify, request
from flask_socketio import emit
from app import cache, socketio
from server.ml.data_fetcher import DataFetcher
from server.ml.ml_models import MLModelManager
from server.utils.services.oracle_service import OracleService
from server.utils.services.crypto_service import CryptoService
from server.utils.services.backtesting import BacktestingEngine
from server.utils.services.notification_service import NotificationService
from server.utils.strategic.oracle_dreams import OracleDreams
from server.utils.strategic.curiosity_engine import CuriosityEngine
from server.utils.strategic.health_monitor import HealthMonitor
from server.utils.strategic.explainability import ExplainabilityService
from server.utils.strategic.portfolio_analyzer import PortfolioAnalyzer
from server.utils.strategic.quantum_forecast import QuantumForecast
import logging

api_bp = Blueprint('api', __name__)

# Initialize services
data_fetcher = DataFetcher()
ml_manager = MLModelManager()
oracle_service = OracleService()
crypto_service = CryptoService()
backtesting_engine = BacktestingEngine()
notification_service = NotificationService()

# Strategic services
oracle_dreams = OracleDreams()
curiosity_engine = CuriosityEngine()
health_monitor = HealthMonitor()
explainability = ExplainabilityService()
portfolio_analyzer = PortfolioAnalyzer()
quantum_forecast = QuantumForecast()

@api_bp.route('/predict/<ticker>')
@cache.cached(timeout=300)
def predict(ticker):
    """Main prediction endpoint with all models"""
    try:
        ticker = ticker.upper()
        
        # Get data
        data = data_fetcher.get_stock_data(ticker)
        if data is None:
            return jsonify({'error': 'Failed to fetch data for ticker'}), 400
        
        # Get predictions from all models (handle failures gracefully)
        rf_prediction = ml_manager.predict_random_forest(data)
        lstm_prediction = ml_manager.predict_lstm(data)
        xgb_prediction = ml_manager.predict_xgboost(data)
        
        # Filter successful predictions
        successful_predictions = []
        ensemble_confidence = 0
        
        if 'prediction' in rf_prediction and 'error' not in rf_prediction:
            successful_predictions.append(rf_prediction['prediction'])
            ensemble_confidence += rf_prediction.get('confidence', 0.5)
        
        if 'prediction' in xgb_prediction and 'error' not in xgb_prediction:
            successful_predictions.append(xgb_prediction['prediction'])
            ensemble_confidence += xgb_prediction.get('confidence', 0.5)
        
        if 'prediction' in lstm_prediction and 'error' not in lstm_prediction:
            successful_predictions.append(lstm_prediction['prediction'])
            ensemble_confidence += lstm_prediction.get('confidence', 0.5)
        
        if not successful_predictions:
            return jsonify({'error': 'All prediction models failed'}), 500
        
        # Ensemble prediction from successful models
        ensemble_pred = sum(successful_predictions) / len(successful_predictions)
        ensemble_confidence = ensemble_confidence / len(successful_predictions)
        
        # Calculate agreement level (only from successful predictions)
        if len(successful_predictions) > 1:
            agreement = 1.0 - (max(successful_predictions) - min(successful_predictions)) / max(successful_predictions)
        else:
            agreement = 1.0  # Single model, perfect agreement
        
        result = {
            'ticker': ticker,
            'current_price': data['Close'].iloc[-1],
            'predictions': {
                'random_forest': rf_prediction,
                'lstm': lstm_prediction,
                'xgboost': xgb_prediction,
                'ensemble': {
                    'prediction': ensemble_pred,
                    'confidence': ensemble_confidence
                }
            },
            'agreement_level': agreement,
            'timestamp': data.index[-1].isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Prediction error for {ticker}: {str(e)}")
        return jsonify({'error': 'Prediction failed'}), 500

@api_bp.route('/crypto/predict/<symbol>')
@cache.cached(timeout=300)
def crypto_predict(symbol):
    """Cryptocurrency prediction endpoint"""
    try:
        result = crypto_service.predict_crypto(symbol)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Crypto prediction error for {symbol}: {str(e)}")
        return jsonify({'error': 'Crypto prediction failed'}), 500

@api_bp.route('/crypto/list')
@cache.cached(timeout=3600)
def crypto_list():
    """Get list of supported cryptocurrencies"""
    try:
        cryptos = crypto_service.get_supported_cryptos()
        return jsonify(cryptos)
    except Exception as e:
        logging.error(f"Error fetching crypto list: {str(e)}")
        return jsonify({'error': 'Failed to fetch crypto list'}), 500

@api_bp.route('/oracle/<ticker>')
def oracle_insights(ticker):
    """Oracle mode mystical insights"""
    try:
        insights = oracle_service.get_mystical_insights(ticker)
        return jsonify(insights)
    except Exception as e:
        logging.error(f"Oracle error for {ticker}: {str(e)}")
        return jsonify({'error': 'Oracle insights failed'}), 500

@api_bp.route('/strategies/<ticker>')
def trading_strategies(ticker):
    """Trading strategy signals"""
    try:
        data = data_fetcher.get_stock_data(ticker)
        if data is None:
            return jsonify({'error': 'Failed to fetch data'}), 400
        
        strategies = ml_manager.get_trading_signals(data)
        return jsonify(strategies)
    except Exception as e:
        logging.error(f"Strategy error for {ticker}: {str(e)}")
        return jsonify({'error': 'Strategy analysis failed'}), 500

@api_bp.route('/chart_data/<ticker>')
@cache.cached(timeout=300)
def chart_data(ticker):
    """Chart visualization data"""
    try:
        data = data_fetcher.get_stock_data(ticker, period='3mo')
        if data is None:
            return jsonify({'error': 'Failed to fetch data'}), 400
        
        chart_data = {
            'labels': [d.strftime('%Y-%m-%d') for d in data.index],
            'prices': data['Close'].tolist(),
            'volumes': data['Volume'].tolist(),
            'predictions': []  # Will be populated by frontend
        }
        
        return jsonify(chart_data)
    except Exception as e:
        logging.error(f"Chart data error for {ticker}: {str(e)}")
        return jsonify({'error': 'Chart data failed'}), 500

@api_bp.route('/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    """Portfolio analysis endpoint"""
    try:
        data = request.json
        tickers = data.get('tickers', [])
        weights = data.get('weights', [])
        
        analysis = portfolio_analyzer.analyze_portfolio(tickers, weights)
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Portfolio analysis error: {str(e)}")
        return jsonify({'error': 'Portfolio analysis failed'}), 500

@api_bp.route('/backtest', methods=['POST'])
def run_backtest():
    """Run backtesting strategy"""
    try:
        data = request.json
        strategy = data.get('strategy')
        ticker = data.get('ticker')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = data.get('initial_capital', 10000)
        
        results = backtesting_engine.run_backtest(
            strategy=strategy,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        return jsonify(results)
    except Exception as e:
        logging.error(f"Backtesting error: {str(e)}")
        return jsonify({'error': 'Backtesting failed'}), 500

# Strategic Evolution Endpoints
@api_bp.route('/oracle_dream')
def oracle_dream():
    """Neuro-Symbolic Market Synthesis"""
    try:
        dream = oracle_dreams.generate_market_dream()
        return jsonify(dream)
    except Exception as e:
        logging.error(f"Oracle dream error: {str(e)}")
        return jsonify({'error': 'Oracle dream failed'}), 500

@api_bp.route('/curiosity/<ticker>')
def curiosity_analysis(ticker):
    """Anomaly Detection Engine"""
    try:
        analysis = curiosity_engine.analyze_anomalies(ticker)
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Curiosity analysis error for {ticker}: {str(e)}")
        return jsonify({'error': 'Curiosity analysis failed'}), 500

@api_bp.route('/health_status')
def health_status():
    """System Health Monitor"""
    try:
        status = health_monitor.get_health_status()
        return jsonify(status)
    except Exception as e:
        logging.error(f"Health status error: {str(e)}")
        return jsonify({'error': 'Health check failed'}), 500

@api_bp.route('/explain/<ticker>')
def explain_prediction(ticker):
    """AI Explainability Service"""
    try:
        explanation = explainability.explain_prediction(ticker)
        return jsonify(explanation)
    except Exception as e:
        logging.error(f"Explanation error for {ticker}: {str(e)}")
        return jsonify({'error': 'Explanation failed'}), 500

@api_bp.route('/quantum_forecast/<ticker>')
def quantum_forecast_endpoint(ticker):
    """Quantum Timeline Simulation"""
    try:
        forecast = quantum_forecast.generate_quantum_paths(ticker)
        return jsonify(forecast)
    except Exception as e:
        logging.error(f"Quantum forecast error for {ticker}: {str(e)}")
        return jsonify({'error': 'Quantum forecast failed'}), 500

@api_bp.route('/alerts', methods=['GET', 'POST', 'DELETE'])
def manage_alerts():
    """Price alerts management"""
    try:
        if request.method == 'POST':
            # Create new alert
            data = request.json
            result = notification_service.create_alert(
                ticker=data['ticker'],
                alert_type=data['alert_type'],
                target_value=data['target_value'],
                user_id=data.get('user_id', 'anonymous')
            )
            return jsonify(result)
        
        elif request.method == 'GET':
            # Get all alerts for user
            user_id = request.args.get('user_id', 'anonymous')
            alerts = notification_service.get_user_alerts(user_id)
            return jsonify(alerts)
        
        elif request.method == 'DELETE':
            # Delete alert
            alert_id = request.args.get('alert_id')
            result = notification_service.delete_alert(alert_id)
            return jsonify(result)
            
    except Exception as e:
        logging.error(f"Alert management error: {str(e)}")
        return jsonify({'error': 'Alert operation failed'}), 500

# WebSocket events
@socketio.on('join_watchlist')
def handle_join_watchlist(data):
    """Join watchlist for real-time updates"""
    ticker = data['ticker']
    emit('joined_watchlist', {'ticker': ticker, 'status': 'subscribed'})

@socketio.on('leave_watchlist')
def handle_leave_watchlist(data):
    """Leave watchlist"""
    ticker = data['ticker']
    emit('left_watchlist', {'ticker': ticker, 'status': 'unsubscribed'})
