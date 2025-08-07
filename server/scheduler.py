"""
FullStock AI vNext Ultimate - Background Task Scheduler
Handles model retraining, data updates, and system maintenance
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FullStockScheduler:
    """Advanced background task scheduler for FullStock AI"""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        
        # Schedule tasks
        self._schedule_model_retraining()
        self._schedule_data_updates()
        self._schedule_health_checks()
        self._schedule_system_maintenance()
        
        # Start scheduler
        self.scheduler.start()
        logger.info("FullStock AI Scheduler started successfully")
    
    def _schedule_model_retraining(self):
        """Schedule daily model retraining"""
        self.scheduler.add_job(
            func=self._retrain_models,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id='model_retraining',
            name='Retrain ML Models',
            replace_existing=True
        )
        
    def _schedule_data_updates(self):
        """Schedule frequent data updates"""
        # Market data updates every 5 minutes during trading hours
        self.scheduler.add_job(
            func=self._update_market_data,
            trigger=IntervalTrigger(minutes=5),
            id='market_data_update',
            name='Update Market Data',
            replace_existing=True
        )
        
        # Price alerts check every 30 seconds
        self.scheduler.add_job(
            func=self._check_price_alerts,
            trigger=IntervalTrigger(seconds=30),
            id='price_alerts',
            name='Check Price Alerts',
            replace_existing=True
        )
    
    def _schedule_health_checks(self):
        """Schedule system health monitoring"""
        self.scheduler.add_job(
            func=self._run_health_check,
            trigger=IntervalTrigger(minutes=10),
            id='health_check',
            name='System Health Check',
            replace_existing=True
        )
    
    def _schedule_system_maintenance(self):
        """Schedule system maintenance tasks"""
        # Daily log cleanup
        self.scheduler.add_job(
            func=self._cleanup_logs,
            trigger=CronTrigger(hour=1, minute=0),  # 1 AM daily
            id='log_cleanup',
            name='Cleanup Old Logs',
            replace_existing=True
        )
        
        # Weekly database optimization
        self.scheduler.add_job(
            func=self._optimize_database,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
            id='db_optimization',
            name='Database Optimization',
            replace_existing=True
        )
    
    def _retrain_models(self):
        """Retrain ML models with latest data"""
        try:
            logger.info("Starting scheduled model retraining...")
            
            # Import here to avoid circular imports
            from server.ml.ml_models import MLModelManager
            from server.ml.data_fetcher import DataFetcher
            
            data_fetcher = DataFetcher()
            ml_manager = MLModelManager()
            
            # Popular stocks to retrain on
            symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA']
            
            for symbol in symbols:
                try:
                    # Fetch latest data
                    data = data_fetcher.fetch_data(symbol, period='2y')
                    
                    if data is not None and len(data) > 100:
                        # Train models
                        rf_success = ml_manager.train_random_forest(data)
                        xgb_success = ml_manager.train_xgboost(data)
                        lstm_success = ml_manager.train_lstm(data)
                        
                        logger.info(f"Model retraining for {symbol}: RF={rf_success}, XGB={xgb_success}, LSTM={lstm_success}")
                    
                except Exception as e:
                    logger.error(f"Error retraining models for {symbol}: {str(e)}")
            
            logger.info("Scheduled model retraining completed")
            
        except Exception as e:
            logger.error(f"Error in scheduled model retraining: {str(e)}")
    
    def _update_market_data(self):
        """Update market data cache"""
        try:
            # Import here to avoid circular imports
            from server.ml.data_fetcher import DataFetcher
            
            data_fetcher = DataFetcher()
            
            # Update cache for popular symbols
            symbols = ['SPY', 'QQQ', 'BTC-USD', 'ETH-USD']
            
            for symbol in symbols:
                try:
                    data_fetcher.fetch_data(symbol, period='1d')
                except Exception as e:
                    logger.warning(f"Failed to update data for {symbol}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    def _check_price_alerts(self):
        """Check and send price alerts"""
        try:
            # Import here to avoid circular imports
            from server.utils.services.notification_service import check_price_alerts
            check_price_alerts()
            
        except Exception as e:
            logger.error(f"Error checking price alerts: {str(e)}")
    
    def _run_health_check(self):
        """Run system health checks"""
        try:
            # Import here to avoid circular imports
            from server.utils.strategic.health_monitor import run_health_check
            run_health_check()
            
        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
    
    def _cleanup_logs(self):
        """Clean up old log files"""
        try:
            logs_dir = 'logs'
            if os.path.exists(logs_dir):
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for filename in os.listdir(logs_dir):
                    filepath = os.path.join(logs_dir, filename)
                    if os.path.isfile(filepath):
                        file_date = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if file_date < cutoff_date:
                            os.remove(filepath)
                            logger.info(f"Removed old log file: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
    
    def _optimize_database(self):
        """Optimize database performance"""
        try:
            # Database optimization logic
            logger.info("Running database optimization...")
            
            # This could include:
            # - Vacuum operations for SQLite
            # - Index optimization
            # - Old data cleanup
            
        except Exception as e:
            logger.error(f"Error optimizing database: {str(e)}")
    
    def shutdown(self):
        """Shutdown scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("FullStock AI Scheduler stopped")

# Global scheduler instance
scheduler = FullStockScheduler()