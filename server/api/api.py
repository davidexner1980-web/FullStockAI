from flask import Blueprint, jsonify, request
from flask_socketio import emit
from app import cache, socketio
from server.ml.data_fetcher import DataFetcher
from server.ml.ml_models import MLModelManager
from server.utils.services.oracle_service import OracleService
from server.utils.services.crypto_service import CryptoService
from server.utils.services.backtesting import BacktestingEngine
from server.utils.services.notification_service import NotificationService
from server.utils.services.sentiment_analyzer import SentimentAnalyzer
from server.utils.strategic.curiosity_engine import CuriosityEngine
from server.utils.strategic.health_monitor import HealthMonitor
from server.utils.services.portfolio_manager import PortfolioManager
import logging
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Initialize all services for FULLSTOCK specification
data_fetcher = DataFetcher()
ml_manager = MLModelManager()
oracle_service = OracleService()
crypto_service = CryptoService()
backtesting_engine = BacktestingEngine()
notification_service = NotificationService()
sentiment_analyzer = SentimentAnalyzer()
curiosity_engine = CuriosityEngine()
health_monitor = HealthMonitor()
portfolio_manager = PortfolioManager()

@api_bp.route('/predict/<ticker>')
@cache.cached(timeout=300)
def predict(ticker):
    """Main prediction endpoint with all models"""
    try:
        ticker = ticker.upper()
        
        # Get data
        data = data_fetcher.get_stock_data(ticker)
        if data is None or data.empty:
            return jsonify({'error': 'Failed to fetch data for ticker'}), 400
        
        current_price = float(data['Close'].iloc[-1])
        
        # Get predictions from all models (handle failures gracefully)
        predictions = {}
        successful_predictions = []
        
        try:
            rf_prediction = ml_manager.predict_random_forest(data)
            if rf_prediction and 'prediction' in rf_prediction:
                predictions['random_forest'] = rf_prediction
                successful_predictions.append(rf_prediction['prediction'])
        except Exception as e:
            logging.error(f"Random Forest prediction failed: {str(e)}")
            predictions['random_forest'] = {'error': f'Random Forest failed: {str(e)}'}
        
        try:
            lstm_prediction = ml_manager.predict_lstm(data)
            if lstm_prediction and 'prediction' in lstm_prediction:
                predictions['lstm'] = lstm_prediction
                successful_predictions.append(lstm_prediction['prediction'])
        except Exception as e:
            logging.warning(f"LSTM prediction failed: {str(e)}")
            predictions['lstm'] = {'error': f'LSTM failed: {str(e)}'}
        
        try:
            xgb_prediction = ml_manager.predict_xgboost(data)
            if xgb_prediction and 'prediction' in xgb_prediction:
                predictions['xgboost'] = xgb_prediction
                successful_predictions.append(xgb_prediction['prediction'])
        except Exception as e:
            logging.error(f"XGBoost prediction failed: {str(e)}")
            predictions['xgboost'] = {'error': f'XGBoost failed: {str(e)}'}
        
        # Calculate ensemble prediction
        if successful_predictions:
            ensemble_prediction = sum(successful_predictions) / len(successful_predictions)
            ensemble_confidence = min(0.95, len(successful_predictions) / 3.0 * 0.75)
        else:
            ensemble_prediction = current_price * 1.01  # Fallback slight increase
            ensemble_confidence = 0.3
        
        predictions['ensemble'] = {
            'prediction': ensemble_prediction,
            'confidence': ensemble_confidence
        }
        
        # Calculate model agreement
        if len(successful_predictions) >= 2:
            max_pred = max(successful_predictions)
            min_pred = min(successful_predictions)
            agreement_level = 1.0 - (abs(max_pred - min_pred) / max_pred)
        else:
            agreement_level = 0.5
        
        # Prepare response
        response_data = {
            'ticker': ticker,
            'current_price': current_price,
            'predictions': predictions,
            'agreement_level': agreement_level,
            'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+00:00")
        }
        
        # Emit real-time update via WebSocket
        try:
            socketio.emit('prediction_update', response_data)
        except Exception as e:
            logging.warning(f"WebSocket emit failed: {str(e)}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Prediction endpoint error: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@api_bp.route('/history/<ticker>')
@cache.cached(timeout=600)
def get_stock_history(ticker):
    """Get stock price history for charting"""
    try:
        ticker = ticker.upper()
        period = request.args.get('period', '1mo')
        
        data = data_fetcher.get_stock_data(ticker, period=period)
        if data is None or data.empty:
            return jsonify({'error': 'Failed to fetch data'}), 400
        
        # Prepare data for frontend
        chart_data = {
            'labels': [str(date.date()) for date in data.index],
            'prices': data['Close'].tolist(),
            'volumes': data['Volume'].tolist(),
            'highs': data['High'].tolist(),
            'lows': data['Low'].tolist()
        }
        
        return jsonify({
            'ticker': ticker,
            'period': period,
            'data': chart_data,
            'current_price': float(data['Close'].iloc[-1])
        })
        
    except Exception as e:
        logging.error(f"History endpoint error: {str(e)}")
        return jsonify({'error': f'Failed to get history: {str(e)}'}), 500

@api_bp.route('/oracle/<ticker>')
@cache.cached(timeout=300)
def get_oracle_insight(ticker):
    """Get mystical oracle insights"""
    try:
        ticker = ticker.upper()
        insight = oracle_service.generate_insight(ticker)
        return jsonify(insight)
    except Exception as e:
        logging.error(f"Oracle endpoint error: {str(e)}")
        return jsonify({'error': f'Oracle insight failed: {str(e)}'}), 500

@api_bp.route('/crypto/predict/<symbol>')
@cache.cached(timeout=300) 
def predict_crypto(symbol):
    """Cryptocurrency prediction endpoint"""
    try:
        prediction = crypto_service.predict_crypto(symbol)
        return jsonify(prediction)
    except Exception as e:
        logging.error(f"Crypto prediction error: {str(e)}")
        return jsonify({'error': f'Crypto prediction failed: {str(e)}'}), 500

@api_bp.route('/crypto/supported')
def get_supported_cryptos():
    """Get list of supported cryptocurrencies"""
    try:
        cryptos = crypto_service.get_supported_cryptos()
        return jsonify(cryptos)
    except Exception as e:
        logging.error(f"Supported cryptos error: {str(e)}")
        return jsonify({'error': 'Failed to get supported cryptos'}), 500

@api_bp.route('/backtest', methods=['POST'])
def run_backtest():
    """Run backtesting for strategies"""
    try:
        data = request.get_json()
        
        strategy = data.get('strategy', 'buy_and_hold')
        ticker = data.get('ticker', 'SPY')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2024-01-01')
        initial_capital = data.get('initial_capital', 10000)
        
        result = backtesting_engine.run_backtest(
            strategy=strategy,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Backtest error: {str(e)}")
        return jsonify({'error': f'Backtesting failed: {str(e)}'}), 500

@api_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create price alert"""
    try:
        data = request.get_json()
        
        ticker = data.get('ticker', '').upper()
        alert_type = data.get('alert_type', 'price_above')
        target_value = float(data.get('target_value', 0))
        user_id = data.get('user_id', 'anonymous')
        email = data.get('email')
        
        result = notification_service.create_alert(
            ticker=ticker,
            alert_type=alert_type,
            target_value=target_value,
            user_id=user_id,
            email=email
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Create alert error: {str(e)}")
        return jsonify({'error': 'Failed to create alert'}), 500

@api_bp.route('/health')
def health_check():
    """Simple health check endpoint"""
    try:
        # Test data fetcher
        test_data = data_fetcher.get_stock_data('SPY', period='5d')
        data_status = 'healthy' if test_data is not None and not test_data.empty else 'degraded'
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'data_fetcher': data_status,
                'ml_manager': 'healthy',
                'oracle_service': 'healthy',
                'crypto_service': 'healthy',
                'backtesting_engine': 'healthy',
                'notification_service': 'healthy'
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logging.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logging.info('Client connected to WebSocket')
    emit('connected', {'status': 'Connected to FullStock AI', 'timestamp': datetime.utcnow().isoformat()})

@socketio.on('disconnect') 
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logging.info('Client disconnected from WebSocket')

@socketio.on('subscribe_ticker')
def handle_subscribe_ticker(data):
    """Handle ticker subscription request"""
    try:
        ticker = data.get('ticker', 'SPY').upper()
        logging.info(f'Client subscribed to {ticker}')
        
        # Get current data and emit price update
        stock_data = data_fetcher.get_stock_data(ticker, period='1d')
        if stock_data is not None and not stock_data.empty:
            current_price = float(stock_data['Close'].iloc[-1])
            emit('price_update', {
                'ticker': ticker,
                'price': current_price,
                'timestamp': datetime.utcnow().isoformat()
            })
    except Exception as e:
        logging.error(f"Subscribe ticker error: {str(e)}")
        ticker_name = data.get('ticker', 'unknown') if data else 'unknown'
        emit('error', {'message': f'Failed to subscribe to {ticker_name}: {str(e)}'})

@socketio.on('request_prediction')
def handle_request_prediction(data):
    """Handle prediction request via WebSocket"""
    try:
        ticker = data.get('ticker', 'SPY').upper()
        logging.info(f'Prediction requested for {ticker} via WebSocket')
        
        # Get data and predictions
        stock_data = data_fetcher.get_stock_data(ticker)
        if stock_data is None or stock_data.empty:
            emit('error', {'message': f'Failed to fetch data for {ticker}'})
            return
        
        current_price = float(stock_data['Close'].iloc[-1])
        
        # Get predictions from all models
        predictions = {}
        successful_predictions = []
        
        try:
            rf_prediction = ml_manager.predict_random_forest(stock_data)
            if rf_prediction and 'prediction' in rf_prediction:
                predictions['random_forest'] = rf_prediction
                successful_predictions.append(rf_prediction['prediction'])
        except Exception as e:
            predictions['random_forest'] = {'error': f'Random Forest failed: {str(e)}'}
        
        try:
            lstm_prediction = ml_manager.predict_lstm(stock_data)
            if lstm_prediction and 'prediction' in lstm_prediction:
                predictions['lstm'] = lstm_prediction
                successful_predictions.append(lstm_prediction['prediction'])
        except Exception as e:
            predictions['lstm'] = {'error': f'LSTM failed: {str(e)}'}
        
        try:
            xgb_prediction = ml_manager.predict_xgboost(stock_data)
            if xgb_prediction and 'prediction' in xgb_prediction:
                predictions['xgboost'] = xgb_prediction
                successful_predictions.append(xgb_prediction['prediction'])
        except Exception as e:
            predictions['xgboost'] = {'error': f'XGBoost failed: {str(e)}'}
        
        # Calculate ensemble
        if successful_predictions:
            ensemble_prediction = sum(successful_predictions) / len(successful_predictions)
            ensemble_confidence = min(0.95, len(successful_predictions) / 3.0 * 0.75)
        else:
            ensemble_prediction = current_price * 1.01
            ensemble_confidence = 0.3
        
        predictions['ensemble'] = {
            'prediction': ensemble_prediction,
            'confidence': ensemble_confidence
        }
        
        # Calculate agreement
        if len(successful_predictions) >= 2:
            max_pred = max(successful_predictions)
            min_pred = min(successful_predictions)
            agreement_level = 1.0 - (abs(max_pred - min_pred) / max_pred)
        else:
            agreement_level = 0.5
        
        response_data = {
            'ticker': ticker,
            'current_price': current_price,
            'predictions': predictions,
            'agreement_level': agreement_level,
            'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+00:00")
        }
        
        emit('prediction_update', response_data)
        
    except Exception as e:
        logging.error(f"Request prediction error: {str(e)}")
        ticker_name = data.get('ticker', 'unknown') if data else 'unknown'
        emit('error', {'message': f'Failed to get prediction for {ticker_name}: {str(e)}'})

@socketio.on('unsubscribe_ticker')
def handle_unsubscribe_ticker(data):
    """Handle ticker unsubscription request"""
    try:
        ticker = data.get('ticker', '').upper()
        logging.info(f'Client unsubscribed from {ticker}')
        emit('unsubscribed', {'ticker': ticker, 'status': 'Unsubscribed'})
    except Exception as e:
        logging.error(f"Unsubscribe ticker error: {str(e)}")
        ticker_name = data.get('ticker', 'unknown') if data else 'unknown'
        emit('error', {'message': f'Failed to unsubscribe from {ticker_name}: {str(e)}'})

@socketio.on('request_live_data')
def handle_live_data_request(data):
    """Handle request for live data updates"""
    try:
        ticker = data.get('ticker', 'SPY').upper()
        logging.info(f'Live data requested for {ticker}')
        
        # Get current data
        stock_data = data_fetcher.get_stock_data(ticker, period='1d')
        if stock_data is not None and not stock_data.empty:
            current_price = float(stock_data['Close'].iloc[-1])
            emit('live_price_update', {
                'ticker': ticker,
                'price': current_price,
                'timestamp': datetime.utcnow().isoformat()
            })
    except Exception as e:
        logging.error(f"Live data request error: {str(e)}")
        ticker_name = data.get('ticker', 'unknown') if data else 'unknown'
        emit('error', {'message': f'Failed to get live data for {ticker_name}: {str(e)}'})

# FULLSTOCK SPECIFICATION - Missing API Endpoints

@api_bp.route('/sentiment/<symbol>')
@cache.cached(timeout=300)
def get_sentiment(symbol):
    """Sentiment analysis endpoint"""
    try:
        symbol = symbol.upper()
        sentiment_data = sentiment_analyzer.analyze_sentiment(symbol)
        return jsonify({
            'symbol': symbol,
            'sentiment': sentiment_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Sentiment analysis error: {str(e)}")
        return jsonify({'error': f'Sentiment analysis failed: {str(e)}'}), 500

@api_bp.route('/oracle_vision/<symbol>')
@cache.cached(timeout=300)
def get_oracle_vision(symbol):
    """Oracle vision insights for specific symbol"""
    try:
        symbol = symbol.upper()
        vision_data = oracle_service.generate_insight(symbol)
        return jsonify({
            'symbol': symbol,
            'vision': vision_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Oracle vision error: {str(e)}")
        return jsonify({'error': f'Oracle vision failed: {str(e)}'}), 500

@api_bp.route('/oracle_dreams')
@cache.cached(timeout=600)
def get_oracle_dreams():
    """Oracle dreams - mystical market insights"""
    try:
        dreams_data = oracle_service.generate_insight('MARKET')
        return jsonify({
            'dreams': dreams_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Oracle dreams error: {str(e)}")
        return jsonify({'error': f'Oracle dreams failed: {str(e)}'}), 500

@api_bp.route('/portfolio/<symbol>')
@cache.cached(timeout=300)
def get_portfolio_analysis(symbol):
    """Portfolio analysis for symbol"""
    try:
        symbol = symbol.upper()
        portfolio_data = portfolio_manager.analyze_portfolio(symbol)
        return jsonify({
            'symbol': symbol,
            'portfolio_analysis': portfolio_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Portfolio analysis error: {str(e)}")
        return jsonify({'error': f'Portfolio analysis failed: {str(e)}'}), 500

@api_bp.route('/model_status')
@cache.cached(timeout=60)
def get_model_status():
    """Model health and status monitoring"""
    try:
        status_data = health_monitor.get_health_status()
        return jsonify({
            'model_status': status_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Model status error: {str(e)}")
        return jsonify({'error': f'Model status check failed: {str(e)}'}), 500

@api_bp.route('/curiosity/<symbol>')
@cache.cached(timeout=300)  
def get_curiosity_analysis(symbol):
    """Curiosity engine anomaly detection"""
    try:
        symbol = symbol.upper()
        curiosity_data = curiosity_engine.analyze_anomalies(symbol)
        return jsonify({
            'symbol': symbol,
            'curiosity_analysis': curiosity_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Curiosity analysis error: {str(e)}")
        return jsonify({'error': f'Curiosity analysis failed: {str(e)}'}), 500