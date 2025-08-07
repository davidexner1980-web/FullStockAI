import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from backend.data_fetcher import DataFetcher
from app import db
from models import Stock, PriceHistory, Prediction

logger = logging.getLogger(__name__)

def update_market_data():
    """
    Background task to update market data
    Called every 5 minutes by scheduler
    """
    try:
        logger.info("Starting market data update")
        data_fetcher = DataFetcher()
        
        # Popular symbols to update
        symbols_to_update = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD'
        ]
        
        updated_count = 0
        
        for symbol in symbols_to_update:
            try:
                # Check if we need to update this symbol
                stock = Stock.query.filter_by(symbol=symbol).first()
                
                if stock and stock.last_updated:
                    # Skip if updated within last 5 minutes
                    time_diff = datetime.utcnow() - stock.last_updated
                    if time_diff.total_seconds() < 300:  # 5 minutes
                        continue
                
                # Get current price
                current_price = data_fetcher.get_real_time_price(symbol)
                
                if current_price:
                    # Update or create stock record
                    if not stock:
                        stock_info = data_fetcher.get_stock_info(symbol)
                        stock = Stock(
                            symbol=symbol,
                            name=stock_info.get('name', symbol),
                            sector=stock_info.get('sector', 'Unknown'),
                            market_cap=stock_info.get('market_cap', 0),
                            is_crypto=stock_info.get('is_crypto', False)
                        )
                        db.session.add(stock)
                        db.session.flush()  # Get the ID
                    
                    stock.last_updated = datetime.utcnow()
                    
                    # Add price history entry
                    today = datetime.utcnow().date()
                    existing_entry = PriceHistory.query.filter_by(
                        stock_id=stock.id,
                        date=today
                    ).first()
                    
                    if not existing_entry:
                        price_entry = PriceHistory(
                            stock_id=stock.id,
                            date=today,
                            close_price=current_price,
                            open_price=current_price,  # Simplified
                            high_price=current_price,
                            low_price=current_price,
                            volume=0  # Would need additional API call
                        )
                        db.session.add(price_entry)
                    else:
                        # Update existing entry
                        existing_entry.close_price = current_price
                        existing_entry.high_price = max(existing_entry.high_price, current_price)
                        existing_entry.low_price = min(existing_entry.low_price, current_price)
                    
                    updated_count += 1
                    
                    # Commit every 10 updates to avoid long transactions
                    if updated_count % 10 == 0:
                        db.session.commit()
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error updating {symbol}: {str(e)}")
                continue
        
        # Final commit
        db.session.commit()
        logger.info(f"Market data update completed. Updated {updated_count} symbols.")
        
    except Exception as e:
        logger.error(f"Error in market data update: {str(e)}")
        db.session.rollback()

def cleanup_old_data():
    """
    Clean up old data to prevent database bloat
    Called daily by scheduler
    """
    try:
        logger.info("Starting data cleanup")
        
        # Clean up old predictions (keep last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_predictions = Prediction.query.filter(
            Prediction.prediction_date < cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {old_predictions} old predictions")
        
        # Clean up old price history (keep last 2 years)
        price_cutoff_date = (datetime.utcnow() - timedelta(days=730)).date()
        old_prices = PriceHistory.query.filter(
            PriceHistory.date < price_cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {old_prices} old price records")
        
        db.session.commit()
        logger.info("Data cleanup completed")
        
    except Exception as e:
        logger.error(f"Error in data cleanup: {str(e)}")
        db.session.rollback()

def get_system_health():
    """
    Get system health metrics
    
    Returns:
        Dictionary with system health information
    """
    try:
        health_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'unknown',
            'disk_space': 'unknown',
            'memory': 'unknown',
            'recent_updates': 0
        }
        
        # Test database connection
        try:
            stock_count = Stock.query.count()
            health_info['database'] = 'healthy'
            health_info['total_stocks'] = stock_count
        except Exception:
            health_info['database'] = 'error'
        
        # Check recent updates
        try:
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_updates = Stock.query.filter(
                Stock.last_updated > recent_cutoff
            ).count()
            health_info['recent_updates'] = recent_updates
        except Exception:
            pass
        
        # Basic disk space check
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free // (2**30)  # Convert to GB
            health_info['disk_space'] = f"{free_gb}GB free"
            
            if free_gb < 1:  # Less than 1GB free
                health_info['disk_space_status'] = 'low'
            else:
                health_info['disk_space_status'] = 'healthy'
        except Exception:
            health_info['disk_space_status'] = 'unknown'
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}

