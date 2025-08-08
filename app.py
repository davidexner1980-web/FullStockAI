import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO()
cache = Cache()
mail = Mail()

# Create the app with proper frontend/static separation
app = Flask(__name__, 
           template_folder='frontend',
           static_folder='frontend')
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key-for-development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///fullstock.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300

# Mail configuration
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

# Initialize extensions
db.init_app(app)
# Temporarily disable complex WebSocket setup for stability
# socketio.init_app(app, cors_allowed_origins="*")
# Basic setup for now
pass  # Disable SocketIO temporarily to fix API functionality
cache.init_app(app)
mail.init_app(app)

# Background scheduler for periodic tasks
scheduler = BackgroundScheduler(daemon=True)
scheduler.start()
atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("oracle_logs", exist_ok=True)
    os.makedirs("static/icons", exist_ok=True)

# Import and register blueprints
from server.api.main import main_bp
from server.api.api import api_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Background tasks
from server.utils.services.notification_service import check_price_alerts
from server.utils.strategic.health_monitor import run_health_check

# Schedule periodic tasks
scheduler.add_job(
    func=check_price_alerts,
    trigger="interval",
    seconds=30,
    id='price_alerts'
)

scheduler.add_job(
    func=run_health_check,
    trigger="interval",
    minutes=60,
    id='health_check'
)

# Add static file route for proper frontend asset serving
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files from frontend directory"""
    from flask import send_from_directory
    return send_from_directory('frontend', filename)

# Routes are handled by server/api blueprints
