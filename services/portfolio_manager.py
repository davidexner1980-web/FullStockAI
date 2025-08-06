import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from services.data_fetcher import DataFetcher
import logging

class PortfolioManager:
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    def calculate_portfolio_metrics(self, holdings):
        """Calculate comprehensive portfolio metrics"""
        try:
            portfolio_data = []
            total_value = 0
            
            for holding in holdings:
                ticker = holding['ticker']
                quantity = holding['quantity']
                avg_price = holding['avg_price']
                
                # Get current price
                current_data = self.data_fetcher.get_real_time_price(ticker)
                current_price = current_data['current_price']
                
                # Calculate position metrics
                position_value = quantity * current_price
                cost_basis = quantity * avg_price
                unrealized_pnl = position_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                portfolio_data.append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'position_value': position_value,
                    'cost_basis': cost_basis,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_pct': unrealized_pnl_pct,
                    'weight': 0  # Will be calculated after total value
                })
                
                total_value += position_value
            
            # Calculate weights
            for position in portfolio_data:
                position['weight'] = (position['position_value'] / total_value) * 100 if total_value > 0 else 0
            
            # Calculate overall portfolio metrics
            total_cost = sum(p['cost_basis'] for p in portfolio_data)
            total_pnl = sum(p['unrealized_pnl'] for p in portfolio_data)
            total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
            
            return {
                'positions': portfolio_data,
                'total_value': total_value,
                'total_cost': total_cost,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'num_positions': len(portfolio_data),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error calculating portfolio metrics: {str(e)}")
            raise

    def analyze_portfolio(self, tickers, weights=None):
        """Analyze portfolio with correlation and risk metrics"""
        try:
            if weights is None:
                weights = [1/len(tickers)] * len(tickers)  # Equal weights
            
            # Get historical data for all tickers
            price_data = {}
            for ticker in tickers:
                try:
                    data = self.data_fetcher.get_historical_data(ticker, period='1y')
                    price_data[ticker] = data['Close']
                except:
                    logging.warning(f"Could not fetch data for {ticker}")
                    continue
            
            if not price_data:
                raise ValueError("No valid ticker data found")
            
            # Create price dataframe
            df = pd.DataFrame(price_data)
            df = df.dropna()
            
            # Calculate returns
            returns = df.pct_change().dropna()
            
            # Portfolio metrics
            portfolio_returns = (returns * weights).sum(axis=1)
            
            # Risk metrics
            annual_return = portfolio_returns.mean() * 252
            annual_volatility = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
            
            # Correlation matrix
            correlation_matrix = returns.corr().round(3)
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(portfolio_returns, 5)
            
            # Individual stock metrics
            stock_metrics = []
            for ticker in df.columns:
                stock_returns = returns[ticker]
                stock_metrics.append({
                    'ticker': ticker,
                    'weight': weights[tickers.index(ticker)] * 100,
                    'annual_return': stock_returns.mean() * 252 * 100,
                    'annual_volatility': stock_returns.std() * np.sqrt(252) * 100,
                    'beta': self.calculate_beta(stock_returns, portfolio_returns),
                    'current_price': df[ticker].iloc[-1]
                })
            
            # Diversification metrics
            avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            
            return {
                'portfolio_metrics': {
                    'annual_return': round(annual_return * 100, 2),
                    'annual_volatility': round(annual_volatility * 100, 2),
                    'sharpe_ratio': round(sharpe_ratio, 3),
                    'max_drawdown': round(max_drawdown * 100, 2),
                    'value_at_risk_95': round(var_95 * 100, 2),
                    'avg_correlation': round(avg_correlation, 3)
                },
                'stock_metrics': stock_metrics,
                'correlation_matrix': correlation_matrix.to_dict(),
                'recommendations': self.generate_portfolio_recommendations(
                    annual_return, annual_volatility, avg_correlation, max_drawdown
                ),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Portfolio analysis error: {str(e)}")
            raise

    def calculate_beta(self, stock_returns, market_returns):
        """Calculate beta relative to market/portfolio"""
        try:
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            beta = covariance / market_variance if market_variance > 0 else 1.0
            return round(beta, 3)
        except:
            return 1.0

    def generate_portfolio_recommendations(self, annual_return, annual_volatility, avg_correlation, max_drawdown):
        """Generate portfolio optimization recommendations"""
        recommendations = []
        
        # Return analysis
        if annual_return < 0.05:  # Less than 5% annual return
            recommendations.append("Consider adding growth stocks or higher-yield assets")
        elif annual_return > 0.20:  # More than 20% annual return
            recommendations.append("Strong returns, but consider risk management")
        
        # Risk analysis
        if annual_volatility > 0.25:  # More than 25% volatility
            recommendations.append("High volatility detected - consider defensive positions")
        elif annual_volatility < 0.10:  # Less than 10% volatility
            recommendations.append("Conservative portfolio - consider growth opportunities")
        
        # Correlation analysis
        if avg_correlation > 0.7:
            recommendations.append("High correlation between holdings - diversify across sectors")
        elif avg_correlation < 0.3:
            recommendations.append("Well-diversified portfolio with low correlation")
        
        # Drawdown analysis
        if max_drawdown < -0.20:  # More than 20% drawdown
            recommendations.append("Significant drawdown risk - implement stop-loss strategies")
        
        if not recommendations:
            recommendations.append("Portfolio appears well-balanced")
        
        return recommendations

    def get_performance_metrics(self, user_id):
        """Get historical performance metrics for user portfolio"""
        try:
            # This would query the database for user's historical portfolio performance
            # For now, return sample metrics
            
            # Calculate time-based returns
            periods = ['1D', '1W', '1M', '3M', '1Y', 'YTD']
            performance = {}
            
            for period in periods:
                performance[period] = {
                    'return': np.random.uniform(-10, 15),  # Random sample data
                    'benchmark_return': np.random.uniform(-8, 12),
                    'alpha': np.random.uniform(-2, 3)
                }
            
            return {
                'user_id': user_id,
                'performance_by_period': performance,
                'total_trades': 45,
                'winning_trades': 28,
                'win_rate': 62.2,
                'average_win': 8.5,
                'average_loss': -4.2,
                'profit_factor': 2.02,
                'maximum_drawdown': -12.5,
                'calmar_ratio': 1.35,
                'information_ratio': 0.68,
                'tracking_error': 5.2,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting performance metrics: {str(e)}")
            raise

    def rebalance_portfolio(self, target_weights, current_holdings):
        """Calculate rebalancing recommendations"""
        try:
            rebalancing_actions = []
            
            # Calculate current total value
            total_value = sum(h['position_value'] for h in current_holdings)
            
            for ticker, target_weight in target_weights.items():
                # Find current holding
                current_holding = next((h for h in current_holdings if h['ticker'] == ticker), None)
                
                target_value = total_value * (target_weight / 100)
                current_value = current_holding['position_value'] if current_holding else 0
                difference = target_value - current_value
                
                if abs(difference) > total_value * 0.01:  # 1% threshold
                    action = 'BUY' if difference > 0 else 'SELL'
                    current_price = current_holding['current_price'] if current_holding else self.data_fetcher.get_real_time_price(ticker)['current_price']
                    shares_to_trade = abs(difference) / current_price
                    
                    rebalancing_actions.append({
                        'ticker': ticker,
                        'action': action,
                        'shares': round(shares_to_trade, 2),
                        'dollar_amount': abs(difference),
                        'current_weight': (current_value / total_value) * 100 if total_value > 0 else 0,
                        'target_weight': target_weight,
                        'difference': round((current_value / total_value) * 100 - target_weight, 2) if total_value > 0 else -target_weight
                    })
            
            return {
                'rebalancing_actions': rebalancing_actions,
                'total_portfolio_value': total_value,
                'estimated_transaction_cost': len(rebalancing_actions) * 9.95,  # Assume $9.95 per trade
                'recommendation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error calculating rebalancing: {str(e)}")
            raise

    def optimize_portfolio(self, tickers, risk_tolerance='moderate'):
        """Optimize portfolio allocation using mean reversion and risk parity concepts"""
        try:
            # Risk tolerance mappings
            risk_mappings = {
                'conservative': {'max_weight': 0.3, 'min_volatility': True},
                'moderate': {'max_weight': 0.4, 'min_volatility': False},
                'aggressive': {'max_weight': 0.6, 'min_volatility': False}
            }
            
            settings = risk_mappings.get(risk_tolerance, risk_mappings['moderate'])
            
            # Get historical data
            price_data = {}
            for ticker in tickers:
                try:
                    data = self.data_fetcher.get_historical_data(ticker, period='1y')
                    price_data[ticker] = data['Close']
                except:
                    continue
            
            if len(price_data) < 2:
                raise ValueError("Insufficient data for optimization")
            
            df = pd.DataFrame(price_data).dropna()
            returns = df.pct_change().dropna()
            
            # Calculate expected returns and covariance
            expected_returns = returns.mean() * 252  # Annualized
            cov_matrix = returns.cov() * 252  # Annualized
            
            # Simple equal-weight with risk adjustment
            num_assets = len(tickers)
            base_weight = 1.0 / num_assets
            
            # Adjust weights based on volatility (risk parity concept)
            volatilities = np.sqrt(np.diag(cov_matrix))
            inv_vol_weights = (1 / volatilities) / np.sum(1 / volatilities)
            
            # Blend equal weight with inverse volatility
            if settings['min_volatility']:
                optimized_weights = 0.3 * base_weight + 0.7 * inv_vol_weights
            else:
                optimized_weights = 0.6 * base_weight + 0.4 * inv_vol_weights
            
            # Apply maximum weight constraint
            max_weight = settings['max_weight']
            optimized_weights = np.minimum(optimized_weights, max_weight)
            optimized_weights = optimized_weights / np.sum(optimized_weights)  # Renormalize
            
            # Calculate portfolio metrics
            portfolio_return = np.sum(expected_returns * optimized_weights)
            portfolio_variance = np.dot(optimized_weights.T, np.dot(cov_matrix, optimized_weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Prepare results
            optimization_results = []
            for i, ticker in enumerate(df.columns):
                optimization_results.append({
                    'ticker': ticker,
                    'optimized_weight': round(optimized_weights[i] * 100, 2),
                    'expected_return': round(expected_returns[ticker] * 100, 2),
                    'volatility': round(volatilities[ticker] * 100, 2)
                })
            
            return {
                'optimization_results': optimization_results,
                'portfolio_metrics': {
                    'expected_return': round(portfolio_return * 100, 2),
                    'volatility': round(portfolio_volatility * 100, 2),
                    'sharpe_ratio': round(sharpe_ratio, 3)
                },
                'risk_tolerance': risk_tolerance,
                'optimization_method': 'Risk Parity with Volatility Adjustment',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Portfolio optimization error: {str(e)}")
            raise