def format_currency(amount: float, symbol: str = '$') -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Amount to format
        symbol: Currency symbol
        
    Returns:
        Formatted currency string
    """
    try:
        if abs(amount) >= 1e9:
            return f"{symbol}{amount/1e9:.1f}B"
        elif abs(amount) >= 1e6:
            return f"{symbol}{amount/1e6:.1f}M"
        elif abs(amount) >= 1e3:
            return f"{symbol}{amount/1e3:.1f}K"
        else:
            return f"{symbol}{amount:.2f}"
    except (TypeError, ValueError):
        return f"{symbol}0.00"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage for display
    
    Args:
        value: Percentage value
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string with + or - sign
    """
    try:
        if value > 0:
            return f"+{value:.{decimals}f}%"
        else:
            return f"{value:.{decimals}f}%"
    except (TypeError, ValueError):
        return "0.00%"

def calculate_portfolio_metrics(holdings: List[Dict]) -> Dict:
    """
    Calculate portfolio-level metrics
    
    Args:
        holdings: List of portfolio holdings
        
    Returns:
        Dictionary with portfolio metrics
    """
    try:
        if not holdings:
            return {
                'total_value': 0,
                'total_cost': 0,
                'total_return': 0,
                'total_return_pct': 0,
                'day_change': 0,
                'day_change_pct': 0
            }
        
        total_value = sum(holding.get('current_value', 0) for holding in holdings)
        total_cost = sum(holding.get('cost_basis', 0) for holding in holdings)
        
        total_return = total_value - total_cost
        total_return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate day change (simplified)
        day_change = sum(
            holding.get('current_value', 0) * 0.01  # Placeholder for real day change
            for holding in holdings
        )
        day_change_pct = (day_change / total_value * 100) if total_value > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'day_change': day_change,
            'day_change_pct': day_change_pct
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio metrics: {str(e)}")
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_return': 0,
            'total_return_pct': 0,
            'day_change': 0,
            'day_change_pct': 0
        }

