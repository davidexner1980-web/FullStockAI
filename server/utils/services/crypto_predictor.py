import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

class CryptoPredictor:
    def __init__(self):
        self.models_dir = 'models/crypto'
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Top cryptocurrencies to track
        self.top_cryptos = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum', 
            'BNB-USD': 'Binance Coin',
            'XRP-USD': 'XRP',
            'ADA-USD': 'Cardano',
            'DOGE-USD': 'Dogecoin',
            'MATIC-USD': 'Polygon',
            'SOL-USD': 'Solana',
            'DOT-USD': 'Polkadot',
            'AVAX-USD': 'Avalanche'
        }
        
        self.model_params = {
            'n_estimators': 100,
            'max_depth': 12,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'random_state': 42
        }
    
    def predict(self, symbol: str) -> Dict[str, Any]:
        """Predict cryptocurrency price"""
        try:
            # Ensure proper crypto ticker format
            if not symbol.endswith('-USD'):
                crypto_ticker = f"{symbol}-USD"
            else:
                crypto_ticker = symbol
            
            # Get historical data
            data = self._get_crypto_data(crypto_ticker)
            if data is None or len(data) < 50:
                return {'error': f'Insufficient data for {symbol}'}
            
            # Prepare features
            features = self._prepare_crypto_features(data)
            if features is None:
                return {'error': 'Could not prepare features'}
            
            # Get or train model
            model = self._get_or_train_model(crypto_ticker, data, features)
            
            # Make prediction
            latest_features = features.iloc[-1:].values
            prediction = model.predict(latest_features)[0]
            
            current_price = data['Close'].iloc[-1]
            price_change = prediction - current_price
            change_percent = (price_change / current_price) * 100
            
            # Calculate volatility
            volatility = data['Close'].pct_change().rolling(30).std().iloc[-1] * np.sqrt(365) * 100
            
            # Calculate confidence based on volatility
            confidence = max(0.3, min(0.9, 1 - (volatility / 200)))
            
            return {
                'symbol': symbol,
                'crypto_ticker': crypto_ticker,
                'name': self.top_cryptos.get(crypto_ticker, symbol),
                'current_price': round(current_price, 8),
                'predicted_price': round(prediction, 8),
                'price_change': round(price_change, 8),
                'change_percent': round(change_percent, 2),
                'confidence': round(confidence * 100, 1),
                'volatility': round(volatility, 2),
                'volume_24h': int(data['Volume'].iloc[-1]),
                'prediction_date': datetime.now().isoformat(),
                'target_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'signal': 'BUY' if price_change > 0 else 'SELL',
                'market_cap_rank': self._get_market_cap_rank(crypto_ticker),
                'analysis': self._analyze_crypto_trends(data)
            }
            
        except Exception as e:
            logging.error(f"Crypto prediction error for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _get_crypto_data(self, ticker: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """Fetch cryptocurrency data"""
        try:
            crypto = yf.Ticker(ticker)
            data = crypto.history(period=period)
            
            if data.empty:
                logging.warning(f"No crypto data found for {ticker}")
                return None
                
            return data.dropna()
            
        except Exception as e:
            logging.error(f"Error fetching crypto data for {ticker}: {str(e)}")
            return None
    
    def _prepare_crypto_features(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare crypto-specific features"""
        try:
            features = pd.DataFrame(index=data.index)
            
            # Price features
            features['close'] = data['Close']
            features['high'] = data['High']
            features['low'] = data['Low']
            features['volume'] = data['Volume']
            
            # Returns and volatility
            features['returns'] = data['Close'].pct_change()
            features['volatility_7'] = features['returns'].rolling(7).std()
            features['volatility_30'] = features['returns'].rolling(30).std()
            
            # Moving averages
            for window in [7, 14, 30, 50]:
                features[f'sma_{window}'] = data['Close'].rolling(window).mean()
                features[f'price_to_sma_{window}'] = data['Close'] / features[f'sma_{window}']
            
            # Price momentum (crypto markets move faster)
            for period in [3, 7, 14]:
                features[f'momentum_{period}'] = data['Close'] / data['Close'].shift(period) - 1
            
            # Volume analysis (very important for crypto)
            features['volume_sma_14'] = data['Volume'].rolling(14).mean()
            features['volume_ratio'] = data['Volume'] / features['volume_sma_14']
            features['volume_price_trend'] = features['volume_ratio'] * features['returns']
            
            # Crypto-specific indicators
            
            # High-low volatility
            features['hl_volatility'] = (data['High'] - data['Low']) / data['Close']
            
            # RSI (more sensitive for crypto)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            sma_20 = data['Close'].rolling(20).mean()
            std_20 = data['Close'].rolling(20).std()
            features['bb_upper'] = sma_20 + (std_20 * 2)
            features['bb_lower'] = sma_20 - (std_20 * 2)
            features['bb_position'] = (data['Close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            features['bb_squeeze'] = (features['bb_upper'] - features['bb_lower']) / sma_20
            
            # MACD
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            features['macd'] = ema_12 - ema_26
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_histogram'] = features['macd'] - features['macd_signal']
            
            # Support and resistance levels
            features['support_level'] = data['Low'].rolling(20).min()
            features['resistance_level'] = data['High'].rolling(20).max()
            features['support_distance'] = (data['Close'] - features['support_level']) / data['Close']
            features['resistance_distance'] = (features['resistance_level'] - data['Close']) / data['Close']
            
            # Time-based features (crypto markets are 24/7)
            features['hour'] = data.index.hour
            features['day_of_week'] = data.index.dayofweek
            features['weekend'] = (data.index.dayofweek >= 5).astype(int)
            
            # Remove NaN values
            features = features.dropna()
            
            return features
            
        except Exception as e:
            logging.error(f"Crypto feature preparation error: {str(e)}")
            return None
    
    def _get_or_train_model(self, ticker: str, data: pd.DataFrame, features: pd.DataFrame):
        """Get existing crypto model or train a new one"""
        model_path = os.path.join(self.models_dir, f'crypto_{ticker.replace("-", "_")}.joblib')
        
        try:
            # Check if model exists and is recent (crypto models need frequent updates)
            if os.path.exists(model_path):
                model_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(model_path))
                if model_age.days < 3:  # Update every 3 days for crypto
                    return joblib.load(model_path)
            
            # Train new model
            model = self._train_crypto_model(ticker, data, features)
            joblib.dump(model, model_path)
            return model
            
        except Exception as e:
            logging.error(f"Crypto model error for {ticker}: {str(e)}")
            return self._train_crypto_model(ticker, data, features)
    
    def _train_crypto_model(self, ticker: str, data: pd.DataFrame, features: pd.DataFrame):
        """Train crypto-specific model"""
        try:
            # Prepare target
            target = data['Close'].shift(-1).dropna()
            features_aligned = features.iloc[:-1]
            features_aligned = features_aligned.loc[target.index]
            
            # Use more recent data for training (crypto markets change faster)
            if len(features_aligned) > 200:
                features_aligned = features_aligned.iloc[-200:]
                target = target.iloc[-200:]
            
            # Train model
            model = RandomForestRegressor(**self.model_params)
            model.fit(features_aligned, target)
            
            logging.info(f"Trained crypto model for {ticker}")
            return model
            
        except Exception as e:
            logging.error(f"Crypto model training error for {ticker}: {str(e)}")
            raise
    
    def _analyze_crypto_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze crypto-specific trends"""
        try:
            current_price = data['Close'].iloc[-1]
            
            # Price changes over different periods
            price_1d = data['Close'].iloc[-2] if len(data) > 1 else current_price
            price_7d = data['Close'].iloc[-8] if len(data) > 7 else current_price
            price_30d = data['Close'].iloc[-31] if len(data) > 30 else current_price
            
            change_1d = ((current_price - price_1d) / price_1d * 100) if price_1d != 0 else 0
            change_7d = ((current_price - price_7d) / price_7d * 100) if price_7d != 0 else 0
            change_30d = ((current_price - price_30d) / price_30d * 100) if price_30d != 0 else 0
            
            # Volume trend
            avg_volume_7d = data['Volume'].tail(7).mean()
            current_volume = data['Volume'].iloc[-1]
            volume_trend = "High" if current_volume > avg_volume_7d * 1.5 else "Normal"
            
            # Volatility assessment
            volatility_7d = data['Close'].pct_change().tail(7).std() * np.sqrt(7) * 100
            
            if volatility_7d > 15:
                volatility_assessment = "Very High"
            elif volatility_7d > 10:
                volatility_assessment = "High"
            elif volatility_7d > 5:
                volatility_assessment = "Medium"
            else:
                volatility_assessment = "Low"
            
            return {
                'change_24h': round(change_1d, 2),
                'change_7d': round(change_7d, 2),
                'change_30d': round(change_30d, 2),
                'volume_trend': volume_trend,
                'volatility_7d': round(volatility_7d, 2),
                'volatility_assessment': volatility_assessment,
                'all_time_high': round(data['High'].max(), 8),
                'all_time_low': round(data['Low'].min(), 8),
                'current_vs_ath': round(((current_price - data['High'].max()) / data['High'].max() * 100), 2)
            }
            
        except Exception as e:
            logging.error(f"Crypto trend analysis error: {str(e)}")
            return {}
    
    def _get_market_cap_rank(self, ticker: str) -> int:
        """Get approximate market cap rank"""
        rank_map = {
            'BTC-USD': 1, 'ETH-USD': 2, 'BNB-USD': 3, 'XRP-USD': 4, 'ADA-USD': 5,
            'DOGE-USD': 6, 'MATIC-USD': 7, 'SOL-USD': 8, 'DOT-USD': 9, 'AVAX-USD': 10
        }
        return rank_map.get(ticker, 999)
    
    def get_top_cryptocurrencies(self) -> Dict[str, Any]:
        """Get data for top cryptocurrencies"""
        try:
            crypto_data = {}
            
            for ticker, name in list(self.top_cryptos.items())[:5]:  # Top 5 to avoid rate limits
                try:
                    data = self._get_crypto_data(ticker, period='7d')
                    if data is not None and not data.empty:
                        current_price = data['Close'].iloc[-1]
                        prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
                        change_24h = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0
                        
                        crypto_data[ticker] = {
                            'name': name,
                            'symbol': ticker.replace('-USD', ''),
                            'price': round(current_price, 8),
                            'change_24h': round(change_24h, 2),
                            'volume_24h': int(data['Volume'].iloc[-1]),
                            'market_cap_rank': self._get_market_cap_rank(ticker)
                        }
                        
                except Exception as e:
                    logging.error(f"Error getting data for {ticker}: {str(e)}")
                    continue
            
            return {
                'cryptocurrencies': crypto_data,
                'total_tracked': len(crypto_data),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Top cryptocurrencies error: {str(e)}")
            return {'error': str(e)}
    
    def compare_crypto_predictions(self, symbols: List[str]) -> Dict[str, Any]:
        """Compare predictions for multiple cryptocurrencies"""
        try:
            predictions = {}
            
            for symbol in symbols:
                pred = self.predict(symbol)
                if 'error' not in pred:
                    predictions[symbol] = pred
            
            if not predictions:
                return {'error': 'No successful predictions'}
            
            # Find best opportunities
            best_gainers = sorted(
                predictions.items(), 
                key=lambda x: x[1]['change_percent'], 
                reverse=True
            )[:3]
            
            highest_confidence = sorted(
                predictions.items(),
                key=lambda x: x[1]['confidence'],
                reverse=True
            )[:3]
            
            return {
                'predictions': predictions,
                'analysis': {
                    'total_analyzed': len(predictions),
                    'average_predicted_change': round(
                        sum(p['change_percent'] for p in predictions.values()) / len(predictions), 2
                    ),
                    'best_opportunities': [{'symbol': k, 'change_percent': v['change_percent']} 
                                         for k, v in best_gainers],
                    'highest_confidence': [{'symbol': k, 'confidence': v['confidence']} 
                                         for k, v in highest_confidence]
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Crypto comparison error: {str(e)}")
            return {'error': str(e)}
