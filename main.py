from app import app, socketio

if __name__ == '__main__':
    # For development with Socket.IO support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)
else:
    # For production with gunicorn - app is imported directly
    # Use: gunicorn --config gunicorn_config.py main:app
    pass
