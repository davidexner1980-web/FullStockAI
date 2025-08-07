from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, app
from backend.data_fetcher import DataFetcher
from ml_models import MLModelManager
from oracle_engine import OracleEngine
from backend.crypto_predictor import CryptoPredictorEngine
import threading
import time
import logging
from datetime import datetime

# Global variables for real-time monitoring
active_watchlists = {}
price_alerts = {}
data_fetcher = DataFetcher()
ml_manager = MLModelManager()
oracle_engine = OracleEngine()
crypto_predictor = CryptoPredictorEngine()

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    try:
        logging.info(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to FullStock AI'})
    except Exception as e:
        logging.error(f"Connection error: {str(e)}")

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    try:
        logging.info(f"Client disconnected: {request.sid}")
        # Remove client from active watchlists
        if request.sid in active_watchlists:
            del active_watchlists[request.sid]
    except Exception as e:
        logging.error(f"Disconnection error: {str(e)}")

@socketio.on('join_watchlist')
def on_join_watchlist(data):
    """Add ticker to client's watchlist for real-time updates"""
    try:
        ticker = data.get('ticker', '').upper()
        predicted_price = data.get('predicted_price', 0)
        
        if not ticker:
            emit('error', {'message': 'Ticker required'})
            return
        
        # Add to client's watchlist
        if request.sid not in active_watchlists:
            active_watchlists[request.sid] = {}
        
        active_watchlists[request.sid][ticker] = {
            'predicted_price': predicted_price,
            'last_price': 0,
            'joined_at': datetime.now().isoformat()
        }
        
        # Join ticker room for targeted updates
        join_room(f"ticker_{ticker}")
        
        emit('watchlist_joined', {
            'ticker': ticker,
            'message': f'Added {ticker} to watchlist'
        })
        
        logging.info(f"Client {request.sid} joined watchlist for {ticker}")
        
    except Exception as e:
        logging.error(f"Join watchlist error: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('leave_watchlist')
def on_leave_watchlist(data):
    """Remove ticker from client's watchlist"""
    try:
        ticker = data.get('ticker', '').upper()
        
        if request.sid in active_watchlists and ticker in active_watchlists[request.sid]:
            del active_watchlists[request.sid][ticker]
            leave_room(f"ticker_{ticker}")
            
            emit('watchlist_left', {
                'ticker': ticker,
                'message': f'Removed {ticker} from watchlist'
            })
            
            logging.info(f"Client {request.sid} left watchlist for {ticker}")
        
    except Exception as e:
        logging.error(f"Leave watchlist error: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('request_prediction')
def on_request_prediction(data):
    """Handle real-time prediction request"""
    try:
        ticker = data.get('ticker', '').upper()
        asset_type = data.get('asset_type', 'stock')
        
        if not ticker:
            emit('error', {'message': 'Ticker required'})
            return
        
        # Get prediction based on asset type
        if asset_type == 'crypto':
            prediction = crypto_predictor.predict(ticker)
        else:
            prediction = ml_manager.predict_random_forest(ticker)
        
        emit('prediction_update', {
            'ticker': ticker,
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Prediction request error: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('request_oracle_insight')
def on_request_oracle_insight(data):
    """Handle Oracle insight request"""
    try:
        ticker = data.get('ticker', '').upper()
        
        if not ticker:
            emit('error', {'message': 'Ticker required'})
            return
        
        insight = oracle_engine.generate_insight(ticker)
        
        emit('oracle_insight', {
            'ticker': ticker,
            'insight': insight,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Oracle insight request error: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('set_price_alert')
def on_set_price_alert(data):
    """Set price alert for real-time monitoring"""
    try:
        ticker = data.get('ticker', '').upper()
        target_price = float(data.get('target_price', 0))
        condition = data.get('condition', 'above')  # 'above' or 'below'
        
        if not ticker or target_price <= 0:
            emit('error', {'message': 'Valid ticker and target price required'})
            return
        
        alert_id = f"{request.sid}_{ticker}_{int(time.time())}"
        
        if request.sid not in price_alerts:
            price_alerts[request.sid] = {}
        
        price_alerts[request.sid][alert_id] = {
            'ticker': ticker,
            'target_price': target_price,
            'condition': condition,
            'created_at': datetime.now().isoformat(),
            'triggered': False
        }
        
        emit('alert_set', {
            'alert_id': alert_id,
            'ticker': ticker,
            'target_price': target_price,
            'condition': condition,
            'message': f'Alert set for {ticker} {condition} ${target_price}'
        })
        
        logging.info(f"Price alert set: {ticker} {condition} ${target_price}")
        
    except Exception as e:
        logging.error(f"Set price alert error: {str(e)}")
        emit('error', {'message': str(e)})

@socketio.on('get_market_status')
def on_get_market_status():
    """Get current market status"""
    try:
        # Get major indices
        indices_data = data_fetcher.get_market_indices()
        
        # Get crypto market summary
        crypto_summary = crypto_predictor.get_crypto_market_summary()
        
        emit('market_status', {
            'indices': indices_data,
            'crypto': crypto_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Market status error: {str(e)}")
        emit('error', {'message': str(e)})

def start_price_monitoring():
    """Background task to monitor prices and trigger alerts"""
    with app.app_context():
        while True:
            try:
                if not active_watchlists and not price_alerts:
                    time.sleep(10)
                    continue
                
                # Get unique tickers from all watchlists and alerts
                all_tickers = set()
                
                for client_watchlist in active_watchlists.values():
                    all_tickers.update(client_watchlist.keys())
                
                for client_alerts in price_alerts.values():
                    for alert in client_alerts.values():
                        if not alert['triggered']:
                            all_tickers.add(alert['ticker'])
                
                # Monitor each ticker
                for ticker in all_tickers:
                    try:
                        # Get current price
                        df = data_fetcher.get_stock_data(ticker, period='1d')
                        if df.empty:
                            continue
                        
                        current_price = df['Close'].iloc[-1]
                        
                        # Check watchlist updates
                        for client_id, watchlist in active_watchlists.items():
                            if ticker in watchlist:
                                last_price = watchlist[ticker]['last_price']
                                predicted_price = watchlist[ticker]['predicted_price']
                                
                                # Calculate deviation from prediction
                                if predicted_price > 0:
                                    deviation = abs((current_price - predicted_price) / predicted_price) * 100
                                    if deviation > 1.5:  # 1.5% deviation threshold
                                        socketio.emit('price_deviation', {
                                            'ticker': ticker,
                                            'current_price': current_price,
                                            'predicted_price': predicted_price,
                                            'deviation_percent': round(deviation, 2),
                                            'timestamp': datetime.now().isoformat()
                                        }, room=client_id)
                                
                                # Update last price and send regular update
                                if abs(current_price - last_price) / last_price > 0.005:  # 0.5% change
                                    watchlist[ticker]['last_price'] = current_price
                                    socketio.emit('price_update', {
                                        'ticker': ticker,
                                        'price': current_price,
                                        'timestamp': datetime.now().isoformat()
                                    }, room=f"ticker_{ticker}")
                        
                        # Check price alerts
                        for client_id, client_alerts in price_alerts.items():
                            for alert_id, alert in client_alerts.items():
                                if alert['triggered'] or alert['ticker'] != ticker:
                                    continue
                                
                                target_price = alert['target_price']
                                condition = alert['condition']
                                
                                triggered = False
                                if condition == 'above' and current_price >= target_price:
                                    triggered = True
                                elif condition == 'below' and current_price <= target_price:
                                    triggered = True
                                
                                if triggered:
                                    alert['triggered'] = True
                                    socketio.emit('alert_triggered', {
                                        'alert_id': alert_id,
                                        'ticker': ticker,
                                        'current_price': current_price,
                                        'target_price': target_price,
                                        'condition': condition,
                                        'timestamp': datetime.now().isoformat()
                                    }, room=client_id)
                                    
                                    logging.info(f"Alert triggered: {ticker} {condition} ${target_price}, current: ${current_price}")
                    
                    except Exception as e:
                        logging.error(f"Error monitoring {ticker}: {str(e)}")
                        continue
                
                # Wait before next monitoring cycle
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logging.error(f"Price monitoring error: {str(e)}")
                time.sleep(60)  # Wait longer on error

def broadcast_market_updates():
    """Background task to broadcast periodic market updates"""
    with app.app_context():
        while True:
            try:
                # Get market indices
                indices_data = data_fetcher.get_market_indices()
                
                if indices_data:
                    socketio.emit('market_update', {
                        'indices': indices_data,
                        'timestamp': datetime.now().isoformat()
                    }, broadcast=True)
                
                # Broadcast every 5 minutes
                time.sleep(300)
                
            except Exception as e:
                logging.error(f"Market update broadcast error: {str(e)}")
                time.sleep(600)  # Wait longer on error

def start_background_tasks():
    """Start all background tasks"""
    # Start price monitoring thread
    monitoring_thread = threading.Thread(target=start_price_monitoring, daemon=True)
    monitoring_thread.start()
    
    # Start market updates thread
    market_thread = threading.Thread(target=broadcast_market_updates, daemon=True)
    market_thread.start()
    
    logging.info("WebSocket background tasks started")

# Start background tasks when module is imported
start_background_tasks()

