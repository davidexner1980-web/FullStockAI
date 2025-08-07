import logging
import yfinance as yf
import numpy as np
from datetime import datetime

class PortfolioAnalyzer:
    """Advanced portfolio analysis and optimization service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_portfolio(self, tickers, weights=None):
        """Analyze portfolio composition and risk metrics"""
        try:
            if weights is None:
                weights = [1.0 / len(tickers)] * len(tickers)
            
            portfolio_data = []
            total_value = 0
            
            for i, ticker in enumerate(tickers):
                try:
                    stock = yf.Ticker(ticker)
                    data = stock.history(period="30d")
                    
                    if not data.empty:
                        current_price = data['Close'].iloc[-1]
                        daily_returns = data['Close'].pct_change().mean()
                        volatility = data['Close'].pct_change().std()
                        
                        portfolio_data.append({
                            'ticker': ticker,
                            'weight': weights[i],
                            'current_price': current_price,
                            'expected_return': daily_returns * 252,  # Annualized
                            'volatility': volatility * np.sqrt(252),  # Annualized
                            'sharpe_ratio': (daily_returns * 252) / (volatility * np.sqrt(252)) if volatility > 0 else 0
                        })
                        
                        total_value += current_price * weights[i]
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing {ticker}: {str(e)}")
                    continue
            
            if not portfolio_data:
                return {'error': 'No valid data for portfolio analysis'}
            
            # Calculate portfolio metrics
            portfolio_return = sum(item['expected_return'] * item['weight'] for item in portfolio_data)
            portfolio_volatility = np.sqrt(sum((item['volatility'] * item['weight']) ** 2 for item in portfolio_data))
            portfolio_sharpe = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            return {
                'portfolio_metrics': {
                    'expected_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': portfolio_sharpe,
                    'total_value': total_value
                },
                'individual_assets': portfolio_data,
                'analysis_date': datetime.now().isoformat(),
                'recommendation': 'HOLD' if portfolio_sharpe > 0.5 else 'REBALANCE'
            }
            
        except Exception as e:
            self.logger.error(f"Portfolio analysis error: {str(e)}")
            return {'error': f'Analysis failed: {str(e)}'}