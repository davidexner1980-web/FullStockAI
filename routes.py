from flask import render_template, request, jsonify, session, redirect, url_for
from flask_socketio import emit
from app import app, db, cache, socketio
from models import User, Portfolio, PortfolioHolding, Watchlist, PriceAlert, Prediction, BacktestResult
from ml_models import MLModelManager
from backend.data_fetcher import DataFetcher
from sentiment_analyzer import SentimentAnalyzer
from trading_strategies import TradingStrategies
from oracle_engine import OracleEngine
from backend.crypto_predictor import CryptoPredictorEngine
from portfolio_manager import PortfolioManager
from backtesting_engine import BacktestingEngine
from notification_service import NotificationService
from strategic.oracle_dreams import OracleDreams
from strategic.curiosity_engine import CuriosityEngine
from strategic.health_monitor import HealthMonitor
from strategic.explainer_service import ExplainerService
from strategic.quantum_forecast import QuantumForecast
from strategic.portfolio_optimizer import PortfolioOptimizer
import json
import logging

# Initialize services
ml_manager = MLModelManager()
data_fetcher = DataFetcher()
sentiment_analyzer = SentimentAnalyzer()
trading_strategies = TradingStrategies()
oracle_engine = OracleEngine()
crypto_predictor = CryptoPredictorEngine()
portfolio_manager = PortfolioManager()
backtesting_engine = BacktestingEngine()
notification_service = NotificationService()

# Strategic services
oracle_dreams = OracleDreams()
curiosity_engine = CuriosityEngine()
health_monitor = HealthMonitor()
explainer_service = ExplainerService()
quantum_forecast = QuantumForecast()
portfolio_optimizer = PortfolioOptimizer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crypto.html')
def crypto():
    return render_template('crypto.html')

@app.route('/oracle.html')
def oracle():
    return render_template('oracle.html')

@app.route('/portfolio.html')
def portfolio():
    return render_template('portfolio.html')

