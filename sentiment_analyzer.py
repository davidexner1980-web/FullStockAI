from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
from bs4 import BeautifulSoup
from backend.data_fetcher import DataFetcher
import logging
import time

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.data_fetcher = DataFetcher()
        
    def analyze_text(self, text):
        """Analyze sentiment of a text string"""
        try:
            scores = self.analyzer.polarity_scores(text)
            
            # Determine overall sentiment
            if scores['compound'] >= 0.05:
                sentiment = 'positive'
            elif scores['compound'] <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }
        except Exception as e:
            logging.error(f"Error analyzing text sentiment: {str(e)}")
            return {
                'sentiment': 'neutral',
                'compound': 0.0,
                'positive': 0.33,
                'negative': 0.33,
                'neutral': 0.34
            }

    def analyze_ticker(self, ticker):
        """Analyze sentiment for a specific ticker"""
        try:
            # Get news headlines from Yahoo Finance
            headlines = self.data_fetcher.get_news_headlines(ticker)
            
            if not headlines:
                return {
                    'overall_sentiment': 'neutral',
                    'sentiment_score': 0.0,
                    'headline_count': 0,
                    'headlines': []
                }
            
            sentiment_scores = []
            analyzed_headlines = []
            
            for headline in headlines:
                title = headline.get('title', '')
                if title:
                    sentiment = self.analyze_text(title)
                    sentiment_scores.append(sentiment['compound'])
                    
                    analyzed_headlines.append({
                        'title': title,
                        'sentiment': sentiment['sentiment'],
                        'score': sentiment['compound'],
                        'publisher': headline.get('publisher', ''),
                        'publish_time': headline.get('publish_time', 0)
                    })
            
            # Calculate overall sentiment
            if sentiment_scores:
                avg_score = sum(sentiment_scores) / len(sentiment_scores)
                
                if avg_score >= 0.1:
                    overall_sentiment = 'positive'
                elif avg_score <= -0.1:
                    overall_sentiment = 'negative'
                else:
                    overall_sentiment = 'neutral'
            else:
                overall_sentiment = 'neutral'
                avg_score = 0.0
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_score': round(avg_score, 3),
                'headline_count': len(analyzed_headlines),
                'headlines': analyzed_headlines[:10],  # Return top 10
                'positive_count': len([h for h in analyzed_headlines if h['sentiment'] == 'positive']),
                'negative_count': len([h for h in analyzed_headlines if h['sentiment'] == 'negative']),
                'neutral_count': len([h for h in analyzed_headlines if h['sentiment'] == 'neutral'])
            }
        except Exception as e:
            logging.error(f"Error analyzing sentiment for {ticker}: {str(e)}")
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'headline_count': 0,
                'headlines': [],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }

    def get_social_sentiment(self, ticker):
        """Get social media sentiment (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In production, you would integrate with Twitter API, Reddit API, etc.
            
            # For now, we'll use news sentiment as a proxy
            news_sentiment = self.analyze_ticker(ticker)
            
            # Simulate social sentiment with some variation
            base_score = news_sentiment['sentiment_score']
            social_variation = 0.1  # Add some noise to simulate social media
            
            import random
            social_score = base_score + random.uniform(-social_variation, social_variation)
            social_score = max(-1, min(1, social_score))  # Clamp to [-1, 1]
            
            if social_score >= 0.1:
                social_sentiment = 'positive'
            elif social_score <= -0.1:
                social_sentiment = 'negative'
            else:
                social_sentiment = 'neutral'
            
            return {
                'social_sentiment': social_sentiment,
                'social_score': round(social_score, 3),
                'mentions_count': random.randint(100, 1000),  # Simulated
                'engagement_rate': round(random.uniform(0.05, 0.25), 3)  # Simulated
            }
        except Exception as e:
            logging.error(f"Error getting social sentiment for {ticker}: {str(e)}")
            return {
                'social_sentiment': 'neutral',
                'social_score': 0.0,
                'mentions_count': 0,
                'engagement_rate': 0.0
            }

    def analyze_market_sentiment(self):
        """Analyze overall market sentiment"""
        try:
            # Analyze sentiment for major indices
            major_tickers = ['SPY', 'QQQ', 'DIA', 'IWM']
            market_sentiments = []
            
            for ticker in major_tickers:
                sentiment = self.analyze_ticker(ticker)
                market_sentiments.append(sentiment['sentiment_score'])
            
            if market_sentiments:
                avg_market_sentiment = sum(market_sentiments) / len(market_sentiments)
                
                if avg_market_sentiment >= 0.1:
                    market_mood = 'bullish'
                elif avg_market_sentiment <= -0.1:
                    market_mood = 'bearish'
                else:
                    market_mood = 'neutral'
            else:
                market_mood = 'neutral'
                avg_market_sentiment = 0.0
            
            return {
                'market_mood': market_mood,
                'sentiment_score': round(avg_market_sentiment, 3),
                'analyzed_indices': major_tickers,
                'individual_scores': dict(zip(major_tickers, market_sentiments))
            }
        except Exception as e:
            logging.error(f"Error analyzing market sentiment: {str(e)}")
            return {
                'market_mood': 'neutral',
                'sentiment_score': 0.0,
                'analyzed_indices': [],
                'individual_scores': {}
            }

    def get_fear_greed_sentiment(self):
        """Convert Fear & Greed index to sentiment"""
        try:
            fear_greed = self.data_fetcher.get_crypto_fear_greed()
            value = fear_greed.get('value', 50)
            
            if value >= 75:
                sentiment = 'extreme_greed'
                sentiment_score = 0.8
            elif value >= 55:
                sentiment = 'greed'
                sentiment_score = 0.4
            elif value >= 45:
                sentiment = 'neutral'
                sentiment_score = 0.0
            elif value >= 25:
                sentiment = 'fear'
                sentiment_score = -0.4
            else:
                sentiment = 'extreme_fear'
                sentiment_score = -0.8
            
            return {
                'fear_greed_sentiment': sentiment,
                'fear_greed_value': value,
                'sentiment_score': sentiment_score,
                'classification': fear_greed.get('classification', 'Neutral')
            }
        except Exception as e:
            logging.error(f"Error getting fear & greed sentiment: {str(e)}")
            return {
                'fear_greed_sentiment': 'neutral',
                'fear_greed_value': 50,
                'sentiment_score': 0.0,
                'classification': 'Neutral'
            }
