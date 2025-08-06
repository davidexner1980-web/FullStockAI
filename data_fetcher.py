import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import time

class DataFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def get_stock_data(self, ticker, period='1y', interval='1d'):
        """Fetch stock data from Yahoo Finance"""
        try:
            cache_key = f"{ticker}_{period}_{interval}"
            
            # Check cache
            if cache_key in self.cache:
                data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    return data
            
            # Fetch fresh data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logging.warning(f"No data found for ticker {ticker}")
                return pd.DataFrame()
            
            # Cache the data
            self.cache[cache_key] = (df, time.time())
            
            return df
        except Exception as e:
            logging.error(f"Error fetching stock data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def get_crypto_data(self, ticker, period='1y', interval='1d'):
        """Fetch cryptocurrency data from Yahoo Finance"""
        try:
            # Ensure crypto ticker format
            if not ticker.endswith('-USD'):
                ticker = f"{ticker}-USD"
            
            return self.get_stock_data(ticker, period, interval)
        except Exception as e:
            logging.error(f"Error fetching crypto data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def get_options_data(self, ticker):
        """Fetch options chain data"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get options expiration dates
            exp_dates = stock.options
            if not exp_dates:
                return {'error': 'No options data available'}
            
            # Get options for the nearest expiration
            nearest_exp = exp_dates[0]
            options_chain = stock.option_chain(nearest_exp)
            
            calls = options_chain.calls
            puts = options_chain.puts
            
            # Get current stock price
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            
            # Find ATM options
            atm_strike = round(current_price / 5) * 5  # Round to nearest $5
            
            atm_calls = calls[calls['strike'] == atm_strike]
            atm_puts = puts[puts['strike'] == atm_strike]
            
            return {
                'current_price': round(current_price, 2),
                'expiration_date': nearest_exp,
                'atm_strike': atm_strike,
                'calls': calls.head(10).to_dict('records'),
                'puts': puts.head(10).to_dict('records'),
                'atm_call': atm_calls.to_dict('records')[0] if not atm_calls.empty else None,
                'atm_put': atm_puts.to_dict('records')[0] if not atm_puts.empty else None
            }
        except Exception as e:
            logging.error(f"Error fetching options data for {ticker}: {str(e)}")
            return {'error': str(e)}

    def get_chart_data(self, ticker, period='6mo'):
        """Get chart-ready data for visualization"""
        try:
            df = self.get_stock_data(ticker, period=period)
            if df.empty:
                return {'error': 'No data available'}
            
            # Prepare data for Chart.js
            dates = df.index.strftime('%Y-%m-%d').tolist()
            
            return {
                'labels': dates,
                'prices': df['Close'].round(2).tolist(),
                'volumes': df['Volume'].tolist(),
                'high': df['High'].round(2).tolist(),
                'low': df['Low'].round(2).tolist(),
                'open': df['Open'].round(2).tolist()
            }
        except Exception as e:
            logging.error(f"Error fetching chart data for {ticker}: {str(e)}")
            return {'error': str(e)}

    def get_company_info(self, ticker):
        """Get company information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'description': info.get('longBusinessSummary', '')[:500] + '...' if info.get('longBusinessSummary') else ''
            }
        except Exception as e:
            logging.error(f"Error fetching company info for {ticker}: {str(e)}")
            return {'name': ticker, 'error': str(e)}

    def get_market_indices(self):
        """Get major market indices data"""
        try:
            indices = {
                'SPY': 'S&P 500',
                'QQQ': 'NASDAQ 100',
                'DIA': 'Dow Jones',
                'IWM': 'Russell 2000',
                'VTI': 'Total Stock Market'
            }
            
            data = {}
            for ticker, name in indices.items():
                df = self.get_stock_data(ticker, period='5d')
                if not df.empty:
                    current = df['Close'].iloc[-1]
                    previous = df['Close'].iloc[-2] if len(df) > 1 else current
                    change = current - previous
                    change_pct = (change / previous) * 100
                    
                    data[ticker] = {
                        'name': name,
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_pct, 2)
                    }
            
            return data
        except Exception as e:
            logging.error(f"Error fetching market indices: {str(e)}")
            return {}

    def get_news_headlines(self, ticker):
        """Get news headlines for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            headlines = []
            for article in news[:10]:  # Get top 10 headlines
                headlines.append({
                    'title': article.get('title', ''),
                    'publisher': article.get('publisher', ''),
                    'publish_time': article.get('providerPublishTime', 0),
                    'link': article.get('link', '')
                })
            
            return headlines
        except Exception as e:
            logging.error(f"Error fetching news for {ticker}: {str(e)}")
            return []

    def get_crypto_fear_greed(self):
        """Get Crypto Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][0]
                    return {
                        'value': int(latest['value']),
                        'classification': latest['value_classification'],
                        'timestamp': latest['timestamp']
                    }
            
            # Fallback calculation based on Bitcoin volatility
            btc_data = self.get_crypto_data('BTC-USD', period='30d')
            if not btc_data.empty:
                volatility = btc_data['Close'].pct_change().std() * 100
                if volatility < 2:
                    value = 75  # Greed
                    classification = "Greed"
                elif volatility < 4:
                    value = 50  # Neutral
                    classification = "Neutral"
                else:
                    value = 25  # Fear
                    classification = "Fear"
                
                return {
                    'value': value,
                    'classification': classification,
                    'timestamp': int(time.time())
                }
            
            return {'value': 50, 'classification': 'Neutral', 'timestamp': int(time.time())}
        except Exception as e:
            logging.error(f"Error fetching fear & greed index: {str(e)}")
            return {'value': 50, 'classification': 'Neutral', 'timestamp': int(time.time())}

    def get_trending_crypto(self):
        """Get trending cryptocurrencies"""
        try:
            # Popular crypto tickers
            crypto_list = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 'XRP-USD', 'DOT-USD', 'DOGE-USD']
            
            trending = []
            for ticker in crypto_list:
                df = self.get_crypto_data(ticker, period='7d')
                if not df.empty:
                    current = df['Close'].iloc[-1]
                    week_ago = df['Close'].iloc[0]
                    change_pct = ((current - week_ago) / week_ago) * 100
                    
                    trending.append({
                        'symbol': ticker.replace('-USD', ''),
                        'price': round(current, 6),
                        'change_7d': round(change_pct, 2),
                        'volume': int(df['Volume'].iloc[-1])
                    })
            
            # Sort by 7-day change
            trending.sort(key=lambda x: abs(x['change_7d']), reverse=True)
            
            return trending[:6]  # Return top 6
        except Exception as e:
            logging.error(f"Error fetching trending crypto: {str(e)}")
            return []
