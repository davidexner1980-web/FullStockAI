import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from services.data_fetcher import DataFetcher
from services.ml_models import MLModelManager
from services.oracle_service import OracleService
import json
import os
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import yfinance as yf

class PortfolioAnalyzer:
    """Advanced Portfolio Analysis and Optimization Engine"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.ml_manager = MLModelManager()
        self.oracle_service = OracleService()
        self.scaler = StandardScaler()
        
        # Risk-free rate assumption
        self.risk_free_rate = 0.02  # 2% annual
        
        # Portfolio optimization constraints
        self.min_weight = 0.01  # 1% minimum allocation
        self.max_weight = 0.4   # 40% maximum single position
    
    def analyze_portfolio(self, tickers, weights=None):
        """Comprehensive portfolio analysis with ML predictions"""
        try:
            if not tickers:
                return {'error': 'No tickers provided for analysis'}
            
            # Validate and normalize weights
            if weights is None:
                weights = [1.0 / len(tickers)] * len(tickers)  # Equal weights
            elif len(weights) != len(tickers):
                return {'error': 'Number of weights must match number of tickers'}
            
            # Normalize weights to sum to 1
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            # Get individual stock predictions and data
            stock_analyses = {}
            price_data = {}
            
            for i, ticker in enumerate(tickers):
                try:
                    # Get stock data
                    data = self.data_fetcher.get_stock_data(ticker, period='1y')
                    if data is None:
                        continue
                    
                    price_data[ticker] = data['Close']
                    
                    # Get ML predictions
                    rf_pred = self.ml_manager.predict_random_forest(data)
                    lstm_pred = self.ml_manager.predict_lstm(data)
                    xgb_pred = self.ml_manager.predict_xgboost(data)
                    
                    # Calculate ensemble prediction
                    predictions = []
                    confidences = []
                    
                    for pred in [rf_pred, lstm_pred, xgb_pred]:
                        if 'prediction' in pred:
                            predictions.append(pred['prediction'])
                            confidences.append(pred['confidence'])
                    
                    if predictions:
                        ensemble_pred = np.mean(predictions)
                        ensemble_conf = np.mean(confidences)
                        
                        current_price = data['Close'].iloc[-1]
                        expected_return = (ensemble_pred - current_price) / current_price
                        
                        stock_analyses[ticker] = {
                            'weight': weights[i],
                            'current_price': float(current_price),
                            'predicted_price': float(ensemble_pred),
                            'expected_return': float(expected_return),
                            'confidence': float(ensemble_conf),
                            'individual_predictions': {
                                'random_forest': rf_pred,
                                'lstm': lstm_pred,
                                'xgboost': xgb_pred
                            }
                        }
                    
                except Exception as e:
                    logging.warning(f"Failed to analyze {ticker}: {str(e)}")
                    continue
            
            if not stock_analyses:
                return {'error': 'Failed to analyze any stocks in portfolio'}
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(stock_analyses, price_data)
            
            # Correlation analysis
            correlation_matrix = self._calculate_correlation_matrix(price_data)
            
            # Risk analysis
            risk_analysis = self._analyze_portfolio_risk(stock_analyses, correlation_matrix, price_data)
            
            # Optimization suggestions
            optimization = self._suggest_portfolio_optimization(stock_analyses, correlation_matrix)
            
            # Hedging recommendations
            hedging = self._generate_hedging_recommendations(stock_analyses, portfolio_metrics)
            
            # Oracle portfolio synthesis
            oracle_synthesis = self._generate_oracle_portfolio_synthesis(stock_analyses)
            
            # Performance projections
            performance_projections = self._project_portfolio_performance(stock_analyses, price_data)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'portfolio_composition': stock_analyses,
                'portfolio_metrics': portfolio_metrics,
                'correlation_analysis': correlation_matrix,
                'risk_analysis': risk_analysis,
                'optimization_suggestions': optimization,
                'hedging_recommendations': hedging,
                'oracle_synthesis': oracle_synthesis,
                'performance_projections': performance_projections,
                'diversification_score': self._calculate_diversification_score(correlation_matrix, weights),
                'portfolio_health': self._assess_portfolio_health(stock_analyses, risk_analysis)
            }
            
        except Exception as e:
            logging.error(f"Error in portfolio analysis: {str(e)}")
            return {'error': f'Portfolio analysis failed: {str(e)}'}
    
    def _calculate_portfolio_metrics(self, stock_analyses, price_data):
        """Calculate comprehensive portfolio metrics"""
        try:
            weights = [analysis['weight'] for analysis in stock_analyses.values()]
            expected_returns = [analysis['expected_return'] for analysis in stock_analyses.values()]
            confidences = [analysis['confidence'] for analysis in stock_analyses.values()]
            
            # Portfolio expected return
            portfolio_return = sum(w * r for w, r in zip(weights, expected_returns))
            
            # Portfolio confidence (weighted average)
            portfolio_confidence = sum(w * c for w, c in zip(weights, confidences))
            
            # Calculate historical volatility for each stock
            stock_volatilities = {}
            for ticker in stock_analyses.keys():
                if ticker in price_data:
                    returns = price_data[ticker].pct_change().dropna()
                    stock_volatilities[ticker] = returns.std() * np.sqrt(252)  # Annualized
            
            # Portfolio volatility (simplified - assuming some correlation)
            if stock_volatilities:
                weighted_volatilities = []
                for ticker, analysis in stock_analyses.items():
                    if ticker in stock_volatilities:
                        weighted_volatilities.append(analysis['weight'] * stock_volatilities[ticker])
                
                # Simplified portfolio volatility (actual calculation would need full covariance matrix)
                portfolio_volatility = np.sqrt(sum(v**2 for v in weighted_volatilities))
            else:
                portfolio_volatility = 0.0
            
            # Sharpe ratio
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            # Risk-adjusted return
            risk_adjusted_return = portfolio_return / (1 + portfolio_volatility) if portfolio_volatility > 0 else portfolio_return
            
            return {
                'expected_return': float(portfolio_return),
                'expected_volatility': float(portfolio_volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'risk_adjusted_return': float(risk_adjusted_return),
                'portfolio_confidence': float(portfolio_confidence),
                'number_of_positions': len(stock_analyses),
                'total_weight': sum(weights),
                'largest_position': max(weights) if weights else 0,
                'concentration_risk': 'HIGH' if max(weights) > 0.3 else 'MEDIUM' if max(weights) > 0.2 else 'LOW'
            }
            
        except Exception as e:
            logging.error(f"Error calculating portfolio metrics: {str(e)}")
            return {'error': 'Failed to calculate portfolio metrics'}
    
    def _calculate_correlation_matrix(self, price_data):
        """Calculate correlation matrix for portfolio stocks"""
        try:
            if len(price_data) < 2:
                return {'error': 'Need at least 2 stocks for correlation analysis'}
            
            # Align price data by date
            df = pd.DataFrame(price_data)
            df = df.dropna()
            
            if df.empty:
                return {'error': 'No overlapping price data found'}
            
            # Calculate returns
            returns = df.pct_change().dropna()
            
            # Calculate correlation matrix
            correlation_matrix = returns.corr()
            
            # Convert to dictionary format
            corr_dict = {}
            for ticker1 in correlation_matrix.columns:
                corr_dict[ticker1] = {}
                for ticker2 in correlation_matrix.columns:
                    corr_dict[ticker1][ticker2] = float(correlation_matrix.loc[ticker1, ticker2])
            
            # Calculate average correlation
            correlations = []
            tickers = list(correlation_matrix.columns)
            for i in range(len(tickers)):
                for j in range(i+1, len(tickers)):
                    correlations.append(correlation_matrix.loc[tickers[i], tickers[j]])
            
            avg_correlation = np.mean(correlations) if correlations else 0
            
            return {
                'correlation_matrix': corr_dict,
                'average_correlation': float(avg_correlation),
                'correlation_interpretation': self._interpret_correlation(avg_correlation),
                'highly_correlated_pairs': self._find_high_correlations(correlation_matrix)
            }
            
        except Exception as e:
            logging.error(f"Error calculating correlation matrix: {str(e)}")
            return {'error': 'Correlation calculation failed'}
    
    def _interpret_correlation(self, avg_correlation):
        """Interpret average portfolio correlation"""
        if avg_correlation > 0.8:
            return "Very high correlation - portfolio lacks diversification"
        elif avg_correlation > 0.6:
            return "High correlation - consider adding uncorrelated assets"
        elif avg_correlation > 0.3:
            return "Moderate correlation - reasonable diversification"
        elif avg_correlation > 0:
            return "Low correlation - good diversification"
        else:
            return "Negative correlation - excellent risk mitigation"
    
    def _find_high_correlations(self, correlation_matrix):
        """Find highly correlated stock pairs"""
        high_corr_pairs = []
        tickers = list(correlation_matrix.columns)
        
        for i in range(len(tickers)):
            for j in range(i+1, len(tickers)):
                corr = correlation_matrix.loc[tickers[i], tickers[j]]
                if abs(corr) > 0.7:  # High correlation threshold
                    high_corr_pairs.append({
                        'ticker1': tickers[i],
                        'ticker2': tickers[j],
                        'correlation': float(corr),
                        'relationship': 'strongly positive' if corr > 0.7 else 'strongly negative'
                    })
        
        return high_corr_pairs
    
    def _analyze_portfolio_risk(self, stock_analyses, correlation_matrix, price_data):
        """Comprehensive portfolio risk analysis"""
        try:
            risk_factors = {
                'concentration_risk': self._assess_concentration_risk(stock_analyses),
                'correlation_risk': self._assess_correlation_risk(correlation_matrix),
                'volatility_risk': self._assess_volatility_risk(stock_analyses, price_data),
                'prediction_risk': self._assess_prediction_risk(stock_analyses),
                'sector_risk': self._assess_sector_risk(stock_analyses)
            }
            
            # Calculate overall risk score (0-100, higher = riskier)
            risk_scores = []
            for risk_type, risk_data in risk_factors.items():
                if isinstance(risk_data, dict) and 'risk_score' in risk_data:
                    risk_scores.append(risk_data['risk_score'])
            
            overall_risk_score = np.mean(risk_scores) if risk_scores else 50
            
            # Risk categorization
            if overall_risk_score > 70:
                risk_level = 'HIGH'
            elif overall_risk_score > 40:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'overall_risk_score': float(overall_risk_score),
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'risk_recommendations': self._generate_risk_recommendations(risk_factors),
                'value_at_risk_estimates': self._calculate_var_estimates(stock_analyses, price_data)
            }
            
        except Exception as e:
            logging.error(f"Error in risk analysis: {str(e)}")
            return {'error': 'Risk analysis failed'}
    
    def _assess_concentration_risk(self, stock_analyses):
        """Assess concentration risk in portfolio"""
        weights = [analysis['weight'] for analysis in stock_analyses.values()]
        max_weight = max(weights) if weights else 0
        
        # Calculate Herfindahl Index (concentration measure)
        hhi = sum(w**2 for w in weights)
        
        if max_weight > 0.4 or hhi > 0.25:
            risk_score = 80
            assessment = "High concentration risk detected"
        elif max_weight > 0.25 or hhi > 0.15:
            risk_score = 50
            assessment = "Moderate concentration risk"
        else:
            risk_score = 20
            assessment = "Well diversified portfolio"
        
        return {
            'risk_score': risk_score,
            'assessment': assessment,
            'largest_position_weight': float(max_weight),
            'herfindahl_index': float(hhi),
            'recommendation': 'Consider reducing large positions' if risk_score > 60 else 'Concentration levels acceptable'
        }
    
    def _assess_correlation_risk(self, correlation_matrix):
        """Assess correlation risk"""
        if 'average_correlation' not in correlation_matrix:
            return {'risk_score': 50, 'assessment': 'Cannot assess correlation risk'}
        
        avg_corr = correlation_matrix['average_correlation']
        
        if avg_corr > 0.7:
            risk_score = 90
            assessment = "Very high correlation increases portfolio risk"
        elif avg_corr > 0.5:
            risk_score = 60
            assessment = "High correlation reduces diversification benefits"
        elif avg_corr > 0.3:
            risk_score = 30
            assessment = "Moderate correlation - acceptable diversification"
        else:
            risk_score = 10
            assessment = "Low correlation provides good diversification"
        
        return {
            'risk_score': risk_score,
            'assessment': assessment,
            'average_correlation': float(avg_corr)
        }
    
    def _assess_volatility_risk(self, stock_analyses, price_data):
        """Assess volatility risk"""
        volatilities = []
        
        for ticker in stock_analyses.keys():
            if ticker in price_data:
                returns = price_data[ticker].pct_change().dropna()
                if len(returns) > 20:
                    vol = returns.std() * np.sqrt(252)  # Annualized
                    volatilities.append(vol)
        
        if not volatilities:
            return {'risk_score': 50, 'assessment': 'Cannot assess volatility risk'}
        
        avg_volatility = np.mean(volatilities)
        max_volatility = max(volatilities)
        
        if avg_volatility > 0.4:
            risk_score = 80
            assessment = "High volatility portfolio"
        elif avg_volatility > 0.25:
            risk_score = 50
            assessment = "Moderate volatility portfolio"
        else:
            risk_score = 20
            assessment = "Low volatility portfolio"
        
        return {
            'risk_score': risk_score,
            'assessment': assessment,
            'average_volatility': float(avg_volatility),
            'maximum_volatility': float(max_volatility)
        }
    
    def _assess_prediction_risk(self, stock_analyses):
        """Assess risk from prediction uncertainty"""
        confidences = [analysis['confidence'] for analysis in stock_analyses.values()]
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        # Lower confidence = higher risk
        risk_score = (1 - avg_confidence) * 100
        
        if avg_confidence < 0.5:
            assessment = "Low prediction confidence increases uncertainty"
        elif avg_confidence < 0.7:
            assessment = "Moderate prediction confidence"
        else:
            assessment = "High prediction confidence"
        
        return {
            'risk_score': risk_score,
            'assessment': assessment,
            'average_confidence': float(avg_confidence)
        }
    
    def _assess_sector_risk(self, stock_analyses):
        """Assess sector concentration risk (simplified)"""
        # This is a simplified assessment - in a full implementation,
        # you would map tickers to sectors using external data
        
        num_stocks = len(stock_analyses)
        
        if num_stocks < 3:
            risk_score = 70
            assessment = "Few positions increase sector concentration risk"
        elif num_stocks < 6:
            risk_score = 40
            assessment = "Moderate number of positions"
        else:
            risk_score = 20
            assessment = "Good number of positions for diversification"
        
        return {
            'risk_score': risk_score,
            'assessment': assessment,
            'number_of_positions': num_stocks
        }
    
    def _generate_risk_recommendations(self, risk_factors):
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        for risk_type, risk_data in risk_factors.items():
            if isinstance(risk_data, dict) and risk_data.get('risk_score', 0) > 60:
                if risk_type == 'concentration_risk':
                    recommendations.append("Reduce position sizes to improve diversification")
                elif risk_type == 'correlation_risk':
                    recommendations.append("Add assets from different sectors or asset classes")
                elif risk_type == 'volatility_risk':
                    recommendations.append("Consider adding lower volatility assets to reduce overall risk")
                elif risk_type == 'prediction_risk':
                    recommendations.append("Use smaller position sizes when prediction confidence is low")
                elif risk_type == 'sector_risk':
                    recommendations.append("Diversify across more sectors and industries")
        
        if not recommendations:
            recommendations.append("Portfolio risk profile is acceptable - maintain current diversification")
        
        return recommendations
    
    def _calculate_var_estimates(self, stock_analyses, price_data):
        """Calculate Value at Risk estimates"""
        try:
            portfolio_returns = []
            
            # Calculate portfolio returns for each day
            common_dates = None
            for ticker in stock_analyses.keys():
                if ticker in price_data:
                    if common_dates is None:
                        common_dates = price_data[ticker].index
                    else:
                        common_dates = common_dates.intersection(price_data[ticker].index)
            
            if common_dates is None or len(common_dates) < 30:
                return {'error': 'Insufficient data for VaR calculation'}
            
            for date in common_dates:
                daily_return = 0
                for ticker, analysis in stock_analyses.items():
                    if ticker in price_data:
                        try:
                            price_series = price_data[ticker]
                            if date in price_series.index:
                                prev_date_idx = price_series.index.get_loc(date) - 1
                                if prev_date_idx >= 0:
                                    prev_price = price_series.iloc[prev_date_idx]
                                    curr_price = price_series.loc[date]
                                    stock_return = (curr_price - prev_price) / prev_price
                                    daily_return += analysis['weight'] * stock_return
                        except:
                            continue
                
                if daily_return != 0:
                    portfolio_returns.append(daily_return)
            
            if len(portfolio_returns) < 30:
                return {'error': 'Insufficient portfolio return data'}
            
            portfolio_returns = np.array(portfolio_returns)
            
            # Calculate VaR at different confidence levels
            var_95 = np.percentile(portfolio_returns, 5)  # 95% VaR
            var_99 = np.percentile(portfolio_returns, 1)  # 99% VaR
            
            # Calculate Conditional VaR (Expected Shortfall)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            return {
                'var_95_daily': float(var_95),
                'var_99_daily': float(var_99),
                'cvar_95_daily': float(cvar_95),
                'var_95_annual': float(var_95 * np.sqrt(252)),
                'var_99_annual': float(var_99 * np.sqrt(252)),
                'portfolio_volatility': float(portfolio_returns.std() * np.sqrt(252))
            }
            
        except Exception as e:
            logging.error(f"Error calculating VaR: {str(e)}")
            return {'error': 'VaR calculation failed'}
    
    def _suggest_portfolio_optimization(self, stock_analyses, correlation_matrix):
        """Suggest portfolio optimization improvements"""
        try:
            suggestions = []
            
            # Weight optimization suggestions
            weights = [analysis['weight'] for analysis in stock_analyses.values()]
            expected_returns = [analysis['expected_return'] for analysis in stock_analyses.values()]
            
            # Find overweight/underweight positions
            for ticker, analysis in stock_analyses.items():
                if analysis['weight'] > 0.3:
                    suggestions.append(f"Consider reducing {ticker} position (currently {analysis['weight']:.1%})")
                elif analysis['weight'] < 0.05 and analysis['expected_return'] > 0.1:
                    suggestions.append(f"Consider increasing {ticker} position - high expected return with low weight")
            
            # Correlation-based suggestions
            if 'highly_correlated_pairs' in correlation_matrix:
                for pair in correlation_matrix['highly_correlated_pairs']:
                    if pair['correlation'] > 0.8:
                        suggestions.append(f"High correlation between {pair['ticker1']} and {pair['ticker2']} - consider diversifying")
            
            # Expected return optimization
            if expected_returns:
                best_performer = max(stock_analyses.items(), key=lambda x: x[1]['expected_return'])
                worst_performer = min(stock_analyses.items(), key=lambda x: x[1]['expected_return'])
                
                if best_performer[1]['expected_return'] > 0.15 and best_performer[1]['weight'] < 0.2:
                    suggestions.append(f"Consider increasing allocation to {best_performer[0]} - highest expected return")
                
                if worst_performer[1]['expected_return'] < -0.1:
                    suggestions.append(f"Consider reducing allocation to {worst_performer[0]} - negative expected return")
            
            # Diversification suggestions
            if len(stock_analyses) < 5:
                suggestions.append("Consider adding more positions to improve diversification")
            elif len(stock_analyses) > 15:
                suggestions.append("Consider consolidating positions - portfolio may be over-diversified")
            
            return {
                'optimization_suggestions': suggestions if suggestions else ["Portfolio allocation appears well-balanced"],
                'rebalancing_frequency': "Consider rebalancing quarterly or when allocations drift >5% from target",
                'optimal_portfolio_size': "5-12 positions for optimal risk-return balance"
            }
            
        except Exception as e:
            logging.error(f"Error in portfolio optimization: {str(e)}")
            return {'error': 'Optimization analysis failed'}
    
    def _generate_hedging_recommendations(self, stock_analyses, portfolio_metrics):
        """Generate hedging recommendations"""
        try:
            hedging_strategies = []
            
            # Market hedge recommendations
            if portfolio_metrics.get('expected_volatility', 0) > 0.25:
                hedging_strategies.append({
                    'strategy': 'Market Hedge',
                    'recommendation': 'Consider SPY puts or VIX calls to hedge market risk',
                    'reason': 'High portfolio volatility detected'
                })
            
            # Sector hedge recommendations
            portfolio_return = portfolio_metrics.get('expected_return', 0)
            if portfolio_return > 0.2:
                hedging_strategies.append({
                    'strategy': 'Profit Protection',
                    'recommendation': 'Consider protective puts on largest positions',
                    'reason': 'High expected returns may warrant downside protection'
                })
            
            # Correlation hedge
            if len(stock_analyses) > 2:
                confidences = [analysis['confidence'] for analysis in stock_analyses.values()]
                if np.mean(confidences) < 0.6:
                    hedging_strategies.append({
                        'strategy': 'Uncertainty Hedge',
                        'recommendation': 'Consider reducing position sizes or adding defensive assets',
                        'reason': 'Low prediction confidence increases uncertainty'
                    })
            
            # Currency hedge (if applicable)
            # This would be more relevant for international portfolios
            
            return {
                'hedging_strategies': hedging_strategies if hedging_strategies else [
                    {'strategy': 'No Hedge Needed', 'recommendation': 'Portfolio risk profile acceptable', 'reason': 'Balanced risk exposure'}
                ],
                'hedge_ratio_suggestion': min(0.3, portfolio_metrics.get('expected_volatility', 0.2)),
                'hedging_instruments': ['SPY puts', 'VIX calls', 'Individual stock puts', 'Inverse ETFs']
            }
            
        except Exception as e:
            logging.error(f"Error generating hedging recommendations: {str(e)}")
            return {'error': 'Hedging analysis failed'}
    
    def _generate_oracle_portfolio_synthesis(self, stock_analyses):
        """Generate Oracle's mystical portfolio synthesis"""
        try:
            # Calculate portfolio energy
            total_confidence = sum(analysis['confidence'] for analysis in stock_analyses.values())
            avg_confidence = total_confidence / len(stock_analyses)
            
            total_expected_return = sum(analysis['expected_return'] * analysis['weight'] 
                                      for analysis in stock_analyses.values())
            
            # Oracle emotional state for portfolio
            if avg_confidence > 0.8 and total_expected_return > 0.15:
                oracle_state = 'EUPHORIA'
                synthesis = "The cosmic winds favor this portfolio! Golden threads of prosperity weave through each position."
            elif avg_confidence > 0.6 and total_expected_return > 0.05:
                oracle_state = 'SERENITY'
                synthesis = "Balanced energies flow through this portfolio, suggesting steady progress on the path of abundance."
            elif avg_confidence < 0.4 or total_expected_return < -0.05:
                oracle_state = 'CONTEMPLATION'
                synthesis = "The Oracle perceives shadows and uncertainty. Meditation and patience are required."
            else:
                oracle_state = 'WONDER'
                synthesis = "Mixed energies dance through this portfolio. The future holds both challenges and opportunities."
            
            # Individual stock Oracle insights
            stock_insights = {}
            for ticker, analysis in stock_analyses.items():
                if analysis['expected_return'] > 0.1:
                    stock_insights[ticker] = f"🔥 {ticker} burns with the fire of potential growth"
                elif analysis['expected_return'] < -0.05:
                    stock_insights[ticker] = f"🌊 {ticker} flows through turbulent waters requiring careful navigation"
                else:
                    stock_insights[ticker] = f"⚖️ {ticker} maintains cosmic balance between risk and reward"
            
            # Portfolio blessing/warning
            blessing = self._generate_portfolio_blessing(oracle_state, len(stock_analyses))
            
            return {
                'oracle_state': oracle_state,
                'portfolio_synthesis': synthesis,
                'individual_insights': stock_insights,
                'cosmic_blessing': blessing,
                'energy_level': float(avg_confidence),
                'prosperity_potential': 'HIGH' if total_expected_return > 0.1 else 'MEDIUM' if total_expected_return > 0 else 'LOW',
                'divine_guidance': self._channel_portfolio_guidance(oracle_state)
            }
            
        except Exception as e:
            logging.error(f"Error in Oracle synthesis: {str(e)}")
            return {'error': 'Oracle connection disrupted'}
    
    def _generate_portfolio_blessing(self, oracle_state, num_positions):
        """Generate Oracle blessing for portfolio"""
        if oracle_state == 'EUPHORIA':
            return f"May the {num_positions} pillars of your portfolio stand firm against the storms of uncertainty, bearing fruit in all seasons."
        elif oracle_state == 'SERENITY':
            return f"The Oracle blesses this {num_positions}-fold path of investment with steady growth and peaceful slumber."
        elif oracle_state == 'CONTEMPLATION':
            return f"In times of uncertainty, the wise investor contemplates deeply. May wisdom guide your {num_positions} choices."
        else:
            return f"The journey of {num_positions} investments begins with a single step. May each step be guided by divine wisdom."
    
    def _channel_portfolio_guidance(self, oracle_state):
        """Channel Oracle guidance for portfolio management"""
        guidance = {
            'EUPHORIA': "Ride the waves of prosperity but remember - even the highest tide must recede. Prepare for all seasons.",
            'SERENITY': "In stillness lies strength. Your portfolio reflects inner harmony. Maintain this balance through all market weather.",
            'CONTEMPLATION': "The Oracle sees multiple paths before you. Sometimes the best action is thoughtful inaction. Wait for clarity.",
            'WONDER': "Mystery surrounds your portfolio like morning mist. As the sun rises, so too will understanding come."
        }
        return guidance.get(oracle_state, "Trust in the process of conscious investing.")
    
    def _project_portfolio_performance(self, stock_analyses, price_data):
        """Project portfolio performance scenarios"""
        try:
            # Base case (ML predictions)
            base_case_return = sum(analysis['expected_return'] * analysis['weight'] 
                                 for analysis in stock_analyses.values())
            
            # Bull case (predictions * 1.5)
            bull_case_return = base_case_return * 1.5
            
            # Bear case (predictions * 0.5, but negative returns * 1.5)
            bear_case_return = base_case_return * (0.5 if base_case_return > 0 else 1.5)
            
            # Calculate scenario probabilities based on confidence
            avg_confidence = np.mean([analysis['confidence'] for analysis in stock_analyses.values()])
            
            base_probability = avg_confidence
            bull_probability = avg_confidence * 0.3
            bear_probability = (1 - avg_confidence) * 0.7
            
            # Time horizon projections
            time_horizons = [30, 90, 365]  # days
            projections = {}
            
            for days in time_horizons:
                # Adjust returns for time horizon (simplified)
                time_factor = days / 365
                
                projections[f"{days}_days"] = {
                    'bull_case': {
                        'return': float(bull_case_return * time_factor),
                        'probability': float(bull_probability)
                    },
                    'base_case': {
                        'return': float(base_case_return * time_factor),
                        'probability': float(base_probability)
                    },
                    'bear_case': {
                        'return': float(bear_case_return * time_factor),
                        'probability': float(bear_probability)
                    },
                    'expected_value': float((
                        bull_case_return * time_factor * bull_probability +
                        base_case_return * time_factor * base_probability +
                        bear_case_return * time_factor * bear_probability
                    ))
                }
            
            return {
                'scenario_analysis': projections,
                'key_assumptions': [
                    "ML predictions materialize as expected",
                    "Market conditions remain similar to training data",
                    "No major external shocks or black swan events",
                    "Portfolio weights remain constant (no rebalancing)"
                ],
                'confidence_in_projections': float(avg_confidence)
            }
            
        except Exception as e:
            logging.error(f"Error projecting performance: {str(e)}")
            return {'error': 'Performance projection failed'}
    
    def _calculate_diversification_score(self, correlation_matrix, weights):
        """Calculate portfolio diversification score (0-100)"""
        try:
            if 'average_correlation' not in correlation_matrix:
                return 50  # Default score
            
            avg_correlation = correlation_matrix['average_correlation']
            
            # Lower correlation = higher diversification
            correlation_score = (1 - avg_correlation) * 100
            
            # Weight distribution score
            weight_entropy = -sum(w * np.log(w) for w in weights if w > 0)
            max_entropy = np.log(len(weights))
            weight_score = (weight_entropy / max_entropy) * 100 if max_entropy > 0 else 0
            
            # Combined diversification score
            diversification_score = (correlation_score * 0.6 + weight_score * 0.4)
            
            return float(max(0, min(100, diversification_score)))
            
        except Exception as e:
            logging.error(f"Error calculating diversification score: {str(e)}")
            return 50.0
    
    def _assess_portfolio_health(self, stock_analyses, risk_analysis):
        """Assess overall portfolio health"""
        try:
            health_factors = []
            
            # Diversification health
            num_positions = len(stock_analyses)
            if 5 <= num_positions <= 12:
                health_factors.append(('diversification', 'GOOD', 'Optimal number of positions'))
            elif num_positions < 5:
                health_factors.append(('diversification', 'POOR', 'Too few positions - concentration risk'))
            else:
                health_factors.append(('diversification', 'FAIR', 'Many positions - may be over-diversified'))
            
            # Risk health
            risk_score = risk_analysis.get('overall_risk_score', 50)
            if risk_score < 40:
                health_factors.append(('risk', 'GOOD', 'Well-managed risk profile'))
            elif risk_score < 70:
                health_factors.append(('risk', 'FAIR', 'Moderate risk levels'))
            else:
                health_factors.append(('risk', 'POOR', 'High risk - consider risk reduction'))
            
            # Return potential health
            expected_returns = [analysis['expected_return'] for analysis in stock_analyses.values()]
            avg_return = np.mean(expected_returns) if expected_returns else 0
            
            if avg_return > 0.1:
                health_factors.append(('returns', 'GOOD', 'Strong return potential'))
            elif avg_return > 0:
                health_factors.append(('returns', 'FAIR', 'Modest return potential'))
            else:
                health_factors.append(('returns', 'POOR', 'Negative return expectations'))
            
            # Confidence health
            confidences = [analysis['confidence'] for analysis in stock_analyses.values()]
            avg_confidence = np.mean(confidences) if confidences else 0.5
            
            if avg_confidence > 0.7:
                health_factors.append(('confidence', 'GOOD', 'High prediction confidence'))
            elif avg_confidence > 0.5:
                health_factors.append(('confidence', 'FAIR', 'Moderate prediction confidence'))
            else:
                health_factors.append(('confidence', 'POOR', 'Low prediction confidence'))
            
            # Calculate overall health score
            good_count = sum(1 for _, status, _ in health_factors if status == 'GOOD')
            fair_count = sum(1 for _, status, _ in health_factors if status == 'FAIR')
            poor_count = sum(1 for _, status, _ in health_factors if status == 'POOR')
            
            total_factors = len(health_factors)
            health_score = (good_count * 100 + fair_count * 60 + poor_count * 20) / total_factors
            
            if health_score >= 80:
                overall_health = 'EXCELLENT'
            elif health_score >= 65:
                overall_health = 'GOOD'
            elif health_score >= 50:
                overall_health = 'FAIR'
            else:
                overall_health = 'POOR'
            
            return {
                'overall_health': overall_health,
                'health_score': float(health_score),
                'health_factors': [
                    {'category': cat, 'status': status, 'description': desc}
                    for cat, status, desc in health_factors
                ],
                'improvement_priority': self._prioritize_improvements(health_factors)
            }
            
        except Exception as e:
            logging.error(f"Error assessing portfolio health: {str(e)}")
            return {'error': 'Health assessment failed'}
    
    def _prioritize_improvements(self, health_factors):
        """Prioritize portfolio improvements"""
        poor_factors = [factor for factor in health_factors if factor[1] == 'POOR']
        
        if not poor_factors:
            return "Portfolio health is good - focus on regular monitoring and rebalancing"
        
        priority_map = {
            'risk': 'Reduce portfolio risk through diversification or position sizing',
            'diversification': 'Improve diversification by adding/removing positions',
            'confidence': 'Focus on higher-confidence predictions or reduce position sizes',
            'returns': 'Review position selection and consider higher-return opportunities'
        }
        
        priorities = [priority_map.get(factor[0], f"Improve {factor[0]}") for factor in poor_factors]
        return priorities[0] if priorities else "Continue current strategy"
