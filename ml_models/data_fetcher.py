import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

class DataFetcher:
    """Enhanced data fetcher supporting stocks and cryptocurrencies"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_stock_data(self, ticker, period='1y'):
        """Fetch stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                raise ValueError(f"No data found for ticker {ticker}")
            
            # Add technical indicators
            hist = self._add_technical_indicators(hist)
            
            return hist
            
        except Exception as e:
            logging.error(f"Error fetching stock data for {ticker}: {str(e)}")
            raise
    
    def get_crypto_data(self, ticker, period='1y'):
        """Fetch cryptocurrency data from Yahoo Finance"""
        try:
            # Ensure proper crypto ticker format
            if not ticker.endswith('-USD'):
                ticker += '-USD'
            
            crypto = yf.Ticker(ticker)
            hist = crypto.history(period=period)
            
            if hist.empty:
                raise ValueError(f"No data found for crypto {ticker}")
            
            # Add technical indicators
            hist = self._add_technical_indicators(hist)
            
            return hist
            
        except Exception as e:
            logging.error(f"Error fetching crypto data for {ticker}: {str(e)}")
            raise
    
    def _add_technical_indicators(self, df):
        """Add technical indicators to price data"""
        try:
            # Simple Moving Averages
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price momentum
            df['Price_Change'] = df['Close'].pct_change()
            df['Price_Change_5'] = df['Close'].pct_change(periods=5)
            df['Price_Change_10'] = df['Close'].pct_change(periods=10)
            
            # Volatility
            df['Volatility'] = df['Price_Change'].rolling(window=20).std()
            
            return df
            
        except Exception as e:
            logging.error(f"Error adding technical indicators: {str(e)}")
            return df
    
    def get_options_data(self, ticker):
        """Fetch options chain data"""
        try:
            stock = yf.Ticker(ticker)
            options_dates = stock.options
            
            if not options_dates:
                return {'error': 'No options data available'}
            
            # Get the nearest expiration date
            nearest_date = options_dates[0]
            option_chain = stock.option_chain(nearest_date)
            
            calls = option_chain.calls
            puts = option_chain.puts
            
            # Get current stock price
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # Find at-the-money options
            atm_calls = calls[calls['strike'].sub(current_price).abs().argsort()[:5]]
            atm_puts = puts[puts['strike'].sub(current_price).abs().argsort()[:5]]
            
            result = {
                'current_price': current_price,
                'expiration_date': nearest_date,
                'calls': atm_calls.to_dict('records'),
                'puts': atm_puts.to_dict('records'),
                'iv_rank': self._calculate_iv_rank(calls, puts)
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Error fetching options data for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_iv_rank(self, calls, puts):
        """Calculate implied volatility rank"""
        try:
            all_iv = pd.concat([calls['impliedVolatility'], puts['impliedVolatility']])
            avg_iv = all_iv.mean()
            
            # Simple IV rank calculation (in real implementation, use historical IV data)
            if avg_iv < 0.2:
                return 'LOW'
            elif avg_iv < 0.4:
                return 'MEDIUM'
            else:
                return 'HIGH'
                
        except:
            return 'UNKNOWN'
    
    def get_chart_data(self, ticker, period='1y'):
        """Get chart data for visualization"""
        try:
            # Determine if it's crypto or stock
            if ticker.endswith('-USD') or ticker in ['BTC', 'ETH', 'ADA', 'DOT', 'LINK']:
                data = self.get_crypto_data(ticker, period)
            else:
                data = self.get_stock_data(ticker, period)
            
            # Prepare chart data
            chart_data = {
                'labels': [date.strftime('%Y-%m-%d') for date in data.index],
                'prices': data['Close'].tolist(),
                'volumes': data['Volume'].tolist(),
                'high': data['High'].tolist(),
                'low': data['Low'].tolist(),
                'open': data['Open'].tolist(),
                'sma_20': data['SMA_20'].fillna(0).tolist(),
                'sma_50': data['SMA_50'].fillna(0).tolist(),
                'rsi': data['RSI'].fillna(50).tolist(),
                'bb_upper': data['BB_Upper'].fillna(0).tolist(),
                'bb_lower': data['BB_Lower'].fillna(0).tolist(),
                'volume_sma': data['Volume_SMA'].fillna(0).tolist()
            }
            
            return chart_data
            
        except Exception as e:
            logging.error(f"Error preparing chart data for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def get_company_info(self, ticker):
        """Get company/asset information"""
        try:
            asset = yf.Ticker(ticker)
            info = asset.info
            
            return {
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'day_change': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0)
            }
            
        except Exception as e:
            logging.error(f"Error fetching company info for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def get_market_indices(self):
        """Get major market indices data"""
        try:
            indices = ['SPY', 'QQQ', 'DIA', 'IWM']
            index_data = {}
            
            for index in indices:
                data = self.get_stock_data(index, '5d')
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    
                    index_data[index] = {
                        'price': current_price,
                        'change': change_pct,
                        'volume': data['Volume'].iloc[-1]
                    }
            
            return index_data
            
        except Exception as e:
            logging.error(f"Error fetching market indices: {str(e)}")
            return {}
    
    def get_news_headlines(self, ticker):
        """Fetch news headlines for sentiment analysis"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            headlines = []
            for article in news[:10]:  # Get top 10 articles
                headlines.append({
                    'title': article.get('title', ''),
                    'link': article.get('link', ''),
                    'publisher': article.get('publisher', ''),
                    'publish_time': article.get('providerPublishTime', 0)
                })
            
            return headlines
            
        except Exception as e:
            logging.error(f"Error fetching news for {ticker}: {str(e)}")
            return []
