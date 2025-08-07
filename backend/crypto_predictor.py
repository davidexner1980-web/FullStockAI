import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
from backend.data_fetcher import DataFetcher
import logging

# Conditional TensorFlow imports - won't crash app if TensorFlow has issues
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
    logging.info("TensorFlow loaded successfully for crypto predictions")
except Exception as e:
    logging.warning(f"TensorFlow not available for LSTM models: {str(e)}")
    Sequential = None
    LSTM = Dense = Dropout = None
    TENSORFLOW_AVAILABLE = False

class CryptoPredictorEngine:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.crypto_features = [
            'Open', 'High', 'Low', 'Volume', 'MA_7', 'MA_21', 'RSI', 'MACD', 'BB_upper', 'BB_lower', 'Volatility'
        ]
        
    def prepare_crypto_features(self, df):
        """Prepare technical indicators specific to crypto"""
        try:
            # Moving averages (shorter periods for crypto)
            df['MA_7'] = df['Close'].rolling(window=7).mean()
            df['MA_21'] = df['Close'].rolling(window=21).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            
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
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            df['BB_middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std_dev = df['Close'].rolling(window=bb_period).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std_dev * bb_std)
            df['BB_lower'] = df['BB_middle'] - (bb_std_dev * bb_std)
            
            # Volatility (crypto-specific)
            df['Volatility'] = df['Close'].rolling(window=7).std()
            df['High_Low_Ratio'] = df['High'] / df['Low']
            
            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=7).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
            
            # Price momentum
            df['Price_Momentum_3'] = df['Close'].pct_change(periods=3)
            df['Price_Momentum_7'] = df['Close'].pct_change(periods=7)
            
            # Support and Resistance levels
            df['Support'] = df['Low'].rolling(window=14).min()
            df['Resistance'] = df['High'].rolling(window=14).max()
            
            return df.dropna()
        except Exception as e:
            logging.error(f"Crypto feature preparation error: {str(e)}")
            raise

    def predict(self, ticker):
        """Random Forest prediction for crypto"""
        try:
            # Ensure crypto ticker format
            if not ticker.endswith('-USD'):
                ticker = f"{ticker}-USD"
            
            # Get crypto data
            df = self.data_fetcher.get_crypto_data(ticker, period='1y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare features
            df = self.prepare_crypto_features(df)
            
            # Extended feature set for crypto
            extended_features = self.crypto_features + [
                'Volume_Ratio', 'Price_Momentum_3', 'Price_Momentum_7', 'High_Low_Ratio'
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
            
            # Train model with crypto-specific parameters
            model = RandomForestRegressor(
                n_estimators=150,
                max_depth=12,
                min_samples_split=3,
                random_state=42
            )
            model.fit(features, target)
            
            # Make prediction
            last_features = features.iloc[-1:].values
            predicted_price = model.predict(last_features)[0]
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Crypto-specific confidence calculation
            recent_volatility = df['Volatility'].iloc[-7:].mean()
            volume_stability = df['Volume_Ratio'].iloc[-7:].std()
            confidence = min(90, max(50, 75 - (recent_volatility * 10) - (volume_stability * 20)))
            
            return {
                'predicted_price': round(predicted_price, 6),
                'current_price': round(current_price, 6),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence, 1),
                'model_type': 'Crypto Random Forest',
                'volatility_7d': round(recent_volatility, 6),
                'volume_stability': round(volume_stability, 2)
            }
        except Exception as e:
            logging.error(f"Crypto Random Forest prediction error for {ticker}: {str(e)}")
            raise

    def predict_lstm(self, ticker):
        """LSTM prediction for crypto (with TensorFlow fallback)"""
        try:
            # Check if TensorFlow is available
            if not TENSORFLOW_AVAILABLE:
                logging.warning("TensorFlow not available, falling back to advanced time series prediction")
                return self._lstm_fallback_prediction(ticker)
            
            # Ensure crypto ticker format
            if not ticker.endswith('-USD'):
                ticker = f"{ticker}-USD"
            
            # Get crypto data (more data for LSTM)
            df = self.data_fetcher.get_crypto_data(ticker, period='2y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare data for LSTM
            data = df['Close'].values.reshape(-1, 1)
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)
            
            # Create sequences (shorter for crypto due to higher volatility)
            sequence_length = 30
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i, 0])
                y.append(scaled_data[i, 0])
            
            X, y = np.array(X), np.array(y)
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            if len(X) < 10:
                raise ValueError(f"Insufficient data for LSTM training for {ticker}")
            
            # Build crypto-specific LSTM model
            model = Sequential([
                LSTM(100, return_sequences=True, input_shape=(sequence_length, 1)),
                Dropout(0.3),
                LSTM(100, return_sequences=True),
                Dropout(0.3),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
            
            # Train model
            model.fit(X, y, batch_size=16, epochs=15, verbose=0, validation_split=0.1)
            
            # Make prediction
            last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
            prediction_scaled = model.predict(last_sequence, verbose=0)
            predicted_price = scaler.inverse_transform(prediction_scaled)[0][0]
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Crypto-specific confidence calculation
            recent_returns = df['Close'].pct_change().dropna()
            volatility = recent_returns.rolling(window=14).std().iloc[-1]
            confidence = min(85, max(55, 70 - (volatility * 300)))
            
            return {
                'predicted_price': round(predicted_price, 6),
                'current_price': round(current_price, 6),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence, 1),
                'model_type': 'Crypto LSTM'
            }
        except Exception as e:
            logging.error(f"Crypto LSTM prediction error for {ticker}: {str(e)}")
            # Try fallback method if TensorFlow LSTM fails
            logging.info("Attempting LSTM fallback prediction...")
            return self._lstm_fallback_prediction(ticker)
    
    def _lstm_fallback_prediction(self, ticker):
        """Fallback prediction when TensorFlow LSTM is not available"""
        try:
            # Ensure crypto ticker format
            if not ticker.endswith('-USD'):
                ticker = f"{ticker}-USD"
            
            # Get crypto data
            df = self.data_fetcher.get_crypto_data(ticker, period='6m')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare features for advanced time series analysis
            df = self.prepare_crypto_features(df)
            
            # Use weighted moving averages to simulate LSTM-like behavior
            weights = np.array([0.1, 0.2, 0.3, 0.4])  # More weight on recent data
            prices = df['Close'].values
            
            # Calculate weighted prediction based on recent trends and patterns
            if len(prices) < 10:
                raise ValueError("Insufficient data for fallback prediction")
            
            # Trend analysis
            recent_4 = prices[-4:]
            weighted_avg = np.average(recent_4, weights=weights)
            
            # Momentum calculation
            momentum_5 = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
            momentum_10 = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            
            # Combine weighted average with momentum
            momentum_factor = (momentum_5 * 0.7 + momentum_10 * 0.3) * 0.1
            predicted_price = weighted_avg * (1 + momentum_factor)
            
            current_price = prices[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # Calculate confidence based on recent stability
            recent_volatility = df['Volatility'].iloc[-7:].mean()
            confidence = min(75, max(50, 65 - (recent_volatility * 10)))
            
            return {
                'predicted_price': round(predicted_price, 6),
                'current_price': round(current_price, 6),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence, 1),
                'model_type': 'Advanced Time Series (LSTM Fallback)'
            }
        except Exception as e:
            logging.error(f"LSTM fallback prediction error for {ticker}: {str(e)}")
            raise

    def predict_xgboost(self, ticker):
        """XGBoost prediction for crypto"""
        try:
            # Ensure crypto ticker format
            if not ticker.endswith('-USD'):
                ticker = f"{ticker}-USD"
            
            # Get crypto data
            df = self.data_fetcher.get_crypto_data(ticker, period='1y')
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Prepare features
            df = self.prepare_crypto_features(df)
            
            # Full feature set for XGBoost
            full_features = self.crypto_features + [
                'Volume_Ratio', 'Price_Momentum_3', 'Price_Momentum_7', 
                'High_Low_Ratio', 'MACD_signal', 'Support', 'Resistance'
            ]
            
            # Prepare training data
            features = df[full_features].fillna(method='ffill').dropna()
            target = df['Close'].shift(-1).dropna()
            
            # Align features and target
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]
            
            if len(features) < 30:
                raise ValueError(f"Insufficient data for {ticker}")
            
            # Train XGBoost model with crypto-specific parameters
            model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
            model.fit(features, target)
            
            # Make prediction
            last_features = features.iloc[-1:].values
            predicted_price = model.predict(last_features)[0]
            
            current_price = df['Close'].iloc[-1]
            price_change = ((predicted_price - current_price) / current_price) * 100
            
            # XGBoost-specific confidence for crypto
            feature_importance = model.feature_importances_
            top_feature_weight = max(feature_importance)
            confidence_score = min(88, max(60, 80 - (abs(price_change) * 1.5) + (top_feature_weight * 30)))
            
            return {
                'predicted_price': round(predicted_price, 6),
                'current_price': round(current_price, 6),
                'price_change_percent': round(price_change, 2),
                'confidence': round(confidence_score, 1),
                'model_type': 'Crypto XGBoost',
                'top_feature_importance': round(top_feature_weight, 3)
            }
        except Exception as e:
            logging.error(f"Crypto XGBoost prediction error for {ticker}: {str(e)}")
            raise

    def get_trending_crypto(self):
        """Get trending cryptocurrencies with basic metrics"""
        try:
            # Popular crypto tickers
            crypto_list = [
                'BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 
                'XRP-USD', 'DOT-USD', 'DOGE-USD', 'MATIC-USD', 'AVAX-USD'
            ]
            
            trending = []
            for ticker in crypto_list:
                try:
                    df = self.data_fetcher.get_crypto_data(ticker, period='7d')
                    if not df.empty:
                        current = df['Close'].iloc[-1]
                        day_ago = df['Close'].iloc[-2] if len(df) > 1 else current
                        week_ago = df['Close'].iloc[0]
                        
                        change_24h = ((current - day_ago) / day_ago) * 100 if day_ago > 0 else 0
                        change_7d = ((current - week_ago) / week_ago) * 100 if week_ago > 0 else 0
                        
                        volume_24h = df['Volume'].iloc[-1] if not df['Volume'].empty else 0
                        
                        trending.append({
                            'symbol': ticker.replace('-USD', ''),
                            'name': self.get_crypto_name(ticker),
                            'price': round(current, 6),
                            'change_24h': round(change_24h, 2),
                            'change_7d': round(change_7d, 2),
                            'volume_24h': int(volume_24h),
                            'market_cap_rank': self.get_market_cap_rank(ticker)
                        })
                except Exception as e:
                    logging.error(f"Error processing {ticker}: {str(e)}")
                    continue
            
            # Sort by 24h volume
            trending.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            return trending[:8]  # Return top 8
        except Exception as e:
            logging.error(f"Error getting trending crypto: {str(e)}")
            return []

    def get_crypto_name(self, ticker):
        """Get crypto full name"""
        names = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'BNB-USD': 'Binance Coin',
            'ADA-USD': 'Cardano',
            'SOL-USD': 'Solana',
            'XRP-USD': 'XRP',
            'DOT-USD': 'Polkadot',
            'DOGE-USD': 'Dogecoin',
            'MATIC-USD': 'Polygon',
            'AVAX-USD': 'Avalanche'
        }
        return names.get(ticker, ticker.replace('-USD', ''))

    def get_market_cap_rank(self, ticker):
        """Get approximate market cap rank"""
        ranks = {
            'BTC-USD': 1,
            'ETH-USD': 2,
            'BNB-USD': 3,
            'ADA-USD': 8,
            'SOL-USD': 5,
            'XRP-USD': 6,
            'DOT-USD': 12,
            'DOGE-USD': 9,
            'MATIC-USD': 15,
            'AVAX-USD': 18
        }
        return ranks.get(ticker, 50)

    def get_fear_greed_index(self):
        """Get Fear & Greed Index for crypto market"""
        try:
            return self.data_fetcher.get_crypto_fear_greed()
        except Exception as e:
            logging.error(f"Error getting fear & greed index: {str(e)}")
            return {
                'value': 50,
                'classification': 'Neutral',
                'timestamp': int(time.time())
            }

    def analyze_crypto_correlations(self, tickers):
        """Analyze correlations between cryptocurrencies"""
        try:
            correlations = {}
            price_data = {}
            
            # Get price data for all tickers
            for ticker in tickers:
                if not ticker.endswith('-USD'):
                    ticker = f"{ticker}-USD"
                
                df = self.data_fetcher.get_crypto_data(ticker, period='30d')
                if not df.empty:
                    price_data[ticker] = df['Close'].pct_change().dropna()
            
            # Calculate correlations
            for i, ticker1 in enumerate(price_data.keys()):
                correlations[ticker1] = {}
                for ticker2 in price_data.keys():
                    if ticker1 != ticker2:
                        corr = price_data[ticker1].corr(price_data[ticker2])
                        correlations[ticker1][ticker2] = round(corr, 3) if not np.isnan(corr) else 0
            
            return correlations
        except Exception as e:
            logging.error(f"Error analyzing crypto correlations: {str(e)}")
            return {}

    def get_crypto_market_summary(self):
        """Get overall crypto market summary"""
        try:
            # Major cryptos for market summary
            major_cryptos = ['BTC-USD', 'ETH-USD', 'BNB-USD']
            
            total_market_cap = 0
            total_volume_24h = 0
            avg_change_24h = 0
            
            for ticker in major_cryptos:
                df = self.data_fetcher.get_crypto_data(ticker, period='2d')
                if not df.empty:
                    current = df['Close'].iloc[-1]
                    prev = df['Close'].iloc[-2] if len(df) > 1 else current
                    volume = df['Volume'].iloc[-1]
                    
                    # Estimate market cap (simplified)
                    estimated_supply = {
                        'BTC-USD': 19_700_000,
                        'ETH-USD': 120_000_000,
                        'BNB-USD': 200_000_000
                    }
                    
                    market_cap = current * estimated_supply.get(ticker, 100_000_000)
                    change_24h = ((current - prev) / prev) * 100 if prev > 0 else 0
                    
                    total_market_cap += market_cap
                    total_volume_24h += volume * current
                    avg_change_24h += change_24h
            
            avg_change_24h = avg_change_24h / len(major_cryptos) if major_cryptos else 0
            
            # Get fear & greed index
            fear_greed = self.get_fear_greed_index()
            
            return {
                'total_market_cap': round(total_market_cap / 1e12, 2),  # In trillions
                'total_volume_24h': round(total_volume_24h / 1e9, 2),   # In billions
                'market_change_24h': round(avg_change_24h, 2),
                'fear_greed_index': fear_greed,
                'dominant_trend': 'bullish' if avg_change_24h > 2 else 'bearish' if avg_change_24h < -2 else 'sideways'
            }
        except Exception as e:
            logging.error(f"Error getting crypto market summary: {str(e)}")
            return {
                'total_market_cap': 0,
                'total_volume_24h': 0,
                'market_change_24h': 0,
                'fear_greed_index': {'value': 50, 'classification': 'Neutral'},
                'dominant_trend': 'sideways'
            }
