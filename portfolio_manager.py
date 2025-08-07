import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.data_fetcher import DataFetcher
from ml_models import MLModelManager
from backend.crypto_predictor import CryptoPredictorEngine
import logging
import json

class PortfolioManager:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.ml_manager = MLModelManager()
        self.crypto_predictor = CryptoPredictorEngine()
        
    def calculate_portfolio_metrics(self, holdings):
        """Calculate comprehensive portfolio metrics"""
        try:
            if not holdings:
                return self.empty_portfolio_metrics()
            
            total_value = 0
            total_cost = 0
            positions = []
            
            for holding in holdings:
                symbol = holding.get('symbol', '')
                quantity = float(holding.get('quantity', 0))
                avg_cost = float(holding.get('average_cost', 0))
                asset_type = holding.get('asset_type', 'stock')
                
                # Get current price
                if asset_type == 'crypto':
                    df = self.data_fetcher.get_crypto_data(symbol, period='1d')
                else:
                    df = self.data_fetcher.get_stock_data(symbol, period='1d')
                
                if not df.empty:
                    current_price = df['Close'].iloc[-1]
                    position_value = quantity * current_price
                    position_cost = quantity * avg_cost
                    
                    total_value += position_value
                    total_cost += position_cost
                    
                    positions.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'avg_cost': avg_cost,
                        'current_price': current_price,
                        'position_value': position_value,
                        'position_cost': position_cost,
                        'unrealized_pnl': position_value - position_cost,
                        'unrealized_pnl_percent': ((position_value - position_cost) / position_cost * 100) if position_cost > 0 else 0,
                        'weight': 0  # Will calculate after getting total
                    })
            
            # Calculate weights
            for position in positions:
                position['weight'] = (position['position_value'] / total_value * 100) if total_value > 0 else 0
            
            # Calculate portfolio-level metrics
            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(positions)
            
            return {
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percent': round(total_pnl_percent, 2),
                'positions': positions,
                'risk_metrics': risk_metrics,
                'diversification_score': self.calculate_diversification_score(positions),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Portfolio metrics calculation error: {str(e)}")
            return self.empty_portfolio_metrics()

    def calculate_risk_metrics(self, positions):
        """Calculate portfolio risk metrics"""
        try:
            if not positions:
                return {'volatility': 0, 'beta': 1, 'sharpe_ratio': 0, 'max_drawdown': 0}
            
            # Get historical returns for each position
            returns_data = {}
            weights = {}
            
            for position in positions:
                symbol = position['symbol']
                weight = position['weight'] / 100
                weights[symbol] = weight
                
                # Get 30 days of data for risk calculation
                df = self.data_fetcher.get_stock_data(symbol, period='30d')
                if not df.empty:
                    returns = df['Close'].pct_change().dropna()
                    returns_data[symbol] = returns
            
            if not returns_data:
                return {'volatility': 0, 'beta': 1, 'sharpe_ratio': 0, 'max_drawdown': 0}
            
            # Calculate portfolio returns
            portfolio_returns = pd.Series(0, index=list(returns_data.values())[0].index)
            
            for symbol, returns in returns_data.items():
                weight = weights.get(symbol, 0)
                portfolio_returns += returns * weight
            
            # Portfolio volatility (annualized)
            portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Portfolio beta (vs SPY)
            spy_data = self.data_fetcher.get_stock_data('SPY', period='30d')
            if not spy_data.empty:
                spy_returns = spy_data['Close'].pct_change().dropna()
                # Align indices
                common_dates = portfolio_returns.index.intersection(spy_returns.index)
                if len(common_dates) > 10:
                    portfolio_aligned = portfolio_returns.loc[common_dates]
                    spy_aligned = spy_returns.loc[common_dates]
                    covariance = np.cov(portfolio_aligned, spy_aligned)[0][1]
                    spy_variance = spy_aligned.var()
                    beta = covariance / spy_variance if spy_variance != 0 else 1
                else:
                    beta = 1
            else:
                beta = 1
            
            # Sharpe ratio (simplified, assuming risk-free rate of 2%)
            risk_free_rate = 0.02
            excess_return = portfolio_returns.mean() * 252 - risk_free_rate
            sharpe_ratio = excess_return / portfolio_volatility if portfolio_volatility != 0 else 0
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            return {
                'volatility': round(portfolio_volatility * 100, 2),
                'beta': round(beta, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown * 100, 2)
            }
        except Exception as e:
            logging.error(f"Risk metrics calculation error: {str(e)}")
            return {'volatility': 0, 'beta': 1, 'sharpe_ratio': 0, 'max_drawdown': 0}

    def calculate_diversification_score(self, positions):
        """Calculate portfolio diversification score (0-100)"""
        try:
            if not positions:
                return 0
            
            # Factor in number of positions
            num_positions = len(positions)
            position_score = min(50, num_positions * 5)  # Max 50 points for 10+ positions
            
            # Factor in weight distribution (penalize concentration)
            weights = [pos['weight'] for pos in positions]
            weight_concentration = max(weights) if weights else 100
            concentration_penalty = weight_concentration - 20  # Penalty if any position > 20%
            concentration_score = max(0, 50 - max(0, concentration_penalty))
            
            # Sector diversification (simplified - based on different asset types)
            asset_types = set(pos.get('asset_type', 'stock') for pos in positions)
            asset_diversity_score = len(asset_types) * 10  # 10 points per asset type
            
            total_score = min(100, position_score + concentration_score + asset_diversity_score)
            
            return round(total_score, 1)
        except Exception as e:
            logging.error(f"Diversification score calculation error: {str(e)}")
            return 50

    def get_portfolio_predictions(self, holdings):
        """Get predictions for all holdings in portfolio"""
        try:
            predictions = []
            
            for holding in holdings:
                symbol = holding.get('symbol', '')
                asset_type = holding.get('asset_type', 'stock')
                quantity = float(holding.get('quantity', 0))
                
                try:
                    if asset_type == 'crypto':
                        prediction = self.crypto_predictor.predict(symbol)
                    else:
                        prediction = self.ml_manager.predict_random_forest(symbol)
                    
                    # Calculate impact on portfolio
                    current_value = quantity * prediction['current_price']
                    predicted_value = quantity * prediction['predicted_price']
                    impact = predicted_value - current_value
                    
                    predictions.append({
                        'symbol': symbol,
                        'asset_type': asset_type,
                        'current_price': prediction['current_price'],
                        'predicted_price': prediction['predicted_price'],
                        'price_change_percent': prediction['price_change_percent'],
                        'confidence': prediction['confidence'],
                        'quantity': quantity,
                        'current_value': round(current_value, 2),
                        'predicted_value': round(predicted_value, 2),
                        'impact': round(impact, 2)
                    })
                except Exception as e:
                    logging.error(f"Prediction error for {symbol}: {str(e)}")
                    # Add placeholder with current data
                    df = self.data_fetcher.get_stock_data(symbol, period='1d')
                    current_price = df['Close'].iloc[-1] if not df.empty else 0
                    current_value = quantity * current_price
                    
                    predictions.append({
                        'symbol': symbol,
                        'asset_type': asset_type,
                        'current_price': current_price,
                        'predicted_price': current_price,
                        'price_change_percent': 0,
                        'confidence': 0,
                        'quantity': quantity,
                        'current_value': round(current_value, 2),
                        'predicted_value': round(current_value, 2),
                        'impact': 0,
                        'error': 'Prediction unavailable'
                    })
            
            # Calculate total portfolio impact
            total_current = sum(p['current_value'] for p in predictions)
            total_predicted = sum(p['predicted_value'] for p in predictions)
            total_impact = total_predicted - total_current
            total_impact_percent = (total_impact / total_current * 100) if total_current > 0 else 0
            
            return {
                'predictions': predictions,
                'portfolio_summary': {
                    'total_current_value': round(total_current, 2),
                    'total_predicted_value': round(total_predicted, 2),
                    'total_impact': round(total_impact, 2),
                    'total_impact_percent': round(total_impact_percent, 2)
                }
            }
        except Exception as e:
            logging.error(f"Portfolio predictions error: {str(e)}")
            return {'predictions': [], 'portfolio_summary': {}}

    def suggest_rebalancing(self, holdings, target_allocation=None):
        """Suggest portfolio rebalancing"""
        try:
            if not holdings:
                return {'suggestions': [], 'reasoning': 'No holdings to rebalance'}
            
            current_metrics = self.calculate_portfolio_metrics(holdings)
            positions = current_metrics['positions']
            
            suggestions = []
            
            # Check for over-concentration
            for position in positions:
                if position['weight'] > 25:  # Over 25% in single position
                    suggestions.append({
                        'type': 'reduce',
                        'symbol': position['symbol'],
                        'current_weight': position['weight'],
                        'suggested_weight': 20,
                        'reason': 'Reduce concentration risk',
                        'priority': 'high'
                    })
            
            # Check for under-diversification
            if len(positions) < 5:
                suggestions.append({
                    'type': 'diversify',
                    'reason': 'Consider adding more positions for better diversification',
                    'suggested_count': 8,
                    'priority': 'medium'
                })
            
            # Check for poor performers
            for position in positions:
                if position['unrealized_pnl_percent'] < -20:
                    suggestions.append({
                        'type': 'review',
                        'symbol': position['symbol'],
                        'current_loss': position['unrealized_pnl_percent'],
                        'reason': 'Significant unrealized loss - consider stop-loss',
                        'priority': 'medium'
                    })
            
            # Asset type diversification
            asset_types = {}
            for position in positions:
                asset_type = position.get('asset_type', 'stock')
                asset_types[asset_type] = asset_types.get(asset_type, 0) + position['weight']
            
            if asset_types.get('stock', 0) > 80:
                suggestions.append({
                    'type': 'diversify_assets',
                    'reason': 'Consider adding crypto or other asset types',
                    'current_allocation': asset_types,
                    'priority': 'low'
                })
            
            return {
                'suggestions': suggestions,
                'current_metrics': current_metrics,
                'diversification_score': current_metrics['diversification_score']
            }
        except Exception as e:
            logging.error(f"Rebalancing suggestions error: {str(e)}")
            return {'suggestions': [], 'reasoning': 'Error calculating suggestions'}

    def calculate_correlation_matrix(self, symbols):
        """Calculate correlation matrix for portfolio symbols"""
        try:
            if len(symbols) < 2:
                return {}
            
            returns_data = {}
            
            # Get 60 days of data for correlation calculation
            for symbol in symbols:
                df = self.data_fetcher.get_stock_data(symbol, period='60d')
                if not df.empty:
                    returns = df['Close'].pct_change().dropna()
                    returns_data[symbol] = returns
            
            if len(returns_data) < 2:
                return {}
            
            # Create correlation matrix
            correlations = {}
            symbols_list = list(returns_data.keys())
            
            for i, symbol1 in enumerate(symbols_list):
                correlations[symbol1] = {}
                for symbol2 in symbols_list:
                    if symbol1 == symbol2:
                        correlations[symbol1][symbol2] = 1.0
                    else:
                        # Align the series and calculate correlation
                        s1 = returns_data[symbol1]
                        s2 = returns_data[symbol2]
                        common_dates = s1.index.intersection(s2.index)
                        
                        if len(common_dates) > 20:
                            corr = s1.loc[common_dates].corr(s2.loc[common_dates])
                            correlations[symbol1][symbol2] = round(corr, 3) if not np.isnan(corr) else 0
                        else:
                            correlations[symbol1][symbol2] = 0
            
            return correlations
        except Exception as e:
            logging.error(f"Correlation matrix calculation error: {str(e)}")
            return {}

    def empty_portfolio_metrics(self):
        """Return empty portfolio metrics structure"""
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_pnl': 0,
            'total_pnl_percent': 0,
            'positions': [],
            'risk_metrics': {'volatility': 0, 'beta': 1, 'sharpe_ratio': 0, 'max_drawdown': 0},
            'diversification_score': 0,
            'last_updated': datetime.now().isoformat()
        }

    def get_portfolio_performance_history(self, holdings, days=30):
        """Calculate historical portfolio performance"""
        try:
            if not holdings:
                return {'dates': [], 'values': [], 'returns': []}
            
            # Get date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            portfolio_values = {}
            dates = []
            
            # Calculate portfolio value for each day
            for holding in holdings:
                symbol = holding.get('symbol', '')
                quantity = float(holding.get('quantity', 0))
                
                df = self.data_fetcher.get_stock_data(symbol, period=f'{days+5}d')
                if not df.empty:
                    for date, row in df.iterrows():
                        date_str = date.strftime('%Y-%m-%d')
                        if date_str not in portfolio_values:
                            portfolio_values[date_str] = 0
                            if date_str not in dates:
                                dates.append(date_str)
                        
                        portfolio_values[date_str] += quantity * row['Close']
            
            # Sort dates and calculate returns
            dates.sort()
            values = [portfolio_values[date] for date in dates]
            returns = []
            
            for i in range(1, len(values)):
                daily_return = ((values[i] - values[i-1]) / values[i-1]) * 100 if values[i-1] > 0 else 0
                returns.append(round(daily_return, 2))
            
            return {
                'dates': dates,
                'values': [round(v, 2) for v in values],
                'returns': returns,
                'total_return': round(((values[-1] - values[0]) / values[0]) * 100, 2) if len(values) > 1 and values[0] > 0 else 0
            }
        except Exception as e:
            logging.error(f"Portfolio performance history error: {str(e)}")
            return {'dates': [], 'values': [], 'returns': [], 'total_return': 0}

