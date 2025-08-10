import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
try:
    import talib
except ImportError:
    talib = None
    logging.warning("TA-Lib not installed; technical indicators will be limited.")
import requests
from app import cache

class DataFetcher:
    """Enhanced data fetcher with cryptocurrency support and technical indicators"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @cache.cached(timeout=300, key_prefix='stock_data')
    def get_stock_data(self, ticker, period='1y', interval='1d'):
        """Fetch stock data with technical indicators"""
        try:
            stock = yf.Ticker(ticker, session=self.session)
            data = stock.history(period=period, interval=interval)
            
            if data.empty:
                logging.warning(f"No data found for ticker: {ticker}")
                return None
            
            # Add technical indicators
            data = self._add_technical_indicators(data)
            
            return data
            
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    @cache.cached(timeout=300, key_prefix='crypto_data')
    def get_crypto_data(self, symbol, period='1y', interval='1d'):
        """Fetch cryptocurrency data"""
        try:
            # Format symbol for yfinance (e.g., BTC-USD)
            if not symbol.endswith('-USD'):
                symbol = f"{symbol}-USD"
            
            crypto = yf.Ticker(symbol, session=self.session)
            data = crypto.history(period=period, interval=interval)
            
            if data.empty:
                logging.warning(f"No crypto data found for: {symbol}")
                return None
            
            # Add technical indicators
            data = self._add_technical_indicators(data)
            
            return data
            
        except Exception as e:
            logging.error(f"Error fetching crypto data for {symbol}: {str(e)}")
            return None
    
    def _add_technical_indicators(self, data):
        """Add comprehensive technical indicators"""
        if talib is None:
            logging.warning('TA-Lib not available. Skipping technical indicators.')
            return data
        try:
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values
            volume = data['Volume'].values
            
            # Moving averages
            data['SMA_20'] = talib.SMA(close, timeperiod=20)
            data['SMA_50'] = talib.SMA(close, timeperiod=50)
            data['EMA_12'] = talib.EMA(close, timeperiod=12)
            data['EMA_26'] = talib.EMA(close, timeperiod=26)
            
            # MACD
            macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            data['MACD'] = macd
            data['MACD_Signal'] = macdsignal
            data['MACD_Hist'] = macdhist
            
            # RSI
            data['RSI'] = talib.RSI(close, timeperiod=14)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            data['BB_Upper'] = bb_upper
            data['BB_Middle'] = bb_middle
            data['BB_Lower'] = bb_lower
            
            # Stochastic
            slowk, slowd = talib.STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
            data['Stoch_K'] = slowk
            data['Stoch_D'] = slowd
            
            # Williams %R
            data['Williams_R'] = talib.WILLR(high, low, close, timeperiod=14)
            
            # Average True Range
            data['ATR'] = talib.ATR(high, low, close, timeperiod=14)
            
            # Volume indicators
            data['OBV'] = talib.OBV(close, volume)
            data['AD'] = talib.AD(high, low, close, volume)
            
            # Momentum indicators
            data['MOM'] = talib.MOM(close, timeperiod=10)
            data['ROC'] = talib.ROC(close, timeperiod=10)
            
            # Pattern recognition (sample)
            data['HAMMER'] = talib.CDLHAMMER(data['Open'], high, low, close)
            data['DOJI'] = talib.CDLDOJI(data['Open'], high, low, close)
            
            # Price features
            data['Price_Change'] = data['Close'].pct_change()
            data['Volatility'] = data['Price_Change'].rolling(window=20).std()
            data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
            
            # Support and Resistance levels (simplified)
            data['Support'] = data['Low'].rolling(window=20).min()
            data['Resistance'] = data['High'].rolling(window=20).max()
            
            return data.fillna(method='ffill').fillna(0)
            
        except Exception as e:
            logging.error(f"Error adding technical indicators: {str(e)}")
            return data
    
    def get_options_data(self, ticker):
        """Fetch options chain data"""
        try:
            stock = yf.Ticker(ticker, session=self.session)
            options_dates = stock.options
            
            if not options_dates:
                return None
            
            # Get nearest expiration
            nearest_date = options_dates[0]
            options_chain = stock.option_chain(nearest_date)
            
            return {
                'expiration_date': nearest_date,
                'calls': options_chain.calls.to_dict('records'),
                'puts': options_chain.puts.to_dict('records')
            }
            
        except Exception as e:
            logging.error(f"Error fetching options for {ticker}: {str(e)}")
            return None
    
    def get_news_sentiment(self, ticker):
        """Fetch news and sentiment data"""
        try:
            stock = yf.Ticker(ticker, session=self.session)
            news = stock.news
            
            if not news:
                return {'sentiment': 'neutral', 'headlines': []}
            
            headlines = []
            for article in news[:10]:  # Top 10 articles
                headlines.append({
                    'title': article.get('title', ''),
                    'summary': article.get('summary', ''),
                    'link': article.get('link', ''),
                    'published': article.get('providerPublishTime', 0)
                })
            
            # Simple sentiment scoring (can be enhanced with VADER or other sentiment analyzers)
            positive_words = ['gain', 'rise', 'up', 'bull', 'positive', 'growth', 'strong', 'beat', 'exceed']
            negative_words = ['loss', 'fall', 'down', 'bear', 'negative', 'decline', 'weak', 'miss', 'below']
            
            sentiment_score = 0
            total_headlines = len(headlines)
            
            for headline in headlines:
                title_lower = headline['title'].lower()
                positive_count = sum(1 for word in positive_words if word in title_lower)
                negative_count = sum(1 for word in negative_words if word in title_lower)
                
                if positive_count > negative_count:
                    sentiment_score += 1
                elif negative_count > positive_count:
                    sentiment_score -= 1
            
            if total_headlines > 0:
                normalized_sentiment = sentiment_score / total_headlines
                if normalized_sentiment > 0.2:
                    sentiment = 'positive'
                elif normalized_sentiment < -0.2:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': normalized_sentiment if total_headlines > 0 else 0,
                'headlines': headlines
            }
            
        except Exception as e:
            logging.error(f"Error fetching news for {ticker}: {str(e)}")
            return {'sentiment': 'neutral', 'headlines': []}
