import json
import os
import sys
import types
import pathlib
import time

import eventlet
import eventlet.wsgi
import websocket

eventlet.monkey_patch()

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if 'app' in sys.modules:
    del sys.modules['app']

# Stub heavy modules to speed up imports
sys.modules['yfinance'] = types.ModuleType('yfinance')
sys.modules['server.ml.ml_models'] = types.ModuleType('server.ml.ml_models')
sys.modules['server.ml.ml_models'].MLModelManager = object
sys.modules['server.ml.data_fetcher'] = types.ModuleType('server.ml.data_fetcher')
sys.modules['server.ml.data_fetcher'].DataFetcher = object
mod_notif = types.ModuleType('server.utils.services.notification_service')
mod_notif.NotificationService = object
mod_notif.check_price_alerts = lambda: None
sys.modules['server.utils.services.notification_service'] = mod_notif
sys.modules['server.utils.services.oracle_service'] = types.ModuleType('server.utils.services.oracle_service')
sys.modules['server.utils.services.oracle_service'].OracleService = object
sys.modules['server.utils.services.crypto_service'] = types.ModuleType('server.utils.services.crypto_service')
sys.modules['server.utils.services.crypto_service'].CryptoService = object
sys.modules['server.utils.services.backtesting'] = types.ModuleType('server.utils.services.backtesting')
sys.modules['server.utils.services.backtesting'].BacktestingEngine = object
sys.modules['server.utils.services.sentiment_analyzer'] = types.ModuleType('server.utils.services.sentiment_analyzer')
sys.modules['server.utils.services.sentiment_analyzer'].SentimentAnalyzer = object
sys.modules['server.utils.strategic.curiosity_engine'] = types.ModuleType('server.utils.strategic.curiosity_engine')
sys.modules['server.utils.strategic.curiosity_engine'].CuriosityEngine = object
mod_health = types.ModuleType('server.utils.strategic.health_monitor')
mod_health.HealthMonitor = object
mod_health.run_health_check = lambda: None
sys.modules['server.utils.strategic.health_monitor'] = mod_health
sys.modules['server.utils.services.portfolio_manager'] = types.ModuleType('server.utils.services.portfolio_manager')
sys.modules['server.utils.services.portfolio_manager'].PortfolioManager = object

from app import app


def _run_server():
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 8765)), app)


def test_ws_quotes():
    server = eventlet.spawn(_run_server)
    time.sleep(1)

    ws = websocket.create_connection("ws://127.0.0.1:8765/ws/quotes")
    data = json.loads(ws.recv())
    ws.close()
    server.kill()

    assert "ticker" in data
