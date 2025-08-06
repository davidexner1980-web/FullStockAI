import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from services.data_fetcher import DataFetcher
import logging

class XGBoostPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.data_fetcher = DataFetcher()
        self.is_trained = False
        
    def prepare_features(self, data):
        """Prepare features for XGBoost model"""
        try:
            # Technical indicators
            data['sma_5'] = data['Close'].rolling(window=5).mean()
            data['sma_20'] = data['Close'].rolling(window=20).mean()
            data['ema_12'] = data['Close'].ewm(span=12).mean()
            data['ema_26'] = data['Close'].ewm(span=26).mean()
            
            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            data['bb_middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
            data['bb_width'] = data['bb_upper'] - data['bb_lower']
            data['bb_position'] = (data['Close'] - data['bb_lower']) / data['bb_width']
            
            # Volume indicators
            data['volume_sma'] = data['Volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['Volume'] / data['volume_sma']
            
            # Price momentum
            data['momentum_5'] = data['Close'] / data['Close'].shift(5) - 1
            data['momentum_10'] = data['Close'] / data['Close'].shift(10) - 1
            data['momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
            
            # Volatility
            data['volatility'] = data['Close'].rolling(window=20).std()
            data['volatility_ratio'] = data['volatility'] / data['volatility'].rolling(window=60).mean()
            
            # Price patterns
            data['high_low_ratio'] = data['High'] / data['Low']
            data['close_open_ratio'] = data['Close'] / data['Open']
            
            # Target variable (next day's return)
            data['target'] = (data['Close'].shift(-1) / data['Close'] - 1) * 100
            
            # Select feature columns
            feature_columns = [
                'sma_5', 'sma_20', 'ema_12', 'ema_26', 'macd', 'macd_signal', 
                'macd_histogram', 'rsi', 'bb_position', 'bb_width', 'volume_ratio',
                'momentum_5', 'momentum_10', 'momentum_20', 'volatility_ratio',
                'high_low_ratio', 'close_open_ratio'
            ]
            
            return data[feature_columns + ['target']].dropna()
            
        except Exception as e:
            logging.error(f"Feature preparation error: {str(e)}")
            raise

    def train_model(self, ticker):
        """Train XGBoost model on historical data"""
        try:
            # Get historical data
            historical_data = self.data_fetcher.get_historical_data(ticker, period='2y')
            
            # Prepare features
            data = self.prepare_features(historical_data)
            
            # Split features and target
            X = data.drop('target', axis=1)
            y = data['target']
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train XGBoost model
            self.model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                objective='reg:squarederror'
            )
            
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True
            
            # Calculate training metrics
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            logging.info(f"XGBoost model trained for {ticker}. Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
            
            return {
                'train_score': train_score,
                'test_score': test_score,
                'feature_importance': dict(zip(X.columns, self.model.feature_importances_))
            }
            
        except Exception as e:
            logging.error(f"Model training error: {str(e)}")
            raise

    def predict(self, ticker):
        """Make prediction for given ticker"""
        try:
            # Get recent data
            recent_data = self.data_fetcher.get_historical_data(ticker, period='3mo')
            current_price = recent_data['Close'].iloc[-1]
            
            # Train model if not already trained
            if not self.is_trained:
                self.train_model(ticker)
            
            # Prepare features for latest data point
            data = self.prepare_features(recent_data)
            latest_features = data.drop('target', axis=1).iloc[-1:].values
            
            # Scale features
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction (returns percentage change)
            predicted_change = self.model.predict(latest_features_scaled)[0]
            predicted_price = current_price * (1 + predicted_change / 100)
            
            # Calculate confidence based on feature importance and model certainty
            feature_importance = self.model.feature_importances_
            confidence = min(0.95, max(0.3, np.mean(feature_importance) * 1.5))
            
            # Get top contributing features
            feature_names = [
                'sma_5', 'sma_20', 'ema_12', 'ema_26', 'macd', 'macd_signal', 
                'macd_histogram', 'rsi', 'bb_position', 'bb_width', 'volume_ratio',
                'momentum_5', 'momentum_10', 'momentum_20', 'volatility_ratio',
                'high_low_ratio', 'close_open_ratio'
            ]
            
            top_features = sorted(
                zip(feature_names, feature_importance), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return {
                'ticker': ticker,
                'current_price': float(current_price),
                'prediction': float(predicted_price),
                'predicted_change': float(predicted_change),
                'confidence': float(confidence),
                'model': 'XGBoost',
                'top_features': [{'feature': f, 'importance': float(imp)} for f, imp in top_features],
                'signal': 'BUY' if predicted_change > 1 else 'SELL' if predicted_change < -1 else 'HOLD'
            }
            
        except Exception as e:
            logging.error(f"XGBoost prediction error for {ticker}: {str(e)}")
            raise

    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if not self.is_trained or self.model is None:
            return {}
        
        feature_names = [
            'sma_5', 'sma_20', 'ema_12', 'ema_26', 'macd', 'macd_signal', 
            'macd_histogram', 'rsi', 'bb_position', 'bb_width', 'volume_ratio',
            'momentum_5', 'momentum_10', 'momentum_20', 'volatility_ratio',
            'high_low_ratio', 'close_open_ratio'
        ]
        
        return dict(zip(feature_names, self.model.feature_importances_))
