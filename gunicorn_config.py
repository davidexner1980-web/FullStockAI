# Gunicorn configuration for Flask-SocketIO with WebSocket support
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes  
workers = 1  # Flask-SocketIO works best with 1 worker
worker_class = "eventlet"  # Use eventlet for WebSocket support
worker_connections = 1000
timeout = 30  # Standard timeout
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

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