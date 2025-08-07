import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

class CryptoService:
    """Cryptocurrency prediction and analysis service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.crypto_tickers = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD', 
            'ADA': 'ADA-USD',
            'DOT': 'DOT-USD',
            'SOL': 'SOL-USD',
            'LINK': 'LINK-USD',
            'MATIC': 'MATIC-USD',
            'AVAX': 'AVAX-USD'
        }
    
    def get_supported_cryptos(self):
        """Get list of supported cryptocurrencies"""
        return {
            'cryptos': [
                {'symbol': k, 'name': f'{k} - {v}', 'ticker': v}
                for k, v in self.crypto_tickers.items()
            ],
            'count': len(self.crypto_tickers)
        }
    
    def predict_crypto(self, crypto_symbol):
        """Generate cryptocurrency predictions"""
        try:
            # Normalize symbol
            if crypto_symbol.upper() in self.crypto_tickers:
                ticker = self.crypto_tickers[crypto_symbol.upper()]
            else:
                ticker = f"{crypto_symbol.upper()}-USD"
            
            # Get crypto data
            crypto = yf.Ticker(ticker)
            data = crypto.history(period="90d", interval="1d")
            
            if data.empty:
                return {'error': f'No data available for {crypto_symbol}'}
            
            current_price = data['Close'].iloc[-1]
            
            # Calculate technical indicators
            data['SMA_10'] = data['Close'].rolling(window=10).mean()
            data['SMA_30'] = data['Close'].rolling(window=30).mean()
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['MACD'] = self._calculate_macd(data['Close'])
            
            # Generate predictions using multiple approaches
            rf_prediction = self._random_forest_crypto_prediction(data)
            lstm_prediction = self._lstm_crypto_prediction(data)
            sentiment_prediction = self._crypto_sentiment_prediction(crypto_symbol)
            
            # Ensemble prediction
            ensemble_price = (rf_prediction + lstm_prediction + sentiment_prediction) / 3
            
            # Calculate confidence based on volatility and volume
            volatility = data['Close'].pct_change().std()
            volume_trend = 1.0 if data['Volume'].iloc[-5:].mean() > data['Volume'].iloc[-10:-5].mean() else 0.8
            confidence = min(0.95, max(0.6, (1.0 - volatility) * volume_trend))
            
            # Determine trend
            trend = 'BULLISH' if ensemble_price > current_price * 1.02 else 'BEARISH' if ensemble_price < current_price * 0.98 else 'SIDEWAYS'
            
            prediction = {
                'symbol': crypto_symbol.upper(),
                'ticker': ticker,
                'current_price': current_price,
                'predicted_price': ensemble_price,
                'price_change': (ensemble_price - current_price) / current_price,
                'trend': trend,
                'confidence': confidence,
                'models': {
                    'random_forest': rf_prediction,
                    'lstm': lstm_prediction,
                    'sentiment': sentiment_prediction
                },
                'technical_indicators': {
                    'sma_10': data['SMA_10'].iloc[-1],
                    'sma_30': data['SMA_30'].iloc[-1],
                    'rsi': data['RSI'].iloc[-1],
                    'macd': data['MACD'].iloc[-1]
                },
                'market_metrics': {
                    'volatility': volatility,
                    'volume_trend': 'Increasing' if volume_trend > 0.9 else 'Decreasing',
                    '24h_change': (current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Crypto prediction error for {crypto_symbol}: {str(e)}")
            return {'error': f'Prediction failed: {str(e)}'}
    
    def get_crypto_fear_greed_index(self):
        """Get cryptocurrency fear and greed index"""
        try:
            # Using Alternative.me Fear & Greed Index API
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    index_data = data['data'][0]
                    return {
                        'value': int(index_data['value']),
                        'classification': index_data['value_classification'],
                        'timestamp': index_data['timestamp'],
                        'interpretation': self._interpret_fear_greed(int(index_data['value']))
                    }
            
            # Fallback to calculated sentiment
            return self._calculate_fallback_sentiment()
            
        except Exception as e:
            self.logger.error(f"Fear & Greed Index error: {str(e)}")
            return self._calculate_fallback_sentiment()
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices, fast=12, slow=26):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        return ema_fast - ema_slow
    
    def _random_forest_crypto_prediction(self, data):
        """Simplified Random Forest prediction for crypto"""
        try:
            # Use technical indicators for prediction
            current_price = data['Close'].iloc[-1]
            sma_10 = data['SMA_10'].iloc[-1]
            sma_30 = data['SMA_30'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            
            # Simple rule-based prediction mimicking RF logic
            prediction_factor = 1.0
            
            if sma_10 > sma_30:  # Bullish crossover
                prediction_factor += 0.02
            if rsi < 30:  # Oversold
                prediction_factor += 0.03
            elif rsi > 70:  # Overbought
                prediction_factor -= 0.03
                
            return current_price * prediction_factor
            
        except Exception:
            return data['Close'].iloc[-1] * 1.01  # Slight bullish default
    
    def _lstm_crypto_prediction(self, data):
        """Simplified LSTM prediction for crypto"""
        try:
            # Use recent price momentum
            recent_prices = data['Close'].iloc[-10:]
            momentum = recent_prices.pct_change().mean()
            volatility_adjustment = recent_prices.std() / recent_prices.mean()
            
            prediction_factor = 1.0 + momentum - (volatility_adjustment * 0.5)
            return data['Close'].iloc[-1] * prediction_factor
            
        except Exception:
            return data['Close'].iloc[-1] * 0.995  # Slight bearish default
    
    def _crypto_sentiment_prediction(self, symbol):
        """Generate sentiment-based prediction"""
        try:
            # Get Fear & Greed Index
            fg_data = self.get_crypto_fear_greed_index()
            fg_value = fg_data.get('value', 50)
            
            # Convert sentiment to price factor
            if fg_value >= 75:  # Extreme Greed
                sentiment_factor = 0.98  # Contrarian bearish
            elif fg_value >= 55:  # Greed
                sentiment_factor = 1.01
            elif fg_value >= 45:  # Neutral
                sentiment_factor = 1.0
            elif fg_value >= 25:  # Fear
                sentiment_factor = 1.02  # Contrarian bullish
            else:  # Extreme Fear
                sentiment_factor = 1.05  # Strong contrarian bullish
            
            # Get current price (approximate)
            ticker = self.crypto_tickers.get(symbol, f"{symbol}-USD")
            crypto = yf.Ticker(ticker)
            current_price = crypto.history(period="1d")['Close'].iloc[-1]
            
            return current_price * sentiment_factor
            
        except Exception:
            return 50000  # BTC approximate fallback
    
    def _interpret_fear_greed(self, value):
        """Interpret Fear & Greed Index value"""
        if value >= 75:
            return "Extreme Greed - Market may be overvalued, consider taking profits"
        elif value >= 55:
            return "Greed - Bullish sentiment, but watch for reversal signals"
        elif value >= 45:
            return "Neutral - Balanced market sentiment"
        elif value >= 25:
            return "Fear - Potential buying opportunity, but exercise caution"
        else:
            return "Extreme Fear - Strong buying opportunity for long-term holders"
    
    def _calculate_fallback_sentiment(self):
        """Calculate fallback sentiment when API is unavailable"""
        return {
            'value': 50,
            'classification': 'Neutral',
            'timestamp': str(int(datetime.now().timestamp())),
            'interpretation': 'Neutral market sentiment (calculated fallback)'
        }
    
    def get_top_cryptos(self):
        """Get information about top cryptocurrencies"""
        cryptos = []
        for symbol, ticker in self.crypto_tickers.items():
            try:
                crypto = yf.Ticker(ticker)
                data = crypto.history(period="7d")
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    change_7d = (current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]
                    
                    cryptos.append({
                        'symbol': symbol,
                        'ticker': ticker,
                        'current_price': current_price,
                        'change_7d': change_7d,
                        'volume': data['Volume'].iloc[-1]
                    })
            except Exception as e:
                self.logger.error(f"Error fetching {symbol}: {str(e)}")
                continue
        
        return sorted(cryptos, key=lambda x: x.get('volume', 0), reverse=True)