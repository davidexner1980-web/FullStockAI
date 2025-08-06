import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///fullstock.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache settings
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
    POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', 'demo')
    
    # Model settings
    MODEL_CACHE_TIMEOUT = 3600  # 1 hour
    PREDICTION_CACHE_TIMEOUT = 300  # 5 minutes
    
    # Oracle mode settings
    ORACLE_EMOTIONAL_STATES = [
        'ECSTASY', 'SERENITY', 'WONDER', 'CONTEMPLATION', 
        'MELANCHOLY', 'DREAD'
    ]
    
    # Crypto settings
    SUPPORTED_CRYPTOS = [
        'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',
        'LTC-USD', 'BCH-USD', 'XLM-USD', 'VET-USD', 'UNI-USD'
    ]
    
    # WebSocket settings
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Rate limiting
    API_RATE_LIMIT = 100  # requests per minute

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
