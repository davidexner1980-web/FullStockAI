import json
import logging
import threading
import time
from datetime import datetime
from collections import defaultdict
from flask_socketio import emit, disconnect
from app import socketio
import yfinance as yf

class WebSocketManager:
    """WebSocket connection and real-time data management"""
    
    def __init__(self):
        self.active_connections = {}  # session_id -> connection_info
        self.subscriptions = defaultdict(set)  # ticker -> set of session_ids
        self.price_cache = {}  # ticker -> last_price
        self.update_intervals = {
            'price_update': 5,  # seconds
            'portfolio_update': 30,
            'market_update': 60
        }
        
        # Background threads
        self.price_update_thread = None
        self.portfolio_update_thread = None
        self.market_update_thread = None
        self.shutdown_flag = threading.Event()
        
        # Start background processes
        self.start_background_processes()
    
    def start_background_processes(self):
        """Start background threads for real-time updates"""
        try:
            if not self.price_update_thread or not self.price_update_thread.is_alive():
                self.price_update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
                self.price_update_thread.start()
                logging.info("Price update thread started")
            
            if not self.portfolio_update_thread or not self.portfolio_update_thread.is_alive():
                self.portfolio_update_thread = threading.Thread(target=self._portfolio_update_loop, daemon=True)
                self.portfolio_update_thread.start()
                logging.info("Portfolio update thread started")
            
            if not self.market_update_thread or not self.market_update_thread.is_alive():
                self.market_update_thread = threading.Thread(target=self._market_update_loop, daemon=True)
                self.market_update_thread.start()
                logging.info("Market update thread started")
                
        except Exception as e:
            logging.error(f"Error starting background processes: {str(e)}")
    
    def register_connection(self, session_id, user_data=None):
        """Register new WebSocket connection"""
        try:
            self.active_connections[session_id] = {
                'connected_at': datetime.now().isoformat(),
                'user_data': user_data or {},
                'subscriptions': set(),
                'last_activity': datetime.now().isoformat()
            }
            
            logging.info(f"WebSocket connection registered: {session_id}")
            
            # Send welcome message
            socketio.emit('welcome', {
                'message': 'Connected to FullStock AI real-time data',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
        except Exception as e:
            logging.error(f"Error registering WebSocket connection: {str(e)}")
    
    def unregister_connection(self, session_id):
        """Unregister WebSocket connection"""
        try:
            if session_id in self.active_connections:
                # Remove all subscriptions for this connection
                connection_info = self.active_connections[session_id]
                for ticker in connection_info.get('subscriptions', set()):
                    if ticker in self.subscriptions:
                        self.subscriptions[ticker].discard(session_id)
                        if not self.subscriptions[ticker]:
                            del self.subscriptions[ticker]
                
                del self.active_connections[session_id]
                logging.info(f"WebSocket connection unregistered: {session_id}")
            
        except Exception as e:
            logging.error(f"Error unregistering WebSocket connection: {str(e)}")
    
    def subscribe_ticker(self, ticker, session_id):
        """Subscribe to real-time updates for a ticker"""
        try:
            ticker = ticker.upper()
            
            if session_id in self.active_connections:
                self.subscriptions[ticker].add(session_id)
                self.active_connections[session_id]['subscriptions'].add(ticker)
                
                logging.info(f"Session {session_id} subscribed to {ticker}")
                
                # Send current price if available
                if ticker in self.price_cache:
                    socketio.emit('price_update', {
                        'ticker': ticker,
                        'price': self.price_cache[ticker],
                        'timestamp': datetime.now().isoformat()
                    }, room=session_id)
                
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error subscribing to ticker {ticker}: {str(e)}")
            return False
    
    def unsubscribe_ticker(self, ticker, session_id):
        """Unsubscribe from ticker updates"""
        try:
            ticker = ticker.upper()
            
            if ticker in self.subscriptions:
                self.subscriptions[ticker].discard(session_id)
                if not self.subscriptions[ticker]:
                    del self.subscriptions[ticker]
            
            if session_id in self.active_connections:
                self.active_connections[session_id]['subscriptions'].discard(ticker)
            
            logging.info(f"Session {session_id} unsubscribed from {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error unsubscribing from ticker {ticker}: {str(e)}")
            return False
    
    def broadcast_price_update(self, ticker, price_data):
        """Broadcast price update to all subscribers"""
        try:
            ticker = ticker.upper()
            
            if ticker in self.subscriptions:
                update_data = {
                    'ticker': ticker,
                    'price': price_data.get('price'),
                    'change': price_data.get('change'),
                    'change_percent': price_data.get('change_percent'),
                    'volume': price_data.get('volume'),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Send to all subscribers
                for session_id in self.subscriptions[ticker].copy():
                    if session_id in self.active_connections:
                        socketio.emit('price_update', update_data, room=session_id)
                    else:
                        # Clean up dead connections
                        self.subscriptions[ticker].discard(session_id)
                
                # Update cache
                self.price_cache[ticker] = price_data.get('price')
                
        except Exception as e:
            logging.error(f"Error broadcasting price update for {ticker}: {str(e)}")
    
    def broadcast_alert(self, alert_data):
        """Broadcast alert to all connections"""
        try:
            alert_message = {
                'type': 'alert',
                'message': alert_data.get('message'),
                'severity': alert_data.get('severity', 'info'),
                'ticker': alert_data.get('ticker'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to all active connections
            for session_id in list(self.active_connections.keys()):
                if session_id in self.active_connections:
                    socketio.emit('alert', alert_message, room=session_id)
                
        except Exception as e:
            logging.error(f"Error broadcasting alert: {str(e)}")
    
    def send_portfolio_update(self, session_id, portfolio_data):
        """Send portfolio update to specific session"""
        try:
            if session_id in self.active_connections:
                update_data = {
                    'type': 'portfolio_update',
                    'data': portfolio_data,
                    'timestamp': datetime.now().isoformat()
                }
                
                socketio.emit('portfolio_update', update_data, room=session_id)
                
        except Exception as e:
            logging.error(f"Error sending portfolio update: {str(e)}")
    
    def send_oracle_insight(self, session_id, ticker, oracle_data):
        """Send Oracle insight to specific session"""
        try:
            if session_id in self.active_connections:
                insight_data = {
                    'type': 'oracle_insight',
                    'ticker': ticker,
                    'data': oracle_data,
                    'timestamp': datetime.now().isoformat()
                }
                
                socketio.emit('oracle_insight', insight_data, room=session_id)
                
        except Exception as e:
            logging.error(f"Error sending Oracle insight: {str(e)}")
    
    def _price_update_loop(self):
        """Background loop for price updates"""
        while not self.shutdown_flag.is_set():
            try:
                if self.subscriptions:
                    # Get unique tickers
                    tickers = list(self.subscriptions.keys())
                    
                    # Fetch prices in batches
                    batch_size = 10
                    for i in range(0, len(tickers), batch_size):
                        batch = tickers[i:i + batch_size]
                        self._fetch_and_broadcast_prices(batch)
                        
                        # Small delay between batches
                        if not self.shutdown_flag.wait(1):
                            break
                
                # Wait for next update cycle
                self.shutdown_flag.wait(self.update_intervals['price_update'])
                
            except Exception as e:
                logging.error(f"Error in price update loop: {str(e)}")
                self.shutdown_flag.wait(10)  # Wait before retry
    
    def _fetch_and_broadcast_prices(self, tickers):
        """Fetch and broadcast prices for a batch of tickers"""
        try:
            for ticker in tickers:
                try:
                    # Skip if no subscribers
                    if ticker not in self.subscriptions or not self.subscriptions[ticker]:
                        continue
                    
                    # Fetch price data
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    if not current_price:
                        continue
                    
                    previous_close = info.get('previousClose', current_price)
                    change = current_price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                    volume = info.get('volume', 0)
                    
                    price_data = {
                        'price': current_price,
                        'change': change,
                        'change_percent': change_percent,
                        'volume': volume
                    }
                    
                    # Check for significant price changes (alerts)
                    if self._is_significant_price_change(ticker, current_price):
                        self._send_price_alert(ticker, price_data)
                    
                    # Broadcast update
                    self.broadcast_price_update(ticker, price_data)
                    
                except Exception as e:
                    logging.error(f"Error fetching price for {ticker}: {str(e)}")
                    continue
                
        except Exception as e:
            logging.error(f"Error fetching batch prices: {str(e)}")
    
    def _is_significant_price_change(self, ticker, current_price):
        """Check if price change is significant enough for alert"""
        try:
            if ticker not in self.price_cache:
                return False
            
            last_price = self.price_cache[ticker]
            if last_price == 0:
                return False
            
            change_percent = abs((current_price - last_price) / last_price * 100)
            
            # Alert threshold: 2% price change
            return change_percent >= 2.0
            
        except Exception as e:
            logging.error(f"Error checking price change for {ticker}: {str(e)}")
            return False
    
    def _send_price_alert(self, ticker, price_data):
        """Send price alert for significant changes"""
        try:
            alert_data = {
                'message': f'{ticker} price moved significantly',
                'severity': 'warning',
                'ticker': ticker,
                'price_data': price_data
            }
            
            self.broadcast_alert(alert_data)
            
        except Exception as e:
            logging.error(f"Error sending price alert for {ticker}: {str(e)}")
    
    def _portfolio_update_loop(self):
        """Background loop for portfolio updates"""
        while not self.shutdown_flag.is_set():
            try:
                # Send portfolio updates to connected users
                for session_id, connection_info in list(self.active_connections.items()):
                    try:
                        user_data = connection_info.get('user_data', {})
                        watchlist = user_data.get('watchlist', [])
                        
                        if watchlist:
                            # Calculate basic portfolio metrics
                            portfolio_data = self._calculate_portfolio_metrics(watchlist)
                            self.send_portfolio_update(session_id, portfolio_data)
                            
                    except Exception as e:
                        logging.error(f"Error updating portfolio for session {session_id}: {str(e)}")
                        continue
                
                # Wait for next update cycle
                self.shutdown_flag.wait(self.update_intervals['portfolio_update'])
                
            except Exception as e:
                logging.error(f"Error in portfolio update loop: {str(e)}")
                self.shutdown_flag.wait(30)  # Wait before retry
    
    def _calculate_portfolio_metrics(self, watchlist):
        """Calculate basic portfolio metrics for watchlist"""
        try:
            portfolio_data = {
                'total_positions': len(watchlist),
                'active_alerts': 0,
                'top_performer': None,
                'worst_performer': None,
                'last_update': datetime.now().isoformat()
            }
            
            if watchlist and len(watchlist) > 0:
                # Get performance data for watchlist items
                performances = []
                
                for ticker in watchlist:
                    if ticker in self.price_cache:
                        # This is simplified - in real implementation, 
                        # you'd calculate actual performance
                        performances.append({
                            'ticker': ticker,
                            'performance': 0  # Placeholder
                        })
                
                if performances:
                    portfolio_data['top_performer'] = performances[0]['ticker']
                    portfolio_data['worst_performer'] = performances[-1]['ticker']
            
            return portfolio_data
            
        except Exception as e:
            logging.error(f"Error calculating portfolio metrics: {str(e)}")
            return {}
    
    def _market_update_loop(self):
        """Background loop for market-wide updates"""
        while not self.shutdown_flag.is_set():
            try:
                # Send market updates
                market_data = self._get_market_summary()
                
                if market_data:
                    # Broadcast to all connections
                    for session_id in list(self.active_connections.keys()):
                        if session_id in self.active_connections:
                            socketio.emit('market_update', {
                                'type': 'market_summary',
                                'data': market_data,
                                'timestamp': datetime.now().isoformat()
                            }, room=session_id)
                
                # Wait for next update cycle
                self.shutdown_flag.wait(self.update_intervals['market_update'])
                
            except Exception as e:
                logging.error(f"Error in market update loop: {str(e)}")
                self.shutdown_flag.wait(60)  # Wait before retry
    
    def _get_market_summary(self):
        """Get basic market summary"""
        try:
            # Fetch major indices
            indices = ['SPY', 'QQQ', 'DIA']
            market_data = {}
            
            for index in indices:
                try:
                    stock = yf.Ticker(index)
                    info = stock.info
                    
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    previous_close = info.get('previousClose', current_price)
                    
                    if current_price and previous_close:
                        change_percent = ((current_price - previous_close) / previous_close * 100)
                        
                        market_data[index] = {
                            'price': current_price,
                            'change_percent': change_percent
                        }
                        
                except Exception as e:
                    logging.error(f"Error fetching market data for {index}: {str(e)}")
                    continue
            
            return market_data if market_data else None
            
        except Exception as e:
            logging.error(f"Error getting market summary: {str(e)}")
            return None
    
    def get_connection_stats(self):
        """Get WebSocket connection statistics"""
        try:
            total_connections = len(self.active_connections)
            total_subscriptions = sum(len(subs) for subs in self.subscriptions.values())
            unique_tickers = len(self.subscriptions)
            
            # Connection activity
            recent_connections = 0
            current_time = datetime.now()
            
            for connection_info in self.active_connections.values():
                connected_at = datetime.fromisoformat(connection_info['connected_at'])
                if (current_time - connected_at).seconds < 300:  # Last 5 minutes
                    recent_connections += 1
            
            return {
                'total_connections': total_connections,
                'recent_connections': recent_connections,
                'total_subscriptions': total_subscriptions,
                'unique_tickers_subscribed': unique_tickers,
                'cached_prices': len(self.price_cache),
                'background_threads_active': {
                    'price_updates': self.price_update_thread.is_alive() if self.price_update_thread else False,
                    'portfolio_updates': self.portfolio_update_thread.is_alive() if self.portfolio_update_thread else False,
                    'market_updates': self.market_update_thread.is_alive() if self.market_update_thread else False
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting connection stats: {str(e)}")
            return {}
    
    def handle_disconnect(self, session_id):
        """Handle WebSocket disconnection"""
        self.unregister_connection(session_id)
    
    def shutdown(self):
        """Shutdown WebSocket manager"""
        try:
            logging.info("Shutting down WebSocket manager...")
            self.shutdown_flag.set()
            
            # Wait for threads to complete
            threads = [self.price_update_thread, self.portfolio_update_thread, self.market_update_thread]
            for thread in threads:
                if thread and thread.is_alive():
                    thread.join(timeout=5)
            
            # Clear connections
            self.active_connections.clear()
            self.subscriptions.clear()
            self.price_cache.clear()
            
            logging.info("WebSocket manager shutdown complete")
            
        except Exception as e:
            logging.error(f"Error during WebSocket manager shutdown: {str(e)}")
