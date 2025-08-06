import requests
from textblob import TextBlob
import yfinance as yf
import logging
from datetime import datetime
import re

class SentimentAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def clean_text(self, text):
        """Clean and preprocess text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.lower()
    
    def analyze_text_sentiment(self, text):
        """Analyze sentiment of a single text using TextBlob"""
        try:
            cleaned_text = self.clean_text(text)
            if not cleaned_text:
                return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral'}
            
            blob = TextBlob(cleaned_text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Classify sentiment
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'sentiment': sentiment,
                'confidence': abs(polarity)
            }
        except Exception as e:
            logging.error(f"Error analyzing text sentiment: {str(e)}")
            return {'polarity': 0, 'subjectivity': 0, 'sentiment': 'neutral', 'confidence': 0}
    
    def get_news_headlines(self, ticker):
        """Get news headlines from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            headlines = []
            for article in news[:15]:  # Get top 15 articles
                headline = article.get('title', '')
                summary = article.get('summary', '')
                if headline:
                    headlines.append({
                        'headline': headline,
                        'summary': summary,
                        'publisher': article.get('publisher', ''),
                        'publish_time': article.get('providerPublishTime', 0)
                    })
            
            return headlines
        except Exception as e:
            logging.error(f"Error fetching news for {ticker}: {str(e)}")
            return []
    
    def analyze_sentiment(self, ticker):
        """Analyze overall sentiment for a ticker"""
        try:
            headlines = self.get_news_headlines(ticker)
            
            if not headlines:
                return {
                    'ticker': ticker,
                    'overall_sentiment': 'neutral',
                    'sentiment_score': 0,
                    'confidence': 0,
                    'total_articles': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'analysis_time': datetime.now().isoformat(),
                    'headlines': []
                }
            
            # Analyze each headline
            analyzed_headlines = []
            sentiments = []
            
            for article in headlines:
                # Combine headline and summary for analysis
                full_text = f"{article['headline']} {article.get('summary', '')}"
                sentiment_result = self.analyze_text_sentiment(full_text)
                
                analyzed_headlines.append({
                    'headline': article['headline'],
                    'sentiment': sentiment_result['sentiment'],
                    'polarity': sentiment_result['polarity'],
                    'confidence': sentiment_result['confidence'],
                    'publisher': article['publisher']
                })
                
                sentiments.append(sentiment_result['polarity'])
            
            # Calculate overall sentiment
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Count sentiment types
            positive_count = sum(1 for s in analyzed_headlines if s['sentiment'] == 'positive')
            negative_count = sum(1 for s in analyzed_headlines if s['sentiment'] == 'negative')
            neutral_count = sum(1 for s in analyzed_headlines if s['sentiment'] == 'neutral')
            
            # Determine overall sentiment
            if avg_sentiment > 0.1:
                overall_sentiment = 'positive'
            elif avg_sentiment < -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # Calculate confidence based on consistency
            sentiment_consistency = max(positive_count, negative_count, neutral_count) / len(analyzed_headlines)
            confidence = abs(avg_sentiment) * sentiment_consistency
            
            # Generate sentiment insights
            insights = self.generate_sentiment_insights(
                overall_sentiment, positive_count, negative_count, neutral_count, confidence
            )
            
            return {
                'ticker': ticker,
                'overall_sentiment': overall_sentiment,
                'sentiment_score': round(avg_sentiment, 3),
                'confidence': round(confidence, 3),
                'total_articles': len(analyzed_headlines),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'sentiment_distribution': {
                    'positive': round(positive_count / len(analyzed_headlines) * 100, 1),
                    'negative': round(negative_count / len(analyzed_headlines) * 100, 1),
                    'neutral': round(neutral_count / len(analyzed_headlines) * 100, 1)
                },
                'insights': insights,
                'analysis_time': datetime.now().isoformat(),
                'headlines': analyzed_headlines[:10]  # Return top 10 for display
            }
            
        except Exception as e:
            logging.error(f"Error analyzing sentiment for {ticker}: {str(e)}")
            raise
    
    def generate_sentiment_insights(self, overall_sentiment, positive, negative, neutral, confidence):
        """Generate human-readable sentiment insights"""
        insights = []
        
        total_articles = positive + negative + neutral
        positive_pct = (positive / total_articles) * 100
        negative_pct = (negative / total_articles) * 100
        
        if overall_sentiment == 'positive':
            insights.append(f"Market sentiment is bullish with {positive_pct:.1f}% positive coverage")
            if confidence > 0.3:
                insights.append("High confidence in positive sentiment trend")
            else:
                insights.append("Moderate confidence - mixed signals detected")
        elif overall_sentiment == 'negative':
            insights.append(f"Market sentiment is bearish with {negative_pct:.1f}% negative coverage")
            if confidence > 0.3:
                insights.append("High confidence in negative sentiment trend")
            else:
                insights.append("Moderate confidence - some positive signals present")
        else:
            insights.append("Market sentiment is neutral - balanced coverage")
            insights.append("No clear directional bias in recent news")
        
        # Add specific insights based on distribution
        if positive > negative * 2:
            insights.append("Strong positive momentum in news coverage")
        elif negative > positive * 2:
            insights.append("Strong negative momentum in news coverage")
        elif neutral > (positive + negative):
            insights.append("Predominantly factual reporting without sentiment bias")
        
        return insights
    
    def get_social_sentiment(self, ticker):
        """Get social media sentiment (placeholder for future implementation)"""
        # This would integrate with Twitter API, Reddit API, etc.
        # For now, return a placeholder response
        return {
            'ticker': ticker,
            'social_sentiment': 'neutral',
            'social_score': 0,
            'sources': ['twitter', 'reddit', 'stocktwits'],
            'message': 'Social sentiment analysis coming soon'
        }
    
    def compare_sentiment_with_price(self, ticker):
        """Compare sentiment with recent price action"""
        try:
            # Get sentiment
            sentiment_data = self.analyze_sentiment(ticker)
            
            # Get recent price data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            
            if len(hist) < 2:
                return {'error': 'Insufficient price data'}
            
            recent_return = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
            
            # Compare sentiment with price movement
            sentiment_score = sentiment_data['sentiment_score']
            
            if sentiment_score > 0.1 and recent_return > 0:
                alignment = 'positive_aligned'
                message = "Positive sentiment aligns with recent price gains"
            elif sentiment_score < -0.1 and recent_return < 0:
                alignment = 'negative_aligned'
                message = "Negative sentiment aligns with recent price decline"
            elif sentiment_score > 0.1 and recent_return < 0:
                alignment = 'sentiment_leading'
                message = "Positive sentiment may indicate price recovery ahead"
            elif sentiment_score < -0.1 and recent_return > 0:
                alignment = 'price_leading'
                message = "Price gains despite negative sentiment - potential reversal"
            else:
                alignment = 'neutral'
                message = "Neutral sentiment with mixed price signals"
            
            return {
                'ticker': ticker,
                'sentiment_score': sentiment_score,
                'price_return_5d': round(recent_return, 2),
                'alignment': alignment,
                'message': message,
                'confidence': sentiment_data['confidence']
            }
            
        except Exception as e:
            logging.error(f"Error comparing sentiment with price for {ticker}: {str(e)}")
            return {'error': str(e)}