@app.route('/api/predict/<ticker>')
@cache.cached(timeout=300)
def predict(ticker):
    try:
        # Determine asset type
        asset_type = 'crypto' if ticker.upper() in ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'SOL-USD'] else 'stock'
        
        if asset_type == 'crypto':
            prediction = crypto_predictor.predict(ticker)
        else:
            prediction = ml_manager.predict_random_forest(ticker)
        
        # Store prediction in database
        pred_record = Prediction(
            symbol=ticker,
            asset_type=asset_type,
            model_type='rf',
            predicted_price=prediction['predicted_price'],
            confidence_score=prediction['confidence'],
            target_date=prediction.get('target_date')
        )
        db.session.add(pred_record)
        db.session.commit()
        
        return jsonify(prediction)
    except Exception as e:
        logging.error(f"Prediction error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/<ticker>')
def compare_models(ticker):
    try:
        asset_type = 'crypto' if ticker.upper() in ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'SOL-USD'] else 'stock'
        
        if asset_type == 'crypto':
            rf_pred = crypto_predictor.predict(ticker)
            lstm_pred = crypto_predictor.predict_lstm(ticker)
            xgb_pred = crypto_predictor.predict_xgboost(ticker)
        else:
            rf_pred = ml_manager.predict_random_forest(ticker)
            lstm_pred = ml_manager.predict_lstm(ticker)
            xgb_pred = ml_manager.predict_xgboost(ticker)
        
        # Calculate ensemble prediction
        ensemble_price = (rf_pred['predicted_price'] + lstm_pred['predicted_price'] + xgb_pred['predicted_price']) / 3
        ensemble_confidence = (rf_pred['confidence'] + lstm_pred['confidence'] + xgb_pred['confidence']) / 3
        
        return jsonify({
            'random_forest': rf_pred,
            'lstm': lstm_pred,
            'xgboost': xgb_pred,
            'ensemble': {
                'predicted_price': ensemble_price,
                'confidence': ensemble_confidence
            },
            'agreement_level': ml_manager.calculate_agreement([rf_pred, lstm_pred, xgb_pred])
        })
    except Exception as e:
        logging.error(f"Model comparison error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/oracle/<ticker>')
def oracle_insight(ticker):
    try:
        insight = oracle_engine.generate_insight(ticker)
        return jsonify(insight)
    except Exception as e:
        logging.error(f"Oracle insight error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/<ticker>')
def options_analysis(ticker):
    try:
        options_data = data_fetcher.get_options_data(ticker)
        analysis = trading_strategies.analyze_options(options_data)
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Options analysis error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart_data/<ticker>')
def chart_data(ticker):
    try:
        data = data_fetcher.get_chart_data(ticker)
        return jsonify(data)
    except Exception as e:
        logging.error(f"Chart data error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<ticker>')
def trading_signals(ticker):
    try:
        signals = trading_strategies.get_all_signals(ticker)
        return jsonify(signals)
    except Exception as e:
        logging.error(f"Trading signals error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment/<ticker>')
def sentiment_analysis(ticker):
    try:
        sentiment = sentiment_analyzer.analyze_ticker(ticker)
        return jsonify(sentiment)
    except Exception as e:
        logging.error(f"Sentiment analysis error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Strategic Evolution Endpoints
@app.route('/api/oracle_dream')
def oracle_dream():
    try:
        dream = oracle_dreams.generate_market_dream()
        return jsonify(dream)
    except Exception as e:
        logging.error(f"Oracle dream error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/curiosity/<ticker>')
def curiosity_analysis(ticker):
    try:
        analysis = curiosity_engine.analyze_anomalies(ticker)
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Curiosity analysis error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health_status')
def health_status():
    try:
        status = health_monitor.get_system_health()
        return jsonify(status)
    except Exception as e:
        logging.error(f"Health status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/explain/<ticker>')
def explain_prediction(ticker):
    try:
        explanation = explainer_service.explain_prediction(ticker)
        return jsonify(explanation)
    except Exception as e:
        logging.error(f"Explanation error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Enhanced Portfolio Endpoints
@app.route('/api/portfolio_forecast', methods=['POST'])
def portfolio_forecast():
    try:
        tickers = request.json.get('tickers', [])
        analysis = portfolio_optimizer.analyze_portfolio(tickers)
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Portfolio forecast error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quantum_forecast/<ticker>')
def quantum_timeline(ticker):
    try:
        forecast = quantum_forecast.generate_quantum_paths(ticker)
        return jsonify(forecast)
    except Exception as e:
        logging.error(f"Quantum forecast error for {ticker}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_profile', methods=['GET', 'POST'])
def user_profile():
    try:
        if request.method == 'POST':
            profile_data = request.json
            # Save user profile
            with open('data/user_profiles.json', 'w') as f:
                json.dump(profile_data, f)
            return jsonify({'status': 'saved'})
        else:
            # Load user profile
            try:
                with open('data/user_profiles.json', 'r') as f:
                    profile = json.load(f)
                return jsonify(profile)
            except FileNotFoundError:
                return jsonify({'risk_profile': 'moderate', 'notifications': True})
    except Exception as e:
        logging.error(f"User profile error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    try:
        data = request.json
        strategy_name = data.get('strategy')
        ticker = data.get('ticker')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = data.get('initial_capital', 10000)
        
        result = backtesting_engine.run_backtest(
            strategy_name, ticker, start_date, end_date, initial_capital
        )
        
        # Store backtest result
        backtest_record = BacktestResult(
            strategy_name=strategy_name,
            symbol=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=result['final_value'],
            total_return=result['total_return'],
            sharpe_ratio=result.get('sharpe_ratio'),
            max_drawdown=result.get('max_drawdown'),
            win_rate=result.get('win_rate'),
            total_trades=result.get('total_trades'),
            trade_details=json.dumps(result.get('trades', []))
        )
        db.session.add(backtest_record)
        db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Backtest error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    try:
        data = request.json
        # For demo purposes, store in session
        # In production, this would be tied to user authentication
        portfolio = session.get('portfolio', [])
        portfolio.append(data)
        session['portfolio'] = portfolio
        return jsonify({'status': 'added', 'portfolio': portfolio})
    except Exception as e:
        logging.error(f"Portfolio add error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio')
def get_portfolio():
    try:
        portfolio = session.get('portfolio', [])
        total_value = sum(item.get('current_value', 0) for item in portfolio)
        total_cost = sum(item.get('cost_basis', 0) for item in portfolio)
        pnl = total_value - total_cost
        pnl_percent = (pnl / total_cost * 100) if total_cost > 0 else 0
        
        return jsonify({
            'holdings': portfolio,
            'summary': {
                'total_value': total_value,
                'total_cost': total_cost,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            }
        })
    except Exception as e:
        logging.error(f"Portfolio get error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET', 'POST', 'DELETE'])
def price_alerts():
    try:
        if request.method == 'POST':
            data = request.json
            alerts = session.get('alerts', [])
            alerts.append(data)
            session['alerts'] = alerts
            return jsonify({'status': 'created', 'alert_id': len(alerts) - 1})
        elif request.method == 'DELETE':
            alert_id = request.args.get('id', type=int)
            alerts = session.get('alerts', [])
            if 0 <= alert_id < len(alerts):
                alerts.pop(alert_id)
                session['alerts'] = alerts
            return jsonify({'status': 'deleted'})
        else:
            alerts = session.get('alerts', [])
            return jsonify({'alerts': alerts})
    except Exception as e:
        logging.error(f"Price alerts error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto/trending')
def trending_crypto():
    try:
        trending = crypto_predictor.get_trending_crypto()
        return jsonify(trending)
    except Exception as e:
        logging.error(f"Trending crypto error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto/fear_greed')
def crypto_fear_greed():
    try:
        index = crypto_predictor.get_fear_greed_index()
        return jsonify(index)
    except Exception as e:
        logging.error(f"Fear & Greed index error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
