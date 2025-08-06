import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib
import logging
from datetime import datetime, timedelta
import os
from .data_fetcher import DataFetcher

class PredictionEngine:
    """Enhanced prediction engine with Random Forest and LSTM models"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.rf_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.models_trained = False
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
    
    def _prepare_features(self, data):
        """Prepare features for machine learning models"""
        try:
            # Ensure we have enough data
            if len(data) < 50:
                raise ValueError("Insufficient data for prediction")
            
            features = pd.DataFrame()
            
            # Price-based features
            features['price_momentum_5'] = data['Close'].pct_change(5)
            features['price_momentum_10'] = data['Close'].pct_change(10)
            features['price_momentum_20'] = data['Close'].pct_change(20)
            
            # Technical indicators
            features['sma_ratio_10'] = data['Close'] / data['SMA_10']
            features['sma_ratio_20'] = data['Close'] / data['SMA_20']
            features['sma_ratio_50'] = data['Close'] / data['SMA_50']
            
            features['rsi'] = data['RSI']
            features['macd'] = data['MACD']
            features['macd_signal'] = data['MACD_Signal']
            features['macd_histogram'] = data['MACD_Histogram']
            
            # Bollinger Bands
            features['bb_position'] = (data['Close'] - data['BB_Lower']) / (data['BB_Upper'] - data['BB_Lower'])
            features['bb_width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']
            
            # Volume features
            features['volume_ratio'] = data['Volume_Ratio']
            features['price_volume'] = data['Close'] * data['Volume']
            
            # Volatility features
            features['volatility'] = data['Volatility']
            features['high_low_ratio'] = data['High'] / data['Low']
            
            # Lag features
            for lag in [1, 2, 3, 5]:
                features[f'close_lag_{lag}'] = data['Close'].shift(lag)
                features[f'volume_lag_{lag}'] = data['Volume'].shift(lag)
            
            # Target variable (next day close price)
            features['target'] = data['Close'].shift(-1)
            
            # Remove rows with NaN values
            features = features.dropna()
            
            self.feature_columns = [col for col in features.columns if col != 'target']
            
            return features
            
        except Exception as e:
            logging.error(f"Error preparing features: {str(e)}")
            raise
    
    def train_random_forest(self, ticker, retrain=False):
        """Train Random Forest model"""
        try:
            model_path = f'models/rf_model_{ticker}.joblib'
            
            # Load existing model if available and not retraining
            if os.path.exists(model_path) and not retrain:
                self.rf_model = joblib.load(model_path)
                self.models_trained = True
                return True
            
            # Get training data
            data = self.data_fetcher.get_stock_data(ticker, period='2y')
            features_df = self._prepare_features(data)
            
            if len(features_df) < 100:
                raise ValueError("Insufficient data for training")
            
            X = features_df[self.feature_columns]
            y = features_df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.rf_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.rf_model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logging.info(f"Random Forest trained for {ticker} - MSE: {mse:.4f}, R2: {r2:.4f}")
            
            # Save model
            joblib.dump(self.rf_model, model_path)
            joblib.dump(self.scaler, f'models/scaler_{ticker}.joblib')
            
            self.models_trained = True
            return True
            
        except Exception as e:
            logging.error(f"Error training Random Forest for {ticker}: {str(e)}")
            return False
    
    def train_lstm(self, ticker, retrain=False):
        """Train LSTM model"""
        try:
            model_path = f'models/lstm_model_{ticker}.h5'
            
            # Load existing model if available and not retraining
            if os.path.exists(model_path) and not retrain:
                self.lstm_model = tf.keras.models.load_model(model_path)
                return True
            
            # Get training data
            data = self.data_fetcher.get_stock_data(ticker, period='2y')
            
            # Prepare LSTM data
            close_prices = data['Close'].values
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(close_prices.reshape(-1, 1))
            
            # Create sequences
            sequence_length = 60
            X, y = [], []
            
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            if len(X) < 100:
                raise ValueError("Insufficient data for LSTM training")
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build LSTM model
            self.lstm_model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(1)
            ])
            
            self.lstm_model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model
            self.lstm_model.fit(
                X_train, y_train,
                batch_size=32,
                epochs=50,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # Save model
            self.lstm_model.save(model_path)
            joblib.dump(scaler, f'models/lstm_scaler_{ticker}.joblib')
            
            logging.info(f"LSTM model trained for {ticker}")
            return True
            
        except Exception as e:
            logging.error(f"Error training LSTM for {ticker}: {str(e)}")
            return False
    
    def predict_random_forest(self, ticker):
        """Make Random Forest prediction"""
        try:
            # Train model if not already trained
            if not self.rf_model:
                self.train_random_forest(ticker)
            
            # Get recent data
            data = self.data_fetcher.get_stock_data(ticker, period='1y')
            features_df = self._prepare_features(data)
            
            if features_df.empty:
                raise ValueError("No features available for prediction")
            
            # Get latest features
            latest_features = features_df[self.feature_columns].iloc[-1:].values
            
            # Load scaler
            scaler_path = f'models/scaler_{ticker}.joblib'
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
                latest_features = scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.rf_model.predict(latest_features)[0]
            
            # Calculate confidence based on feature importance and recent performance
            feature_importance = self.rf_model.feature_importances_
            confidence = min(0.95, max(0.6, np.mean(feature_importance) * 100))
            
            current_price = data['Close'].iloc[-1]
            change_percent = ((prediction - current_price) / current_price) * 100
            
            # Determine signal
            if change_percent > 2:
                signal = 'BUY'
            elif change_percent < -2:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            result = {
                'model': 'Random Forest',
                'ticker': ticker,
                'current_price': float(current_price),
                'prediction': float(prediction),
                'change_percent': float(change_percent),
                'confidence': float(confidence),
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Random Forest prediction error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def predict_lstm(self, ticker):
        """Make LSTM prediction"""
        try:
            # Train model if not available
            if not self.lstm_model:
                self.train_lstm(ticker)
            
            # Get recent data
            data = self.data_fetcher.get_stock_data(ticker, period='6m')
            close_prices = data['Close'].values
            
            # Load scaler
            scaler_path = f'models/lstm_scaler_{ticker}.joblib'
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
            else:
                scaler = StandardScaler()
                scaler.fit(close_prices.reshape(-1, 1))
            
            # Prepare sequence
            scaled_data = scaler.transform(close_prices.reshape(-1, 1))
            sequence = scaled_data[-60:].reshape(1, 60, 1)
            
            # Make prediction
            scaled_prediction = self.lstm_model.predict(sequence, verbose=0)[0][0]
            prediction = scaler.inverse_transform([[scaled_prediction]])[0][0]
            
            current_price = data['Close'].iloc[-1]
            change_percent = ((prediction - current_price) / current_price) * 100
            
            # Calculate confidence based on recent volatility
            volatility = data['Close'].pct_change().std()
            confidence = max(0.6, min(0.9, 1 - volatility * 10))
            
            # Determine signal
            if change_percent > 1.5:
                signal = 'BUY'
            elif change_percent < -1.5:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            result = {
                'model': 'LSTM',
                'ticker': ticker,
                'current_price': float(current_price),
                'prediction': float(prediction),
                'change_percent': float(change_percent),
                'confidence': float(confidence),
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"LSTM prediction error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def get_trading_signals(self, ticker):
        """Get comprehensive trading signals from multiple strategies"""
        try:
            data = self.data_fetcher.get_stock_data(ticker, period='6m')
            
            signals = {}
            
            # Moving Average Crossover
            if data['SMA_10'].iloc[-1] > data['SMA_20'].iloc[-1]:
                signals['ma_crossover'] = {'signal': 'BUY', 'confidence': 0.7}
            else:
                signals['ma_crossover'] = {'signal': 'SELL', 'confidence': 0.7}
            
            # RSI Strategy
            rsi = data['RSI'].iloc[-1]
            if rsi < 30:
                signals['rsi'] = {'signal': 'BUY', 'confidence': 0.8}
            elif rsi > 70:
                signals['rsi'] = {'signal': 'SELL', 'confidence': 0.8}
            else:
                signals['rsi'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # MACD Strategy
            if data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1]:
                signals['macd'] = {'signal': 'BUY', 'confidence': 0.75}
            else:
                signals['macd'] = {'signal': 'SELL', 'confidence': 0.75}
            
            # Bollinger Bands
            bb_position = ((data['Close'].iloc[-1] - data['BB_Lower'].iloc[-1]) / 
                          (data['BB_Upper'].iloc[-1] - data['BB_Lower'].iloc[-1]))
            
            if bb_position < 0.2:
                signals['bollinger'] = {'signal': 'BUY', 'confidence': 0.6}
            elif bb_position > 0.8:
                signals['bollinger'] = {'signal': 'SELL', 'confidence': 0.6}
            else:
                signals['bollinger'] = {'signal': 'HOLD', 'confidence': 0.4}
            
            # Volume Analysis
            volume_ratio = data['Volume_Ratio'].iloc[-1]
            if volume_ratio > 1.5:
                signals['volume'] = {'signal': 'BUY', 'confidence': 0.65}
            elif volume_ratio < 0.5:
                signals['volume'] = {'signal': 'SELL', 'confidence': 0.65}
            else:
                signals['volume'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Momentum Strategy
            momentum_5 = data['Close'].pct_change(5).iloc[-1]
            if momentum_5 > 0.05:
                signals['momentum'] = {'signal': 'BUY', 'confidence': 0.7}
            elif momentum_5 < -0.05:
                signals['momentum'] = {'signal': 'SELL', 'confidence': 0.7}
            else:
                signals['momentum'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Volatility Breakout
            volatility = data['Volatility'].iloc[-1]
            if volatility > data['Volatility'].rolling(20).mean().iloc[-1] * 1.5:
                signals['volatility'] = {'signal': 'BUY', 'confidence': 0.6}
            else:
                signals['volatility'] = {'signal': 'HOLD', 'confidence': 0.4}
            
            # Calculate overall signal
            buy_signals = sum(1 for s in signals.values() if s['signal'] == 'BUY')
            sell_signals = sum(1 for s in signals.values() if s['signal'] == 'SELL')
            total_confidence = sum(s['confidence'] for s in signals.values()) / len(signals)
            
            if buy_signals > sell_signals:
                overall_signal = 'BUY'
            elif sell_signals > buy_signals:
                overall_signal = 'SELL'
            else:
                overall_signal = 'HOLD'
            
            result = {
                'ticker': ticker,
                'individual_signals': signals,
                'overall_signal': overall_signal,
                'confidence': total_confidence,
                'signal_strength': max(buy_signals, sell_signals) / len(signals),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Trading signals error for {ticker}: {str(e)}")
            return {'error': str(e)}
