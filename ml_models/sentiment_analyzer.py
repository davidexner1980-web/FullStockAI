import requests
from bs4 import BeautifulSoup
import re
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import time
from .data_fetcher import DataFetcher

class SentimentAnalyzer:
    """Enhanced sentiment analyzer for news and social media"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.data_fetcher = DataFetcher()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_sentiment(self, ticker):
        """Analyze sentiment for a given ticker"""
        try:
            headlines = self._get_all_headlines(ticker)
            
            if not headlines:
                return {
                    'ticker': ticker,
                    'overall_sentiment': 'NEUTRAL',
                    'sentiment_score': 0.0,
                    'confidence': 0.5,
                    'headlines_analyzed': 0,
                    'source_breakdown': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            sentiments = []
            source_sentiments = {}
            
            for headline in headlines:
                # Handle both string and dict formats
                if isinstance(headline, dict):
                    text = headline.get('title', headline.get('headline', ''))
                    source = headline.get('publisher', headline.get('source', 'unknown'))
                else:
                    text = str(headline)
                    source = 'unknown'
                
                if text:
                    scores = self.analyzer.polarity_scores(text)
                    compound_score = scores['compound']
                    sentiments.append(compound_score)
                    
                    if source not in source_sentiments:
                        source_sentiments[source] = []
                    source_sentiments[source].append(compound_score)
            
            if not sentiments:
                return {
                    'ticker': ticker,
                    'overall_sentiment': 'NEUTRAL',
                    'sentiment_score': 0.0,
                    'confidence': 0.5,
                    'headlines_analyzed': 0,
                    'source_breakdown': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            # Calculate overall sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Determine sentiment category
            if avg_sentiment >= 0.05:
                overall_sentiment = 'POSITIVE'
            elif avg_sentiment <= -0.05:
                overall_sentiment = 'NEGATIVE'
            else:
                overall_sentiment = 'NEUTRAL'
            
            # Calculate confidence based on consistency of sentiments
            sentiment_std = self._calculate_std(sentiments)
            confidence = max(0.5, min(0.95, 1 - sentiment_std))
            
            # Calculate source breakdown
            source_breakdown = {}
            for source, scores in source_sentiments.items():
                avg_score = sum(scores) / len(scores)
                source_breakdown[source] = {
                    'sentiment_score': avg_score,
                    'headline_count': len(scores),
                    'sentiment': 'POSITIVE' if avg_score >= 0.05 else 'NEGATIVE' if avg_score <= -0.05 else 'NEUTRAL'
                }
            
            result = {
                'ticker': ticker,
                'overall_sentiment': overall_sentiment,
                'sentiment_score': avg_sentiment,
                'confidence': confidence,
                'headlines_analyzed': len(sentiments),
                'source_breakdown': source_breakdown,
                'individual_scores': sentiments[:10],  # First 10 for debugging
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Sentiment analysis error for {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'error': str(e),
                'overall_sentiment': 'NEUTRAL',
                'sentiment_score': 0.0,
                'confidence': 0.5,
                'headlines_analyzed': 0
            }
    
    def _get_all_headlines(self, ticker):
        """Aggregate headlines from multiple sources"""
        all_headlines = []
        
        # Yahoo Finance headlines
        try:
            yf_headlines = self.data_fetcher.get_news_headlines(ticker)
            all_headlines.extend(yf_headlines)
        except:
            pass
        
        # MarketWatch headlines
        try:
            mw_headlines = self._get_marketwatch_headlines(ticker)
            all_headlines.extend(mw_headlines)
        except:
            pass
        
        # Finviz headlines
        try:
            finviz_headlines = self._get_finviz_headlines(ticker)
            all_headlines.extend(finviz_headlines)
        except:
            pass
        
        return all_headlines
    
    def _get_marketwatch_headlines(self, ticker):
        """Scrape MarketWatch headlines"""
        try:
            url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            headlines = []
            
            # Find headline elements
            headline_elements = soup.find_all(['h3', 'h4', 'a'], class_=re.compile(r'headline|title'))
            
            for element in headline_elements[:10]:
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    headlines.append({
                        'title': text,
                        'source': 'MarketWatch',
                        'publisher': 'MarketWatch'
                    })
            
            return headlines
            
        except Exception as e:
            logging.error(f"Error scraping MarketWatch for {ticker}: {str(e)}")
            return []
    
    def _get_finviz_headlines(self, ticker):
        """Scrape Finviz headlines"""
        try:
            url = f"https://finviz.com/quote.ashx?t={ticker.lower()}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            headlines = []
            
            # Find news table
            news_table = soup.find('table', class_='fullview-news-outer')
            if news_table:
                rows = news_table.find_all('tr')
                
                for row in rows[:10]:
                    link_element = row.find('a')
                    if link_element:
                        text = link_element.get_text(strip=True)
                        if text and len(text) > 20:
                            headlines.append({
                                'title': text,
                                'source': 'Finviz',
                                'publisher': 'Finviz'
                            })
            
            return headlines
            
        except Exception as e:
            logging.error(f"Error scraping Finviz for {ticker}: {str(e)}")
            return []
    
    def _calculate_std(self, values):
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def get_sector_sentiment(self, sector_tickers):
        """Analyze sentiment for a sector"""
        try:
            sector_sentiments = []
            
            for ticker in sector_tickers:
                sentiment_data = self.analyze_sentiment(ticker)
                if 'error' not in sentiment_data:
                    sector_sentiments.append({
                        'ticker': ticker,
                        'sentiment_score': sentiment_data['sentiment_score'],
                        'sentiment': sentiment_data['overall_sentiment']
                    })
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            if not sector_sentiments:
                return {'error': 'No sentiment data available for sector'}
            
            # Calculate sector-wide sentiment
            avg_sentiment = sum(s['sentiment_score'] for s in sector_sentiments) / len(sector_sentiments)
            
            positive_count = sum(1 for s in sector_sentiments if s['sentiment'] == 'POSITIVE')
            negative_count = sum(1 for s in sector_sentiments if s['sentiment'] == 'NEGATIVE')
            neutral_count = len(sector_sentiments) - positive_count - negative_count
            
            result = {
                'sector_sentiment_score': avg_sentiment,
                'sector_sentiment': 'POSITIVE' if avg_sentiment >= 0.05 else 'NEGATIVE' if avg_sentiment <= -0.05 else 'NEUTRAL',
                'positive_stocks': positive_count,
                'negative_stocks': negative_count,
                'neutral_stocks': neutral_count,
                'individual_sentiments': sector_sentiments,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Sector sentiment analysis error: {str(e)}")
            return {'error': str(e)}
    
    def get_market_fear_greed_index(self):
        """Calculate a simple fear & greed index based on market sentiment"""
        try:
            # Major indices for market sentiment
            indices = ['SPY', 'QQQ', 'DIA', 'IWM']
            market_sentiments = []
            
            for index in indices:
                sentiment = self.analyze_sentiment(index)
                if 'error' not in sentiment:
                    market_sentiments.append(sentiment['sentiment_score'])
            
            if not market_sentiments:
                return {'error': 'Unable to calculate market sentiment'}
            
            avg_sentiment = sum(market_sentiments) / len(market_sentiments)
            
            # Convert to 0-100 scale (Fear & Greed Index style)
            fear_greed_score = int((avg_sentiment + 1) * 50)
            fear_greed_score = max(0, min(100, fear_greed_score))
            
            if fear_greed_score >= 75:
                fear_greed_label = 'Extreme Greed'
            elif fear_greed_score >= 55:
                fear_greed_label = 'Greed'
            elif fear_greed_score >= 45:
                fear_greed_label = 'Neutral'
            elif fear_greed_score >= 25:
                fear_greed_label = 'Fear'
            else:
                fear_greed_label = 'Extreme Fear'
            
            result = {
                'fear_greed_score': fear_greed_score,
                'fear_greed_label': fear_greed_label,
                'market_sentiment_score': avg_sentiment,
                'indices_analyzed': len(market_sentiments),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Fear & Greed Index calculation error: {str(e)}")
            return {'error': str(e)}
