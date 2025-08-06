import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging

class RandomForestPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def get_stock_data(self, ticker, period='1y'):
        """Fetch stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty:
                raise ValueError(f"No data found for {ticker}")
                
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {str(e)}")
            raise

    def prepare_features(self, data):
        """Prepare technical indicators and features"""
        try:
            # Moving averages
            data['sma_5'] = data['Close'].rolling(window=5).mean()
            data['sma_10'] = data['Close'].rolling(window=10).mean()
            data['sma_20'] = data['Close'].rolling(window=20).mean()
            data['sma_50'] = data['Close'].rolling(window=50).mean()
            
            # Exponential moving averages
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
            data['bb_position'] = (data['Close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
            
            # Volume indicators
            data['volume_sma'] = data['Volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['Volume'] / data['volume_sma']
            
            # Price momentum
            data['momentum_5'] = data['Close'] / data['Close'].shift(5) - 1
            data['momentum_10'] = data['Close'] / data['Close'].shift(10) - 1
            data['momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
            
            # Volatility
            data['volatility'] = data['Close'].rolling(window=20).std()
            
            # Support and resistance levels
            data['support'] = data['Low'].rolling(window=20).min()
            data['resistance'] = data['High'].rolling(window=20).max()
            data['support_distance'] = (data['Close'] - data['support']) / data['Close']
            data['resistance_distance'] = (data['resistance'] - data['Close']) / data['Close']
            
            # Target variable (next day's closing price)
            data['target'] = data['Close'].shift(-1)
            
            # Feature columns
            feature_columns = [
                'sma_5', 'sma_10', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_histogram', 'rsi', 'bb_position',
                'volume_ratio', 'momentum_5', 'momentum_10', 'momentum_20',
                'volatility', 'support_distance', 'resistance_distance'
            ]
            
            return data[feature_columns + ['target']].dropna()
            
        except Exception as e:
            logging.error(f"Feature preparation error: {str(e)}")
            raise

    def predict(self, ticker):
        """Make stock price prediction"""
        try:
            # Get historical data
            data = self.get_stock_data(ticker, period='1y')
            current_price = data['Close'].iloc[-1]
            
            # Prepare features
            processed_data = self.prepare_features(data)
            
            if len(processed_data) < 50:
                raise ValueError("Insufficient data for prediction")
            
            # Split features and target
            X = processed_data.drop('target', axis=1)
            y = processed_data['target']
            
            # Remove last row (no target available)
            X = X[:-1]
            y = y[:-1]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Prepare latest features for prediction
            latest_features = processed_data.drop('target', axis=1).iloc[-1:].values
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            predicted_price = self.model.predict(latest_features_scaled)[0]
            predicted_change = (predicted_price - current_price) / current_price * 100
            
            # Calculate confidence based on model performance
            feature_importance = self.model.feature_importances_
            confidence = min(0.9, max(0.3, np.mean(feature_importance) * 1.5))
            
            # Determine trading signal
            if predicted_change > 2:
                signal = 'BUY'
            elif predicted_change < -2:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Get top contributing features
            feature_names = [
                'sma_5', 'sma_10', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_histogram', 'rsi', 'bb_position',
                'volume_ratio', 'momentum_5', 'momentum_10', 'momentum_20',
                'volatility', 'support_distance', 'resistance_distance'
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
                'signal': signal,
                'model': 'Random Forest',
                'top_features': [{'feature': f, 'importance': float(imp)} for f, imp in top_features]
            }
            
        except Exception as e:
            logging.error(f"Random Forest prediction error for {ticker}: {str(e)}")
            raise

    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if not self.is_trained or self.model is None:
            return {}
        
        feature_names = [
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'macd', 'macd_signal', 'macd_histogram', 'rsi', 'bb_position',
            'volume_ratio', 'momentum_5', 'momentum_10', 'momentum_20',
            'volatility', 'support_distance', 'resistance_distance'
        ]
        
        return dict(zip(feature_names, self.model.feature_importances_))
