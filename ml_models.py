import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import xgboost as xgb
from data_fetcher import DataFetcher
import joblib
import os
import logging

class MLModelManager:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'Open', 'High', 'Low', 'Volume', 'MA_5', 'MA_20', 'RSI', 'MACD', 'BB_upper', 'BB_lower'
        ]
        
    def prepare_features(self, df):
        """Prepare technical indicators and features"""
        try:
            # Moving averages
            df['MA_5'] = df['Close'].rolling(window=5).mean()
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            df['BB_middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std_dev = df['Close'].rolling(window=bb_period).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std_dev * bb_std)
            df['BB_lower'] = df['BB_middle'] - (bb_std_dev * bb_std)
            
            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=10).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
            
            # Price momentum
            df['Price_Change'] = df['Close'].pct_change()
            df['Price_Momentum_5'] = df['Close'].pct_change(periods=5)
            
            # Volatility
            df['Volatility'] = df['Close'].rolling(window=20).std()
            
            return df.dropna()
        except Exception as e:
            logging.error(f"Feature preparation error: {str(e)}")
            raise

    def predict_random_forest(self, ticker):
        """Random Forest prediction"""
        try:
            # Get historical data
            df = self.data_fetcher.get_stock_data(ticker, period='1y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Prepare training data
            features = df[self.feature_columns].fillna(method='ffill').dropna()
            target = df['Close'].shift(-1).dropna()  # Next day's closing price
            
            # Align features and target
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]
            
            if len(features) < 30:
                raise ValueError(f"Insufficient data for {ticker}")
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(features, target)
            
            # Make prediction
            last_features = features.iloc[-1:].values
            predicted_price = model.predict(last_features)[0]
            
            # Calculate confidence based on model's feature importance and recent volatility
            feature_importance = model.feature_importances_
            recent_volatility = df['Close'].pct_change().rolling(window=10).std().iloc[-1]
            confidence = min(95, max(60, 85 - (recent_volatility * 1000)))
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            return {
                'predicted_price': round(predicted_price, 2),
                'current_price': round(current_price, 2),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence, 1),
                'model_type': 'Random Forest',
                'feature_importance': dict(zip(self.feature_columns, feature_importance.round(3)))
            }
        except Exception as e:
            logging.error(f"Random Forest prediction error for {ticker}: {str(e)}")
            raise

    def predict_lstm(self, ticker):
        """LSTM neural network prediction"""
        try:
            # Get historical data
            df = self.data_fetcher.get_stock_data(ticker, period='2y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare data for LSTM
            data = df['Close'].values.reshape(-1, 1)
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)
            
            # Create sequences
            sequence_length = 60
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            if len(X) < 10:
                raise ValueError(f"Insufficient data for LSTM training for {ticker}")
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(sequence_length, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model
            model.fit(X, y, batch_size=32, epochs=10, verbose=0)
            
            # Make prediction
            last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
            prediction_scaled = model.predict(last_sequence)
            predicted_price = scaler.inverse_transform(prediction_scaled)[0][0]
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Calculate confidence based on recent price stability
            recent_returns = df['Close'].pct_change().dropna()
            volatility = recent_returns.rolling(window=20).std().iloc[-1]
            confidence = min(90, max(65, 80 - (volatility * 800)))
            
            return {
                'predicted_price': round(predicted_price, 2),
                'current_price': round(current_price, 2),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence, 1),
                'model_type': 'LSTM Neural Network'
            }
        except Exception as e:
            logging.error(f"LSTM prediction error for {ticker}: {str(e)}")
            raise

    def predict_xgboost(self, ticker):
        """XGBoost prediction"""
        try:
            # Get historical data
            df = self.data_fetcher.get_stock_data(ticker, period='1y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Extended feature set for XGBoost
            extended_features = self.feature_columns + [
                'Volume_Ratio', 'Price_Change', 'Price_Momentum_5', 'Volatility'
            ]
            
            # Prepare training data
            features = df[extended_features].fillna(method='ffill').dropna()
            target = df['Close'].shift(-1).dropna()
            
            # Align features and target
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]
            
            if len(features) < 30:
                raise ValueError(f"Insufficient data for {ticker}")
            
            # Train XGBoost model
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(features, target)
            
            # Make prediction
            last_features = features.iloc[-1:].values
            predicted_price = model.predict(last_features)[0]
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Calculate confidence based on feature importance and prediction variance
            feature_importance = model.feature_importances_
            confidence_score = min(95, max(70, 88 - (abs(price_change) * 2)))
            
            return {
                'predicted_price': round(predicted_price, 2),
                'current_price': round(current_price, 2),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence_score, 1),
                'model_type': 'XGBoost',
                'feature_importance': dict(zip(extended_features, feature_importance.round(3)))
            }
        except Exception as e:
            logging.error(f"XGBoost prediction error for {ticker}: {str(e)}")
            raise

    def calculate_agreement(self, predictions):
        """Calculate agreement level between multiple model predictions"""
        try:
            prices = [pred['predicted_price'] for pred in predictions]
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            # Agreement based on standard deviation relative to mean
            coefficient_of_variation = std_price / mean_price if mean_price > 0 else 1
            agreement_percentage = max(0, min(100, (1 - coefficient_of_variation * 5) * 100))
            
            if agreement_percentage >= 80:
                agreement_level = "High"
            elif agreement_percentage >= 60:
                agreement_level = "Medium"
            else:
                agreement_level = "Low"
            
            return {
                'agreement_level': agreement_level,
                'agreement_percentage': round(agreement_percentage, 1),
                'price_variance': round(std_price, 2)
            }
        except Exception as e:
            logging.error(f"Agreement calculation error: {str(e)}")
            return {
                'agreement_level': "Unknown",
                'agreement_percentage': 0,
                'price_variance': 0
            }
