from app import app, db, scheduler
from models import User, WatchlistItem, Alert, Prediction
from data_fetcher import DataFetcher
from ml_models import MLModelManager
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Initialize components
data_fetcher = DataFetcher()
ml_manager = MLModelManager()

def update_model_predictions():
    """Background task to update predictions for popular symbols"""
    with app.app_context():
        try:
            # Popular symbols to update
            popular_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'SPY', 'QQQ']
            
            for symbol in popular_symbols:
                try:
                    # Get latest data
                    data = data_fetcher.get_stock_data(symbol)
                    if data is None or data.empty:
                        continue
                    
                    # Make predictions
                    predictions = ml_manager.predict(symbol, data)
                    
                    if predictions.get('ensemble'):
                        # Store in database
                        pred_record = Prediction(
                            symbol=symbol,
                            model_type='ensemble',
                            prediction_value=predictions['ensemble']['prediction'],
                            confidence=predictions['ensemble']['confidence']
                        )
                        db.session.add(pred_record)
                        
                        logger.info(f"Updated prediction for {symbol}: {predictions['ensemble']['prediction']:.2f}")
                
                except Exception as e:
                    logger.error(f"Error updating prediction for {symbol}: {e}")
                    continue
            
            db.session.commit()
            logger.info("Model predictions update completed")
            
        except Exception as e:
            logger.error(f"Error in update_model_predictions: {e}")

def retrain_models():
    """Background task to retrain models with latest data"""
    with app.app_context():
        try:
            # Symbols to retrain (could be based on user activity)
            retrain_symbols = ['AAPL', 'TSLA', 'SPY', 'BTC-USD', 'ETH-USD']
            
            for symbol in retrain_symbols:
                try:
                    logger.info(f"Retraining models for {symbol}")
                    
                    # Get extended data for training
                    if symbol.endswith('-USD'):
                        data = data_fetcher.get_crypto_data(symbol, period='2y')
                    else:
                        data = data_fetcher.get_stock_data(symbol, period='2y')
                    
                    if data is None or data.empty:
                        continue
                    
                    # Retrain models
                    rf_result = ml_manager.train_random_forest(symbol, data)
                    xgb_result = ml_manager.train_xgboost(symbol, data)
                    lstm_result = ml_manager.train_lstm(symbol, data)
                    
                    logger.info(f"Retrained models for {symbol} - RF R2: {rf_result.get('r2', 'N/A'):.3f}, "
                               f"XGB R2: {xgb_result.get('r2', 'N/A'):.3f}")
                
                except Exception as e:
                    logger.error(f"Error retraining models for {symbol}: {e}")
                    continue
            
            logger.info("Model retraining completed")
            
        except Exception as e:
            logger.error(f"Error in retrain_models: {e}")

def check_price_alerts():
    """Background task to check price alerts"""
    with app.app_context():
        try:
            # Get all active alerts
            active_alerts = Alert.query.filter_by(is_active=True).all()
            
            for alert in active_alerts:
                try:
                    # Get current price
                    if alert.symbol.endswith('-USD'):
                        data = data_fetcher.get_crypto_data(alert.symbol, period='1d')
                    else:
                        data = data_fetcher.get_stock_data(alert.symbol, period='1d')
                    
                    if data is None or data.empty:
                        continue
                    
                    current_price = data['Close'].iloc[-1]
                    
                    # Check if alert should trigger
                    triggered = False
                    if alert.alert_type == 'price_above' and current_price >= alert.threshold:
                        triggered = True
                    elif alert.alert_type == 'price_below' and current_price <= alert.threshold:
                        triggered = True
                    
                    if triggered:
                        # Mark as triggered
                        alert.triggered_at = datetime.utcnow()
                        alert.is_active = False
                        
                        logger.info(f"Alert triggered for {alert.symbol}: {current_price} vs {alert.threshold}")
                        
                        # In production, you would send email/SMS notifications here
                        # send_alert_notification(alert, current_price)
                
                except Exception as e:
                    logger.error(f"Error checking alert {alert.id}: {e}")
                    continue
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error in check_price_alerts: {e}")

def cleanup_old_predictions():
    """Background task to clean up old predictions"""
    with app.app_context():
        try:
            # Delete predictions older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_predictions = Prediction.query.filter(Prediction.created_at < cutoff_date).all()
            
            for pred in old_predictions:
                db.session.delete(pred)
            
            db.session.commit()
            logger.info(f"Cleaned up {len(old_predictions)} old predictions")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_predictions: {e}")

def system_health_check():
    """Background task to check system health"""
    with app.app_context():
        try:
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'database': 'OK',
                'api_connectivity': 'OK',
                'model_status': 'OK',
                'disk_space': 'OK'
            }
            
            # Check database connectivity
            try:
                db.session.execute('SELECT 1')
            except Exception:
                health_status['database'] = 'ERROR'
            
            # Check API connectivity (test with SPY)
            try:
                test_data = data_fetcher.get_stock_data('SPY', period='1d')
                if test_data is None or test_data.empty:
                    health_status['api_connectivity'] = 'ERROR'
            except Exception:
                health_status['api_connectivity'] = 'ERROR'
            
            # Check model files
            try:
                model_dir = 'models'
                if os.path.exists(model_dir):
                    model_files = os.listdir(model_dir)
                    if len(model_files) < 5:  # Expect at least some model files
                        health_status['model_status'] = 'WARNING'
                else:
                    health_status['model_status'] = 'WARNING'
            except Exception:
                health_status['model_status'] = 'ERROR'
            
            # Check disk space
            try:
                import shutil
                total, used, free = shutil.disk_usage('.')
                free_percent = (free / total) * 100
                if free_percent < 10:
                    health_status['disk_space'] = 'ERROR'
                elif free_percent < 20:
                    health_status['disk_space'] = 'WARNING'
            except Exception:
                health_status['disk_space'] = 'WARNING'
            
            logger.info(f"System health check: {health_status}")
            
            # Store health status (could be in a separate table)
            # For now, just log it
            
        except Exception as e:
            logger.error(f"Error in system_health_check: {e}")

# Schedule background tasks
def schedule_tasks():
    """Schedule all background tasks"""
    try:
        # Update predictions every 30 minutes
        scheduler.add_job(
            id='update_predictions',
            func=update_model_predictions,
            trigger='interval',
            minutes=30,
            replace_existing=True
        )
        
        # Retrain models daily at 2 AM
        scheduler.add_job(
            id='retrain_models',
            func=retrain_models,
            trigger='cron',
            hour=2,
            minute=0,
            replace_existing=True
        )
        
        # Check alerts every 5 minutes
        scheduler.add_job(
            id='check_alerts',
            func=check_price_alerts,
            trigger='interval',
            minutes=5,
            replace_existing=True
        )
        
        # Cleanup old data daily at 3 AM
        scheduler.add_job(
            id='cleanup_data',
            func=cleanup_old_predictions,
            trigger='cron',
            hour=3,
            minute=0,
            replace_existing=True
        )
        
        # System health check every hour
        scheduler.add_job(
            id='health_check',
            func=system_health_check,
            trigger='interval',
            hours=1,
            replace_existing=True
        )
        
        logger.info("Background tasks scheduled successfully")
        
    except Exception as e:
        logger.error(f"Error scheduling tasks: {e}")

# Initialize scheduling
schedule_tasks()
