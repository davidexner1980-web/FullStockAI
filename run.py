#!/usr/bin/env python3
"""
FullStock AI vNext Ultimate - Main Entry Point
Production-ready Flask application with Gunicorn support
"""

import os
import logging
from app import app, socketio
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO if not app.debug else logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'data', 'models', 'logs', 'oracle_logs', 'docs',
        'static/icons', 'static/generated'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

def validate_environment():
    """Validate critical environment variables"""
    critical_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in critical_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
    
    return len(missing_vars) == 0

if __name__ == '__main__':
    # Initialize application
    create_directories()
    
    # Validate environment
    env_valid = validate_environment()
    if not env_valid:
        logger.warning("Some environment variables are missing. Application may not function properly.")
    
    # Load configuration
    app.config.from_object(Config)
    
    logger.info("Starting FullStock AI vNext Ultimate...")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Database: {Config.DATABASE_URL}")
    
    # Production server detection
    if os.environ.get('DYNO') or os.environ.get('RAILWAY_ENVIRONMENT'):
        # Production environment (Heroku/Railway)
        port = int(os.environ.get('PORT', 5000))
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    elif os.environ.get('REPLIT_DB_URL'):
        # Replit environment
        socketio.run(app, host='0.0.0.0', port=5000, debug=app.debug)
    else:
        # Development environment
        socketio.run(app, host='127.0.0.1', port=5000, debug=True)