def validate_symbol(symbol: str) -> bool:
    """
    Validate if a stock symbol is properly formatted
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if symbol is valid
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    symbol = symbol.upper().strip()
    
    # Basic validation rules
    if len(symbol) < 1 or len(symbol) > 10:
        return False
    
    # Check for valid characters (letters, numbers, hyphens, dots)
    import re
    if not re.match(r'^[A-Z0-9.-]+$', symbol):
        return False
    
    return True

def get_market_status() -> Dict:
    """
    Get current market status (simplified)
    
    Returns:
        Dictionary with market status information
    """
    try:
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Simplified market hours (US markets)
        # Monday-Friday 9:30 AM - 4:00 PM EST
        if current_day < 5:  # Monday to Friday
            if 9 <= current_hour < 16:
                status = 'open'
                message = 'Market is currently open'
            elif current_hour < 9:
                status = 'pre_market'
                message = 'Pre-market trading'
            else:
                status = 'after_hours'
                message = 'After-hours trading'
        else:  # Weekend
            status = 'closed'
            message = 'Market is closed (weekend)'
        
        return {
            'status': status,
            'message': message,
            'current_time': now.isoformat(),
            'is_trading_day': current_day < 5
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {str(e)}")
        return {
            'status': 'unknown',
            'message': 'Unable to determine market status',
            'current_time': datetime.now().isoformat()
        }

def log_user_action(action: str, symbol: str = None, details: Dict = None):
    """
    Log user action for analytics
    
    Args:
        action: Action performed (predict, backtest, etc.)
        symbol: Stock symbol involved (optional)
        details: Additional action details (optional)
    """
    try:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'symbol': symbol,
            'details': details or {}
        }
        
        # In a production system, you might want to store this in a separate analytics table
        logger.info(f"User Action: {log_entry}")
        
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")

def get_crypto_market_cap_rank(symbol: str) -> Optional[int]:
    """
    Get approximate market cap ranking for crypto (simplified)
    
    Args:
        symbol: Crypto symbol
        
    Returns:
        Approximate market cap rank or None
    """
    # Simplified ranking based on common knowledge
    crypto_ranks = {
        'BTC-USD': 1,
        'ETH-USD': 2,
        'ADA-USD': 8,
        'DOT-USD': 12,
        'LINK-USD': 15,
        'LTC-USD': 20,
        'BCH-USD': 25,
        'XLM-USD': 30,
        'UNI-USD': 35,
        'VET-USD': 40
    }
    
    return crypto_ranks.get(symbol)

def calculate_risk_score(volatility: float, beta: float = 1.0, 
                        market_cap: float = 0) -> Dict:
    """
    Calculate risk score for a stock/crypto
    
    Args:
        volatility: Historical volatility
        beta: Beta coefficient (default 1.0)
        market_cap: Market capitalization
        
    Returns:
        Dictionary with risk assessment
    """
    try:
        # Base risk score on volatility
        if volatility < 0.15:  # 15%
            risk_level = 'low'
            risk_score = 25
        elif volatility < 0.25:  # 25%
            risk_level = 'moderate'
            risk_score = 50
        elif volatility < 0.40:  # 40%
            risk_level = 'high'
            risk_score = 75
        else:
            risk_level = 'very_high'
            risk_score = 90
        
        # Adjust for beta
        if abs(beta - 1.0) > 0.5:
            risk_score += 10
        
        # Adjust for market cap (smaller = riskier)
        if market_cap > 0:
            if market_cap < 1e9:  # Less than $1B
                risk_score += 15
            elif market_cap < 10e9:  # Less than $10B
                risk_score += 5
        
        risk_score = min(100, risk_score)  # Cap at 100
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'volatility': round(volatility * 100, 2),
            'beta': beta,
            'factors': {
                'volatility_contribution': 'primary',
                'beta_contribution': 'secondary',
                'market_cap_contribution': 'tertiary'
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        return {
            'risk_score': 50,
            'risk_level': 'moderate',
            'error': str(e)
        }

def get_trading_session_info() -> Dict:
    """
    Get current trading session information
    
    Returns:
        Dictionary with session info
    """
    try:
        now = datetime.now()
        
        # US Market sessions (Eastern Time approximation)
        sessions = {
            'asian': {'start': 18, 'end': 2, 'name': 'Asian Session'},
            'european': {'start': 2, 'end': 11, 'name': 'European Session'},
            'us': {'start': 9, 'end': 17, 'name': 'US Session'},
            'after_hours': {'start': 17, 'end': 18, 'name': 'After Hours'}
        }
        
        current_hour = now.hour
        active_session = None
        
        for session_key, session_info in sessions.items():
            start_hour = session_info['start']
            end_hour = session_info['end']
            
            if start_hour > end_hour:  # Spans midnight
                if current_hour >= start_hour or current_hour < end_hour:
                    active_session = session_info
                    break
            else:
                if start_hour <= current_hour < end_hour:
                    active_session = session_info
                    break
        
        return {
            'current_session': active_session['name'] if active_session else 'Between Sessions',
            'current_time': now.strftime('%H:%M:%S'),
            'all_sessions': sessions,
            'crypto_24_7': True  # Crypto markets are always open
        }
        
    except Exception as e:
        logger.error(f"Error getting trading session info: {str(e)}")
        return {
            'current_session': 'Unknown',
            'current_time': datetime.now().strftime('%H:%M:%S'),
            'crypto_24_7': True
        }
