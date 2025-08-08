# Gunicorn configuration for Flask-SocketIO with WebSocket support
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 512

# Worker processes optimized for Flask-SocketIO
workers = 1  # Single worker required for SocketIO
worker_class = "eventlet"  # Required for WebSocket support
worker_connections = 1000
timeout = 120  # Extended timeout for WebSocket connections
keepalive = 5

# Restart workers - adjusted for SocketIO stability
max_requests = 0  # Disable auto-restart for WebSocket stability
max_requests_jitter = 0
preload_app = False  # Disable preloading for SocketIO compatibility

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "fullstock_ai"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Extended settings for WebSocket stability
graceful_timeout = 120
user = None
group = None
tmp_upload_dir = None