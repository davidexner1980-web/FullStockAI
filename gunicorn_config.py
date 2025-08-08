# Gunicorn configuration for Flask-SocketIO with WebSocket support
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 512

# Worker processes  
workers = 1  # Flask-SocketIO requires exactly 1 worker
worker_class = "eventlet"  # Use eventlet for WebSocket support
worker_connections = 1000
timeout = 120  # Increased timeout for SocketIO
keepalive = 2

# Restart workers - reduced to prevent socket issues
max_requests = 500
max_requests_jitter = 25
preload_app = False  # Disable preloading to prevent socket issues

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

# SocketIO specific settings
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"

# Additional WebSocket optimizations
max_requests_jitter = 50
worker_class_args = {
    'path': '/socket.io/',
    'resource': 'socket.io'
}