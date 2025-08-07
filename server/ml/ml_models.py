import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import logging
import joblib
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union

# Conditional TensorFlow imports - prevent startup crashes
TENSORFLOW_AVAILABLE = False
tf = None
keras = None
layers = None

def _load_tensorflow():
    """Safely load TensorFlow with comprehensive error handling"""
    global TENSORFLOW_AVAILABLE, tf, keras, layers
    try:
        # Suppress TensorFlow warnings
        import os
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        import tensorflow as tf_module
        tf = tf_module
        keras = tf_module.keras
        layers = tf_module.keras.layers
        TENSORFLOW_AVAILABLE = True
        logging.info(f"TensorFlow {tf_module.__version__} loaded successfully for LSTM models")
        return True
    except ImportError as e:
        logging.warning(f"TensorFlow not available: {str(e)}")
        return False
    except Exception as e:
        logging.warning(f"TensorFlow failed to load: {str(e)}")
        return False

# Don't load TensorFlow during import - will be loaded lazily when needed

class MLModelManager:
    """Enhanced ML model manager with XGBoost and improved LSTM"""
    
    def __init__(self):
        self.models: Dict[str, Optional[Any]] = {
            'random_forest': None,
            'xgboost': None,
            'lstm': None
        }
        self.scalers: Dict[str, Any] = {
            'features': StandardScaler(),
            'target': MinMaxScaler()
        }
        self.feature_columns = [
            'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26', 'MACD', 'MACD_Signal',
            'RSI', 'BB_Upper', 'BB_Lower', 'Stoch_K', 'Stoch_D', 'Williams_R',
            'ATR', 'OBV', 'MOM', 'ROC', 'Volatility', 'Volume_Ratio'
        ]
    
    def prepare_features(self, data):
        """Prepare features for ML models with comprehensive technical indicators"""
        try:
            # Create a copy to avoid modifying original data
            df = data.copy()
            
            # Calculate technical indicators
            df = self._calculate_technical_indicators(df)
            
            # Select available feature columns
            available_features = [col for col in self.feature_columns if col in df.columns]
            
            if not available_features:
                # Fallback to basic features if technical indicators aren't available
                basic_features = ['Open', 'High', 'Low', 'Volume']
                available_features = [col for col in basic_features if col in df.columns]
                
                if not available_features:
                    logging.error("No usable features found in data")
                    return None, None
            
            # Extract features and target with proper forward-fill
            features = df[available_features].ffill().fillna(0)
            target = df['Close'].shift(-1).fillna(df['Close'].iloc[-1])
            
            # Remove last row as it doesn't have a target
            features = features.iloc[:-1]
            target = target.iloc[:-1]
            
            if len(features) < 10:
                logging.warning("Insufficient data for training")
                return None, None
                
            logging.info(f"Prepared {len(features)} samples with {len(available_features)} features")
            return features, target
            
        except Exception as e:
            logging.error(f"Error preparing features: {str(e)}")
            return None, None
    
    def _calculate_technical_indicators(self, df):
        """Calculate comprehensive technical indicators"""
        try:
            # Simple Moving Averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Exponential Moving Averages  
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            bb_period = 20
            df['BB_Middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std = df['Close'].rolling(window=bb_period).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            # Stochastic Oscillator
            low_14 = df['Low'].rolling(window=14).min()
            high_14 = df['High'].rolling(window=14).max()
            df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
            df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
            
            # Williams %R
            df['Williams_R'] = -100 * ((high_14 - df['Close']) / (high_14 - low_14))
            
            # Average True Range (ATR)
            df['H_L'] = df['High'] - df['Low']
            df['H_C'] = abs(df['High'] - df['Close'].shift(1))
            df['L_C'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H_L', 'H_C', 'L_C']].max(axis=1)
            df['ATR'] = df['TR'].rolling(window=14).mean()
            
            # On Balance Volume (OBV)
            df['OBV'] = (df['Volume'] * ((df['Close'] - df['Close'].shift(1)) > 0).astype(int)).cumsum()
            
            # Momentum
            df['MOM'] = df['Close'] - df['Close'].shift(10)
            
            # Rate of Change
            df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100
            
            # Volatility
            df['Volatility'] = df['Close'].rolling(window=20).std()
            
            # Volume Ratio
            df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
            
            # Clean up temporary columns
            df.drop(['H_L', 'H_C', 'L_C', 'TR'], axis=1, inplace=True, errors='ignore')
            
            return df
            
        except Exception as e:
            logging.error(f"Error calculating technical indicators: {str(e)}")
            return df
    
    def train_random_forest(self, data):
        """Train Random Forest model"""
        try:
            features, target = self.prepare_features(data)
            if features is None:
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Scale features
            X_train_scaled = self.scalers['features'].fit_transform(X_train)
            X_test_scaled = self.scalers['features'].transform(X_test)
            
            # Train model
            self.models['random_forest'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.models['random_forest'].fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.models['random_forest'].predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logging.info(f"Random Forest - MSE: {mse:.4f}, R²: {r2:.4f}")
            
            # Save model
            os.makedirs('models', exist_ok=True)
            joblib.dump(self.models['random_forest'], 'models/random_forest.joblib')
            joblib.dump(self.scalers['features'], 'models/feature_scaler.joblib')
            
            return True
            
        except Exception as e:
            logging.error(f"Error training Random Forest: {str(e)}")
            return False
    
    def train_xgboost(self, data):
        """Train XGBoost model"""
        try:
            features, target = self.prepare_features(data)
            if features is None:
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42, shuffle=False
            )
            
            # XGBoost parameters
            params = {
                'objective': 'reg:squarederror',
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }
            
            # Create DMatrix
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtest = xgb.DMatrix(X_test, label=y_test)
            
            # Train model
            self.models['xgboost'] = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                evals=[(dtest, 'test')],
                early_stopping_rounds=10,
                verbose_eval=False
            )
            
            # Evaluate
            y_pred = self.models['xgboost'].predict(dtest)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logging.info(f"XGBoost - MSE: {mse:.4f}, R²: {r2:.4f}")
            
            # Save model
            self.models['xgboost'].save_model('models/xgboost.model')
            
            return True
            
        except Exception as e:
            logging.error(f"Error training XGBoost: {str(e)}")
            return False
    
    def train_lstm(self, data, sequence_length=60):
        """Train LSTM model"""
        # Load TensorFlow if not already loaded
        if not TENSORFLOW_AVAILABLE:
            success = _load_tensorflow()
            if not success:
                logging.warning("Cannot train LSTM: TensorFlow not available")
                return False
            
        try:
            # Prepare data for LSTM
            close_prices = data['Close'].values.reshape(-1, 1)
            
            # Scale data
            self.scalers['target'].fit(close_prices)
            scaled_data = self.scalers['target'].transform(close_prices)
            
            # Create sequences
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            X = np.reshape(X, (X.shape[0], X.shape[1], 1))
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Build LSTM model
            self.models['lstm'] = keras.Sequential([
                layers.LSTM(50, return_sequences=True, input_shape=(sequence_length, 1)),
                layers.Dropout(0.2),
                layers.LSTM(50, return_sequences=False),
                layers.Dropout(0.2),
                layers.Dense(25),
                layers.Dense(1)
            ])
            
            self.models['lstm'].compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model
            history = self.models['lstm'].fit(
                X_train, y_train,
                batch_size=32,
                epochs=50,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # Evaluate
            y_pred = self.models['lstm'].predict(X_test)
            
            # Inverse transform for evaluation
            y_test_inv = self.scalers['target'].inverse_transform(y_test.reshape(-1, 1))
            y_pred_inv = self.scalers['target'].inverse_transform(y_pred)
            
            mse = mean_squared_error(y_test_inv, y_pred_inv)
            r2 = r2_score(y_test_inv, y_pred_inv)
            
            logging.info(f"LSTM - MSE: {mse:.4f}, R²: {r2:.4f}")
            
            # Save model
            self.models['lstm'].save('models/lstm.h5')
            joblib.dump(self.scalers['target'], 'models/target_scaler.joblib')
            
            return True
            
        except Exception as e:
            logging.error(f"Error training LSTM: {str(e)}")
            return False
    
    def predict_random_forest(self, data):
        """Make prediction using Random Forest"""
        try:
            if self.models['random_forest'] is None:
                # Try to load saved model
                if os.path.exists('models/random_forest.joblib'):
                    self.models['random_forest'] = joblib.load('models/random_forest.joblib')
                    self.scalers['features'] = joblib.load('models/feature_scaler.joblib')
                else:
                    # Train model if not available
                    self.train_random_forest(data)
            
            # Prepare features
            features, _ = self.prepare_features(data)
            if features is None:
                return {'error': 'Failed to prepare features'}
            
            # Get last row for prediction
            last_features = features.iloc[-1:].fillna(0)
            last_features_scaled = self.scalers['features'].transform(last_features)
            
            # Make prediction
            prediction = self.models['random_forest'].predict(last_features_scaled)[0]
            
            # Calculate confidence based on feature importance
            feature_importance = self.models['random_forest'].feature_importances_
            confidence = np.mean(feature_importance) * 0.8  # Simplified confidence
            
            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'model': 'Random Forest'
            }
            
        except Exception as e:
            logging.error(f"Error in Random Forest prediction: {str(e)}")
            return {'error': 'Random Forest prediction failed'}
    
    def predict_xgboost(self, data):
        """Make prediction using XGBoost"""
        try:
            if self.models['xgboost'] is None:
                # Try to load saved model
                if os.path.exists('models/xgboost.model'):
                    self.models['xgboost'] = xgb.Booster()
                    self.models['xgboost'].load_model('models/xgboost.model')
                else:
                    # Train model if not available
                    self.train_xgboost(data)
            
            # Prepare features
            features, _ = self.prepare_features(data)
            if features is None:
                return {'error': 'Failed to prepare features'}
            
            # Get last row for prediction
            last_features = features.iloc[-1:].fillna(0)
            dtest = xgb.DMatrix(last_features)
            
            # Make prediction
            prediction = self.models['xgboost'].predict(dtest)[0]
            
            # Calculate confidence based on model performance (simplified)
            confidence = 0.75  # Can be improved with proper uncertainty estimation
            
            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'model': 'XGBoost'
            }
            
        except Exception as e:
            logging.error(f"Error in XGBoost prediction: {str(e)}")
            return {'error': 'XGBoost prediction failed'}
    
    def predict_lstm(self, data, sequence_length=60):
        """Make prediction using LSTM"""
        try:
            # Load TensorFlow if not already loaded
            if not TENSORFLOW_AVAILABLE:
                success = _load_tensorflow()
                if not success:
                    return {'error': 'LSTM prediction unavailable - TensorFlow compatibility issue'}
            
            if self.models['lstm'] is None:
                # Try to load saved model
                if os.path.exists('models/lstm.h5'):
                    self.models['lstm'] = keras.models.load_model('models/lstm.h5')
                    self.scalers['target'] = joblib.load('models/target_scaler.joblib')
                else:
                    # Train model if not available
                    success = self.train_lstm(data)
                    if not success:
                        return {'error': 'Failed to train LSTM model'}
            
            # Prepare data
            close_prices = data['Close'].values.reshape(-1, 1)
            
            # Ensure scaler is fitted
            if 'target' not in self.scalers or self.scalers['target'] is None:
                self.scalers['target'] = MinMaxScaler()
                self.scalers['target'].fit(close_prices)
            
            scaled_data = self.scalers['target'].transform(close_prices)
            
            # Get last sequence for prediction
            if len(scaled_data) < sequence_length:
                sequence_length = min(len(scaled_data), 30)  # Use shorter sequence if needed
            
            last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
            
            # Make prediction
            prediction_scaled = self.models['lstm'].predict(last_sequence, verbose=0)
            prediction = self.scalers['target'].inverse_transform(prediction_scaled)[0][0]
            
            # Calculate confidence based on recent volatility
            recent_prices = data['Close'].tail(10).values
            volatility = np.std(recent_prices) / np.mean(recent_prices)
            confidence = max(0.1, 0.9 - volatility)  # Higher volatility = lower confidence
            
            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'model': 'LSTM Neural Network'
            }
            
        except Exception as e:
            logging.error(f"Error in LSTM prediction: {str(e)}")
            return {'error': f'LSTM prediction failed: {str(e)}'}
        
        try:
            if self.models['lstm'] is None:
                # Try to load saved model
                if os.path.exists('models/lstm.h5') and keras is not None:
                    self.models['lstm'] = keras.models.load_model('models/lstm.h5')
                    self.scalers['target'] = joblib.load('models/target_scaler.joblib')
                else:
                    # Train model if not available
                    self.train_lstm(data)
            
            # Prepare data
            close_prices = data['Close'].values.reshape(-1, 1)
            scaled_data = self.scalers['target'].transform(close_prices)
            
            # Get last sequence
            if len(scaled_data) < sequence_length:
                return {'error': 'Insufficient data for LSTM prediction'}
            
            last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
            
            # Make prediction
            scaled_prediction = self.models['lstm'].predict(last_sequence)[0][0]
            prediction = self.scalers['target'].inverse_transform([[scaled_prediction]])[0][0]
            
            # Calculate confidence (simplified)
            confidence = 0.7
            
            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'model': 'LSTM'
            }
            
        except Exception as e:
            logging.warning(f"LSTM prediction failed (expected due to TF compatibility): {str(e)}")
            return {'error': 'LSTM prediction failed'}
    
    def get_trading_signals(self, data):
        """Generate trading signals from multiple strategies"""
        try:
            signals = {}
            
            # RSI Strategy
            rsi = data['RSI'].iloc[-1]
            if rsi < 30:
                rsi_signal = 'BUY'
                rsi_confidence = (30 - rsi) / 30
            elif rsi > 70:
                rsi_signal = 'SELL'
                rsi_confidence = (rsi - 70) / 30
            else:
                rsi_signal = 'HOLD'
                rsi_confidence = 0.5
            
            signals['RSI'] = {'signal': rsi_signal, 'confidence': rsi_confidence}
            
            # MACD Strategy
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_Signal'].iloc[-1]
            
            if macd > macd_signal and data['MACD'].iloc[-2] <= data['MACD_Signal'].iloc[-2]:
                signals['MACD'] = {'signal': 'BUY', 'confidence': 0.8}
            elif macd < macd_signal and data['MACD'].iloc[-2] >= data['MACD_Signal'].iloc[-2]:
                signals['MACD'] = {'signal': 'SELL', 'confidence': 0.8}
            else:
                signals['MACD'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Moving Average Strategy
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                signals['MA'] = {'signal': 'BUY', 'confidence': 0.7}
            elif current_price < sma_20 < sma_50:
                signals['MA'] = {'signal': 'SELL', 'confidence': 0.7}
            else:
                signals['MA'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Bollinger Bands Strategy
            bb_upper = data['BB_Upper'].iloc[-1]
            bb_lower = data['BB_Lower'].iloc[-1]
            
            if current_price <= bb_lower:
                signals['BB'] = {'signal': 'BUY', 'confidence': 0.75}
            elif current_price >= bb_upper:
                signals['BB'] = {'signal': 'SELL', 'confidence': 0.75}
            else:
                signals['BB'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Stochastic Strategy
            stoch_k = data['Stoch_K'].iloc[-1]
            stoch_d = data['Stoch_D'].iloc[-1]
            
            if stoch_k < 20 and stoch_k > stoch_d:
                signals['STOCH'] = {'signal': 'BUY', 'confidence': 0.6}
            elif stoch_k > 80 and stoch_k < stoch_d:
                signals['STOCH'] = {'signal': 'SELL', 'confidence': 0.6}
            else:
                signals['STOCH'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Williams %R Strategy
            williams_r = data['Williams_R'].iloc[-1]
            
            if williams_r < -80:
                signals['WILLIAMS'] = {'signal': 'BUY', 'confidence': 0.65}
            elif williams_r > -20:
                signals['WILLIAMS'] = {'signal': 'SELL', 'confidence': 0.65}
            else:
                signals['WILLIAMS'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Volume Strategy
            volume_ratio = data['Volume_Ratio'].iloc[-1]
            price_change = data['Price_Change'].iloc[-1]
            
            if volume_ratio > 1.5 and price_change > 0:
                signals['VOLUME'] = {'signal': 'BUY', 'confidence': 0.6}
            elif volume_ratio > 1.5 and price_change < 0:
                signals['VOLUME'] = {'signal': 'SELL', 'confidence': 0.6}
            else:
                signals['VOLUME'] = {'signal': 'HOLD', 'confidence': 0.5}
            
            # Calculate overall signal
            buy_votes = sum(1 for s in signals.values() if s['signal'] == 'BUY')
            sell_votes = sum(1 for s in signals.values() if s['signal'] == 'SELL')
            total_confidence = sum(s['confidence'] for s in signals.values() if s['signal'] != 'HOLD')
            
            if buy_votes > sell_votes:
                overall_signal = 'BUY'
                overall_confidence = total_confidence / len(signals) if buy_votes > 0 else 0.5
            elif sell_votes > buy_votes:
                overall_signal = 'SELL'
                overall_confidence = total_confidence / len(signals) if sell_votes > 0 else 0.5
            else:
                overall_signal = 'HOLD'
                overall_confidence = 0.5
            
            return {
                'individual_signals': signals,
                'overall_signal': overall_signal,
                'overall_confidence': overall_confidence,
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'hold_votes': len(signals) - buy_votes - sell_votes
            }
            
        except Exception as e:
            logging.error(f"Error generating trading signals: {str(e)}")
            return {'error': 'Failed to generate trading signals'}
