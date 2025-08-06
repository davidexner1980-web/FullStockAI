from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, db
from models import WatchlistItem, Alert
from data_fetcher import DataFetcher
import logging
import threading
import time
from datetime import datetime

# Initialize components
data_fetcher = DataFetcher()
logger = logging.getLogger(__name__)

# Global variables for real-time monitoring
active_connections = {}
monitoring_thread = None
monitoring_active = False

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    active_connections[request.sid] = {
        'user_id': auth.get('user_id', 1) if auth else 1,
        'watchlist': [],
        'connected_at': datetime.utcnow()
    }
    
    # Start monitoring thread if not already running
    global monitoring_thread, monitoring_active
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitor_prices)
        monitoring_thread.daemon = True
        monitoring_thread.start()
    
    emit('connection_status', {'status': 'connected', 'timestamp': datetime.utcnow().isoformat()})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")
    if request.sid in active_connections:
        del active_connections[request.sid]
    
    # Stop monitoring if no active connections
    global monitoring_active
    if not active_connections:
        monitoring_active = False

@socketio.on('join_watchlist')
def handle_join_watchlist(data):
    """Join a watchlist room for real-time updates"""
    try:
        symbol = data.get('symbol', '').upper()
        user_id = active_connections.get(request.sid, {}).get('user_id', 1)
        
        # Add to user's active watchlist
        if request.sid in active_connections:
            if symbol not in active_connections[request.sid]['watchlist']:
                active_connections[request.sid]['watchlist'].append(symbol)
        
        # Join the symbol's room
        join_room(f"symbol_{symbol}")
        
        logger.info(f"Client {request.sid} joined watchlist for {symbol}")
        emit('watchlist_joined', {'symbol': symbol, 'status': 'success'})
        
        # Send initial price data
        send_price_update(symbol)
        
    except Exception as e:
        logger.error(f"Error joining watchlist: {e}")
        emit('error', {'message': str(e)})

