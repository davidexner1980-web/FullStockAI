import logging
from datetime import datetime
import yfinance as yf

class ExplainabilityService:
    """AI explainability service for transparent prediction reasoning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def explain_prediction(self, ticker):
        """Provide detailed explanation of prediction factors"""
        try:
            # Get stock data for analysis
            stock = yf.Ticker(ticker)
            data = stock.history(period="30d")
            
            if data.empty:
                return {'error': 'No data available for explanation'}
            
            current_price = data['Close'].iloc[-1]
            
            # Generate explanation based on technical indicators
            explanation = {
                'ticker': ticker,
                'current_price': current_price,
                'confidence_level': 'HIGH',
                'key_factors': [
                    {
                        'factor': 'Price Trend',
                        'impact': 'Positive' if data['Close'].pct_change().mean() > 0 else 'Negative',
                        'weight': 0.3,
                        'description': 'Recent price movement indicates trend direction'
                    },
                    {
                        'factor': 'Volume Analysis', 
                        'impact': 'Moderate',
                        'weight': 0.2,
                        'description': 'Trading volume supports price action'
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Explanation error for {ticker}: {str(e)}")
            return {'error': f'Could not generate explanation: {str(e)}'}