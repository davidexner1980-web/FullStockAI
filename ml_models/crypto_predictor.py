import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import requests
import logging
from datetime import datetime, timedelta

class CryptoPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.crypto_symbols = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD', 
            'BNB': 'BNB-USD',
            'ADA': 'ADA-USD',
            'SOL': 'SOL-USD',
            'DOT': 'DOT-USD',
            'AVAX': 'AVAX-USD',
            'LINK': 'LINK-USD',
            'MATIC': 'MATIC-USD',
            'UNI': 'UNI-USD'
        }
        
    def get_crypto_data(self, symbol, period='1y'):
        """Fetch cryptocurrency data from Yahoo Finance"""
        try:
            # Ensure symbol has -USD suffix for crypto
            if symbol in self.crypto_symbols:
                symbol = self.crypto_symbols[symbol]
            elif not symbol.endswith('-USD'):
                symbol += '-USD'
                
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
                
            return data
            
        except Exception as e:
            logging.error(f"Error fetching crypto data for {symbol}: {str(e)}")
            raise

    def prepare_crypto_features(self, data):
        """Prepare crypto-specific features"""
        try:
            # Basic price features
            data['returns'] = data['Close'].pct_change()
            data['log_returns'] = np.log(data['Close'] / data['Close'].shift(1))
            
            # Moving averages
            data['sma_7'] = data['Close'].rolling(window=7).mean()
            data['sma_14'] = data['Close'].rolling(window=14).mean()
            data['sma_30'] = data['Close'].rolling(window=30).mean()
            
            # Exponential moving averages
            data['ema_12'] = data['Close'].ewm(span=12).mean()
            data['ema_26'] = data['Close'].ewm(span=26).mean()
            
            # MACD for crypto
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            
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
            
            # Volatility features (important for crypto)
            data['volatility_7'] = data['returns'].rolling(window=7).std()
            data['volatility_14'] = data['returns'].rolling(window=14).std()
            data['volatility_30'] = data['returns'].rolling(window=30).std()
            
            # Volume features
            data['volume_sma'] = data['Volume'].rolling(window=14).mean()
            data['volume_ratio'] = data['Volume'] / data['volume_sma']
            
            # Price momentum
            data['momentum_3'] = data['Close'] / data['Close'].shift(3) - 1
            data['momentum_7'] = data['Close'] / data['Close'].shift(7) - 1
            data['momentum_14'] = data['Close'] / data['Close'].shift(14) - 1
            
            # High-Low spread (important for crypto volatility)
            data['hl_ratio'] = (data['High'] - data['Low']) / data['Close']
            data['close_position'] = (data['Close'] - data['Low']) / (data['High'] - data['Low'])
            
            # Target variable (next day return)
            data['target'] = data['Close'].shift(-1) / data['Close'] - 1
            
            # Feature columns
            feature_columns = [
                'sma_7', 'sma_14', 'sma_30', 'ema_12', 'ema_26', 'macd', 'macd_signal',
                'rsi', 'bb_position', 'volatility_7', 'volatility_14', 'volatility_30',
                'volume_ratio', 'momentum_3', 'momentum_7', 'momentum_14',
                'hl_ratio', 'close_position'
            ]
            
            return data[feature_columns + ['target']].dropna()
            
        except Exception as e:
            logging.error(f"Crypto feature preparation error: {str(e)}")
            raise

    def predict(self, symbol):
        """Predict cryptocurrency price"""
        try:
            # Get historical data
            data = self.get_crypto_data(symbol, period='6mo')
            current_price = data['Close'].iloc[-1]
            
            # Prepare features
            processed_data = self.prepare_crypto_features(data)
            
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
            
            # Prepare latest features for prediction
            latest_features = processed_data.drop('target', axis=1).iloc[-1:].values
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            predicted_return = self.model.predict(latest_features_scaled)[0]
            predicted_price = current_price * (1 + predicted_return)
            
            # Calculate confidence (crypto has higher uncertainty)
            feature_importance = self.model.feature_importances_
            base_confidence = np.mean(feature_importance)
            confidence = min(0.85, max(0.2, base_confidence * 1.2))  # Lower max confidence for crypto
            
            # Determine signal with crypto-specific thresholds
            if predicted_return > 0.03:  # 3% threshold for crypto
                signal = 'BUY'
            elif predicted_return < -0.03:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            # Get top features
            feature_names = [
                'sma_7', 'sma_14', 'sma_30', 'ema_12', 'ema_26', 'macd', 'macd_signal',
                'rsi', 'bb_position', 'volatility_7', 'volatility_14', 'volatility_30',
                'volume_ratio', 'momentum_3', 'momentum_7', 'momentum_14',
                'hl_ratio', 'close_position'
            ]
            
            top_features = sorted(
                zip(feature_names, feature_importance),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'ticker': symbol,
                'asset_type': 'crypto',
                'current_price': float(current_price),
                'prediction': float(predicted_price),
                'predicted_return': float(predicted_return * 100),  # Convert to percentage
                'confidence': float(confidence),
                'signal': signal,
                'model': 'Crypto Random Forest',
                'top_features': [{'feature': f, 'importance': float(imp)} for f, imp in top_features],
                'volatility_warning': confidence < 0.4
            }
            
        except Exception as e:
            logging.error(f"Crypto prediction error for {symbol}: {str(e)}")
            raise

    def get_market_cap_rank(self, symbol):
        """Get market cap ranking for crypto"""
        try:
            # This would typically use CoinGecko API
            # For now, return estimated ranking based on known symbols
            rankings = {
                'BTC': 1, 'ETH': 2, 'BNB': 3, 'ADA': 4, 'SOL': 5,
                'DOT': 6, 'AVAX': 7, 'LINK': 8, 'MATIC': 9, 'UNI': 10
            }
            return rankings.get(symbol.replace('-USD', ''), 100)
        except:
            return None

    def get_24h_volume(self, symbol):
        """Get 24h trading volume"""
        try:
            data = self.get_crypto_data(symbol, period='2d')
            return float(data['Volume'].iloc[-1])
        except:
            return None

    def get_24h_change(self, symbol):
        """Get 24h price change percentage"""
        try:
            data = self.get_crypto_data(symbol, period='2d')
            if len(data) >= 2:
                current = data['Close'].iloc[-1]
                previous = data['Close'].iloc[-2]
                return float((current - previous) / previous * 100)
            return 0.0
        except:
            return None

    def get_top_gainers(self, limit=10):
        """Get top crypto gainers"""
        try:
            gainers = []
            for symbol in list(self.crypto_symbols.keys())[:limit]:
                try:
                    change = self.get_24h_change(symbol)
                    if change is not None:
                        gainers.append({
                            'symbol': symbol,
                            'change_24h': change
                        })
                except:
                    continue
            
            return sorted(gainers, key=lambda x: x['change_24h'], reverse=True)
        except Exception as e:
            logging.error(f"Error getting crypto gainers: {str(e)}")
            return []

    def get_market_overview(self):
        """Get crypto market overview"""
        try:
            overview = {
                'total_market_cap': 'N/A',  # Would need external API
                'total_volume_24h': 'N/A',
                'bitcoin_dominance': 'N/A',
                'active_cryptocurrencies': len(self.crypto_symbols),
                'top_cryptos': []
            }
            
            # Get data for top cryptos
            for symbol in ['BTC', 'ETH', 'BNB']:
                try:
                    data = self.get_crypto_data(symbol, period='1d')
                    current_price = data['Close'].iloc[-1]
                    change_24h = self.get_24h_change(symbol)
                    
                    overview['top_cryptos'].append({
                        'symbol': symbol,
                        'price': float(current_price),
                        'change_24h': change_24h
                    })
                except:
                    continue
            
            return overview
        except Exception as e:
            logging.error(f"Error getting market overview: {str(e)}")
            return {}
