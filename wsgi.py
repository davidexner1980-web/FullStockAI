"""
WSGI entry point for Gunicorn with eventlet support
"""
from app import app, socketio

# For gunicorn
application = app

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)