import os
import logging
import json
from datetime import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_mail import Mail
from flask_sock import Sock
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from server.utils.logging import JsonFormatter

# Configure structured logging
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO()
cache = Cache()
mail = Mail()
sock = Sock()

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
# Initialize SocketIO with a portable threading async mode
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)
cache.init_app(app)
mail.init_app(app)
sock.init_app(app)

# Background scheduler for periodic tasks - gevent compatible
scheduler = BackgroundScheduler(daemon=True)
if not scheduler.running:
    scheduler.start()
atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    db.create_all()
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("oracle_logs", exist_ok=True)
    os.makedirs("static/icons", exist_ok=True)

# Import and register blueprints
from server.api.main import main_bp  # noqa: E402
from server.api.api import api_bp  # noqa: E402

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Background tasks
from server.utils.services.notification_service import check_price_alerts  # noqa: E402
from server.utils.strategic.health_monitor import run_health_check  # noqa: E402

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


# Consistent JSON error responses
@app.errorhandler(Exception)
def handle_exception(err):
    code = getattr(err, "code", 500)
    response = {"error": type(err).__name__, "message": str(err)}
    return jsonify(response), code

# Add static file route for proper frontend asset serving
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files from frontend directory"""
    from flask import send_from_directory
    return send_from_directory('frontend', filename)

@sock.route('/ws/quotes')
def quotes(ws):
    """Stream basic quote updates over plain WebSocket"""
    while True:
        data = {
            'ticker': 'SPY',
            'timestamp': datetime.utcnow().isoformat()
        }
        ws.send(json.dumps(data))
        socketio.sleep(1)

# Routes are handled by server/api blueprints
