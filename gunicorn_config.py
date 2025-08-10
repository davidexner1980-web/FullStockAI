# Gunicorn configuration for Flask-Sock with gevent WebSocket support
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 512

# Worker processes optimized for WebSocket
workers = 1
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers - adjusted for WebSocket stability
max_requests = 0
max_requests_jitter = 0
preload_app = False

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
