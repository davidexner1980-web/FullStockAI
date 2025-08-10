import sys
import types
import pathlib
import pandas as pd
import pytest
from flask import Flask
from flask_caching import Cache
from flask_socketio import SocketIO

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


# Stub external dependencies to keep tests lightweight
class DummyDataFetcher:
    def get_stock_data(self, ticker, period='1y'):
        return pd.DataFrame(
            {
                'Open': [1.0],
                'High': [1.0],
                'Low': [1.0],
                'Close': [1.0],
                'Volume': [100],
            },
            index=[pd.Timestamp('2024-01-01')],
        )


class DummyMLManager:
    def predict_random_forest(self, data):
        return {'prediction': 2.0}

    def predict_lstm(self, data):
        return {'prediction': 3.0}

    def predict_xgboost(self, data):
        return {'prediction': 4.0}


class DummyService:
    def __init__(self, *args, **kwargs):
        pass


sys.modules['server.ml.ml_models'] = types.ModuleType('server.ml.ml_models')
sys.modules['server.ml.ml_models'].MLModelManager = DummyMLManager
sys.modules['server.ml.data_fetcher'] = types.ModuleType('server.ml.data_fetcher')
sys.modules['server.ml.data_fetcher'].DataFetcher = DummyDataFetcher
sys.modules['server.utils.services.oracle_service'] = types.ModuleType('server.utils.services.oracle_service')
sys.modules['server.utils.services.oracle_service'].OracleService = DummyService
sys.modules['server.utils.services.crypto_service'] = types.ModuleType('server.utils.services.crypto_service')
sys.modules['server.utils.services.crypto_service'].CryptoService = DummyService
sys.modules['server.utils.services.backtesting'] = types.ModuleType('server.utils.services.backtesting')
sys.modules['server.utils.services.backtesting'].BacktestingEngine = DummyService
sys.modules['server.utils.services.notification_service'] = types.ModuleType('server.utils.services.notification_service')
sys.modules['server.utils.services.notification_service'].NotificationService = DummyService
sys.modules['server.utils.services.sentiment_analyzer'] = types.ModuleType('server.utils.services.sentiment_analyzer')
sys.modules['server.utils.services.sentiment_analyzer'].SentimentAnalyzer = DummyService
sys.modules['server.utils.strategic.curiosity_engine'] = types.ModuleType('server.utils.strategic.curiosity_engine')
sys.modules['server.utils.strategic.curiosity_engine'].CuriosityEngine = DummyService
sys.modules['server.utils.strategic.health_monitor'] = types.ModuleType('server.utils.strategic.health_monitor')
sys.modules['server.utils.strategic.health_monitor'].HealthMonitor = DummyService
sys.modules['server.utils.services.portfolio_manager'] = types.ModuleType('server.utils.services.portfolio_manager')
sys.modules['server.utils.services.portfolio_manager'].PortfolioManager = DummyService

# Create a minimal 'app' module expected by server.api.api
flask_app = Flask(__name__)
socketio = SocketIO(flask_app, async_mode='threading', logger=False, engineio_logger=False)
cache = Cache(flask_app)
dummy_app = types.ModuleType('app')
dummy_app.cache = cache
dummy_app.socketio = socketio
sys.modules['app'] = dummy_app

from server.api import api

flask_app.register_blueprint(api.api_bp, url_prefix='/api')


def test_http_and_ws_prediction_consistency():
    client = flask_app.test_client()
    sio_client = socketio.test_client(flask_app)

    http_resp = client.get('/api/predict/TEST')
    assert http_resp.status_code == 200
    http_data = http_resp.get_json()

    sio_client.emit('request_prediction', {'ticker': 'TEST'})
    received = sio_client.get_received()
    ws_data = None
    for event in received:
        if event['name'] == 'prediction_update':
            ws_data = event['args'][0]
            break

    assert ws_data is not None
    assert http_data['predictions'] == ws_data['predictions']
    assert http_data['agreement_level'] == ws_data['agreement_level']
    assert http_data['ticker'] == ws_data['ticker'] == 'TEST'

    sio_client.disconnect()

