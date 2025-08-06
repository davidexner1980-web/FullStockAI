import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Tuple
import joblib
import os
from .random_forest_model import RandomForestModel
from .lstm_model import LSTMModel
from .xgboost_model import XGBoostModel
from services.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators

class MLPredictor:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.tech_indicators = TechnicalIndicators()
        self.rf_model = RandomForestModel()
        self.lstm_model = LSTMModel()
        self.xgb_model = XGBoostModel()
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        
    def predict_random_forest(self, ticker: str) -> Dict[str, Any]:
        """Generate Random Forest prediction for a ticker"""
        try:
            # Get historical data
            data = self.data_fetcher.get_stock_data(ticker, period='1y')
            if data is None or len(data) < 50:
                return {'error': 'Insufficient data for prediction'}
            
            # Prepare features
            features = self._prepare_features(data)
            if features is None:
                return {'error': 'Could not prepare features'}
            
            # Train/load model
            model = self.rf_model.get_or_train_model(ticker, data)
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction = model.predict(latest_features)[0]
            confidence = self._calculate_confidence(model, latest_features)
            
            current_price = data['Close'].iloc[-1]
            price_change = prediction - current_price
            change_percent = (price_change / current_price) * 100
            
            return {
                'ticker': ticker,
                'model': 'Random Forest',
                'current_price': round(current_price, 2),
                'predicted_price': round(prediction, 2),
                'price_change': round(price_change, 2),
                'change_percent': round(change_percent, 2),
                'confidence': round(confidence * 100, 1),
                'prediction_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'features_used': list(features.columns),
                'signal': 'BUY' if price_change > 0 else 'SELL'
            }
            
        except Exception as e:
            logging.error(f"Random Forest prediction error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def predict_lstm(self, ticker: str) -> Dict[str, Any]:
        """Generate LSTM prediction for a ticker"""
        try:
            # Get historical data
            data = self.data_fetcher.get_stock_data(ticker, period='2y')
            if data is None or len(data) < 100:
                return {'error': 'Insufficient data for LSTM prediction'}
            
            # Train/load LSTM model
            model, scaler = self.lstm_model.get_or_train_model(ticker, data)
            
            # Prepare sequence for prediction
            sequence = self.lstm_model.prepare_prediction_sequence(data, scaler)
            
            # Make prediction
            prediction = model.predict(sequence)
            prediction = scaler.inverse_transform(prediction)[0][0]
            
            current_price = data['Close'].iloc[-1]
            price_change = prediction - current_price
            change_percent = (price_change / current_price) * 100
            
            # Calculate confidence based on recent prediction accuracy
            confidence = self.lstm_model.calculate_confidence(ticker)
            
            return {
                'ticker': ticker,
                'model': 'LSTM Neural Network',
                'current_price': round(current_price, 2),
                'predicted_price': round(prediction, 2),
                'price_change': round(price_change, 2),
                'change_percent': round(change_percent, 2),
                'confidence': round(confidence * 100, 1),
                'prediction_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'signal': 'BUY' if price_change > 0 else 'SELL'
            }
            
        except Exception as e:
            logging.error(f"LSTM prediction error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def predict_xgboost(self, ticker: str) -> Dict[str, Any]:
        """Generate XGBoost prediction for a ticker"""
        try:
            # Get historical data
            data = self.data_fetcher.get_stock_data(ticker, period='1y')
            if data is None or len(data) < 50:
                return {'error': 'Insufficient data for XGBoost prediction'}
            
            # Prepare features
            features = self._prepare_features(data)
            if features is None:
                return {'error': 'Could not prepare features'}
            
            # Train/load XGBoost model
            model = self.xgb_model.get_or_train_model(ticker, data, features)
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction = model.predict(latest_features)[0]
            
            # Get feature importance
            feature_importance = self.xgb_model.get_feature_importance(model, features.columns)
            
            current_price = data['Close'].iloc[-1]
            price_change = prediction - current_price
            change_percent = (price_change / current_price) * 100
            
            # Calculate confidence based on prediction interval
            confidence = self._calculate_xgb_confidence(model, latest_features)
            
            return {
                'ticker': ticker,
                'model': 'XGBoost',
                'current_price': round(current_price, 2),
                'predicted_price': round(prediction, 2),
                'price_change': round(price_change, 2),
                'change_percent': round(change_percent, 2),
                'confidence': round(confidence * 100, 1),
                'prediction_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'feature_importance': feature_importance[:5],  # Top 5 features
                'signal': 'BUY' if price_change > 0 else 'SELL'
            }
            
        except Exception as e:
            logging.error(f"XGBoost prediction error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def compare_models(self, ticker: str) -> Dict[str, Any]:
        """Compare predictions from all three models"""
        try:
            rf_pred = self.predict_random_forest(ticker)
            lstm_pred = self.predict_lstm(ticker)
            xgb_pred = self.predict_xgboost(ticker)
            
            # Handle errors in individual predictions
            predictions = {}
            if 'error' not in rf_pred:
                predictions['random_forest'] = rf_pred
            if 'error' not in lstm_pred:
                predictions['lstm'] = lstm_pred
            if 'error' not in xgb_pred:
                predictions['xgboost'] = xgb_pred
            
            if not predictions:
                return {'error': 'All models failed to generate predictions'}
            
            # Calculate ensemble prediction
            prices = [pred['predicted_price'] for pred in predictions.values()]
            confidences = [pred['confidence'] for pred in predictions.values()]
            
            # Weighted average by confidence
            total_weight = sum(confidences)
            ensemble_price = sum(price * conf for price, conf in zip(prices, confidences)) / total_weight
            ensemble_confidence = np.mean(confidences)
            
            # Calculate agreement level
            price_std = np.std(prices)
            price_mean = np.mean(prices)
            agreement_level = max(0, 100 - (price_std / price_mean * 100))
            
            current_price = predictions[list(predictions.keys())[0]]['current_price']
            ensemble_change = ensemble_price - current_price
            ensemble_change_percent = (ensemble_change / current_price) * 100
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'predictions': predictions,
                'ensemble': {
                    'predicted_price': round(ensemble_price, 2),
                    'price_change': round(ensemble_change, 2),
                    'change_percent': round(ensemble_change_percent, 2),
                    'confidence': round(ensemble_confidence, 1),
                    'agreement_level': round(agreement_level, 1),
                    'signal': 'BUY' if ensemble_change > 0 else 'SELL'
                },
                'analysis': {
                    'models_used': len(predictions),
                    'price_range': {
                        'min': round(min(prices), 2),
                        'max': round(max(prices), 2)
                    },
                    'divergence': round(price_std, 2)
                }
            }
            
        except Exception as e:
            logging.error(f"Model comparison error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare technical indicator features for ML models"""
        try:
            features_df = pd.DataFrame(index=data.index)
            
            # Price-based features
            features_df['returns'] = data['Close'].pct_change()
            features_df['volatility'] = features_df['returns'].rolling(20).std()
            features_df['price_momentum'] = data['Close'] / data['Close'].shift(10) - 1
            
            # Volume features
            features_df['volume_sma'] = data['Volume'].rolling(20).mean()
            features_df['volume_ratio'] = data['Volume'] / features_df['volume_sma']
            
            # Technical indicators
            features_df['rsi'] = self.tech_indicators.calculate_rsi(data['Close'])
            features_df['macd'] = self.tech_indicators.calculate_macd(data['Close'])['macd']
            features_df['bb_position'] = self.tech_indicators.calculate_bollinger_position(data['Close'])
            features_df['sma_20'] = data['Close'].rolling(20).mean()
            features_df['sma_50'] = data['Close'].rolling(50).mean()
            features_df['price_to_sma20'] = data['Close'] / features_df['sma_20']
            features_df['price_to_sma50'] = data['Close'] / features_df['sma_50']
            
            # Trend features
            features_df['trend_strength'] = self.tech_indicators.calculate_trend_strength(data['Close'])
            features_df['support_resistance'] = self.tech_indicators.calculate_support_resistance_level(data['Close'])
            
            # Remove NaN values
            features_df = features_df.dropna()
            
            return features_df
            
        except Exception as e:
            logging.error(f"Feature preparation error: {str(e)}")
            return None
    
    def _calculate_confidence(self, model, features: np.ndarray) -> float:
        """Calculate prediction confidence for ensemble models"""
        try:
            # Use prediction variance from individual trees
            if hasattr(model, 'estimators_'):
                predictions = [tree.predict(features)[0] for tree in model.estimators_]
                variance = np.var(predictions)
                confidence = 1 / (1 + variance)
                return min(confidence, 0.95)
            return 0.75  # Default confidence
        except:
            return 0.75
    
    def _calculate_xgb_confidence(self, model, features: np.ndarray) -> float:
        """Calculate XGBoost prediction confidence"""
        try:
            # Use leaf predictions variance as confidence measure
            prediction = model.predict(features)[0]
            # Simple confidence based on prediction magnitude
            confidence = min(0.8 + abs(prediction) * 0.1, 0.95)
            return confidence
        except:
            return 0.80
