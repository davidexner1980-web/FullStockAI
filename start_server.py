#!/usr/bin/env python3
"""
FullStock AI Server Startup Script
Ensures proper WebSocket support with gevent
"""

from app import app, socketio

if __name__ == '__main__':
    print("🚀 Starting FullStock AI with WebSocket support...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        log_output=True
    )