@socketio.on('leave_watchlist')
def handle_leave_watchlist(data):
    """Leave a watchlist room"""
    try:
        symbol = data.get('symbol', '').upper()
        
        # Remove from user's active watchlist
        if request.sid in active_connections:
            if symbol in active_connections[request.sid]['watchlist']:
                active_connections[request.sid]['watchlist'].remove(symbol)
        
        # Leave the symbol's room
        leave_room(f"symbol_{symbol}")
        
        logger.info(f"Client {request.sid} left watchlist for {symbol}")
        emit('watchlist_left', {'symbol': symbol, 'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error leaving watchlist: {e}")
        emit('error', {'message': str(e)})

@socketio.on('request_prediction')
def handle_prediction_request(data):
    """Handle real-time prediction request"""
    try:
        symbol = data.get('symbol', '').upper()
        
        # Import here to avoid circular imports
        from ml_models import MLModelManager
        from crypto_predictor import CryptocurrencyPredictor
        
        ml_manager = MLModelManager()
        crypto_predictor = CryptocurrencyPredictor()
        
        # Determine asset type and get prediction
        if symbol.endswith('-USD') or symbol in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']:
            result = crypto_predictor.predict_crypto(symbol)
        else:
            stock_data = data_fetcher.get_stock_data(symbol)
            if stock_data is not None and not stock_data.empty:
                predictions = ml_manager.predict(symbol, stock_data)
                result = {
                    'symbol': symbol,
                    'predictions': predictions,
                    'current_price': stock_data['Close'].iloc[-1]
                }
            else:
                result = {'error': f'No data available for {symbol}'}
        
        emit('prediction_result', result)
        
    except Exception as e:
        logger.error(f"Error handling prediction request: {e}")
        emit('error', {'message': str(e)})

@socketio.on('set_alert')
def handle_set_alert(data):
    """Set a price alert"""
    try:
        symbol = data.get('symbol', '').upper()
        alert_type = data.get('type')  # 'above' or 'below'
        threshold = float(data.get('threshold'))
        user_id = active_connections.get(request.sid, {}).get('user_id', 1)
        
        # Create alert in database
        alert = Alert(
            user_id=user_id,
            symbol=symbol,
            alert_type=f"price_{alert_type}",
            threshold=threshold
        )
        
        db.session.add(alert)
        db.session.commit()
        
        emit('alert_set', {
            'symbol': symbol,
            'type': alert_type,
            'threshold': threshold,
            'id': alert.id
        })
        
    except Exception as e:
        logger.error(f"Error setting alert: {e}")
        emit('error', {'message': str(e)})

def send_price_update(symbol):
    """Send price update for a symbol"""
    try:
        # Get current price data
        if symbol.endswith('-USD') or symbol in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']:
            data = data_fetcher.get_crypto_data(symbol, period='1d')
            asset_type = 'crypto'
        else:
            data = data_fetcher.get_stock_data(symbol, period='1d')
            asset_type = 'stock'
        
        if data is not None and not data.empty:
            current_price = data['Close'].iloc[-1]
            previous_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0
            
            price_update = {
                'symbol': symbol,
                'price': current_price,
                'change_percent': change_percent,
                'timestamp': datetime.utcnow().isoformat(),
                'asset_type': asset_type
            }
            
            # Emit to all clients watching this symbol
            socketio.emit('price_update', price_update, room=f"symbol_{symbol}")
            
            # Check for triggered alerts
            check_alerts(symbol, current_price)
            
    except Exception as e:
        logger.error(f"Error sending price update for {symbol}: {e}")

def check_alerts(symbol, current_price):
    """Check if any alerts should be triggered"""
    try:
        # Get active alerts for this symbol
        alerts = Alert.query.filter_by(symbol=symbol, is_active=True).all()
        
        for alert in alerts:
            triggered = False
            
            if alert.alert_type == 'price_above' and current_price >= alert.threshold:
                triggered = True
            elif alert.alert_type == 'price_below' and current_price <= alert.threshold:
                triggered = True
            
            if triggered:
                # Mark alert as triggered
                alert.triggered_at = datetime.utcnow()
                alert.is_active = False
                
                # Send alert notification
                alert_data = {
                    'id': alert.id,
                    'symbol': symbol,
                    'type': alert.alert_type,
                    'threshold': alert.threshold,
                    'current_price': current_price,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Emit to specific user (in production, you'd need user session mapping)
                socketio.emit('alert_triggered', alert_data)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error checking alerts for {symbol}: {e}")

def monitor_prices():
    """Background thread to monitor prices for active watchlists"""
    global monitoring_active
    
    while monitoring_active:
        try:
            if not active_connections:
                time.sleep(5)
                continue
            
            # Get all unique symbols being watched
            watched_symbols = set()
            for connection_data in active_connections.values():
                watched_symbols.update(connection_data['watchlist'])
            
            # Update prices for watched symbols
            for symbol in watched_symbols:
                send_price_update(symbol)
                time.sleep(1)  # Rate limiting
            
            # Wait before next update cycle
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in price monitoring thread: {e}")
            time.sleep(5)

@socketio.on('get_market_pulse')
def handle_market_pulse():
    """Send current market pulse data"""
    try:
        # Get major indices
        indices = ['SPY', 'QQQ', 'DIA']
        market_pulse = {}
        
        for index in indices:
            data = data_fetcher.get_stock_data(index, period='1d')
            if data is not None and not data.empty:
                current_price = data['Close'].iloc[-1]
                change = ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100 if len(data) > 1 else 0
                market_pulse[index] = {
                    'price': current_price,
                    'change': change
                }
        
        # Get crypto pulse
        crypto_symbols = ['BTC-USD', 'ETH-USD']
        crypto_pulse = {}
        
        for symbol in crypto_symbols:
            data = data_fetcher.get_crypto_data(symbol, period='1d')
            if data is not None and not data.empty:
                current_price = data['Close'].iloc[-1]
                change = ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100 if len(data) > 1 else 0
                crypto_pulse[symbol] = {
                    'price': current_price,
                    'change': change
                }
        
        emit('market_pulse', {
            'indices': market_pulse,
            'crypto': crypto_pulse,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting market pulse: {e}")
        emit('error', {'message': str(e)})
