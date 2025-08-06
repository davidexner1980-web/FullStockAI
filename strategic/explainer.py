import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
from services.data_fetcher import DataFetcher
from utils.technical_indicators import TechnicalIndicators
from ml_models.predictor import MLPredictor
import json
import os

class MLExplainerWrapper:
    """Wrapper to provide explainability for ML models"""
    def __init__(self):
        self.feature_names = []
        self.feature_importance = []
    
    def fit(self, X, y):
        """Fit method for compatibility"""
        pass
    
    def explain_instance(self, instance, predict_fn, num_features=10):
        """Explain a single instance"""
        # Simple explanation based on feature values
        explanation = []
        for i, feature in enumerate(self.feature_names[:num_features]):
            value = instance[i] if len(instance) > i else 0
            explanation.append({
                'feature': feature,
                'value': float(value),
                'importance': float(self.feature_importance[i]) if len(self.feature_importance) > i else 0.1
            })
        return explanation

class AIExplainer:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.tech_indicators = TechnicalIndicators()
        self.ml_predictor = MLPredictor()
        self.explainer = MLExplainerWrapper()
        self.explanations_dir = 'data/explanations'
        os.makedirs(self.explanations_dir, exist_ok=True)
        
    def explain(self, ticker: str) -> Dict[str, Any]:
        """Generate comprehensive explanation for a ticker's prediction"""
        try:
            ticker = ticker.upper()
            
            # Get model predictions
            rf_prediction = self.ml_predictor.predict_random_forest(ticker)
            lstm_prediction = self.ml_predictor.predict_lstm(ticker)
            xgb_prediction = self.ml_predictor.predict_xgboost(ticker)
            
            # Get historical data for analysis
            data = self.data_fetcher.get_stock_data(ticker, period='3mo')
            if data is None or data.empty:
                return {'error': f'No data available for {ticker}'}
            
            # Generate explanations for each model
            explanations = {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'model_explanations': self._explain_all_models(ticker, rf_prediction, lstm_prediction, xgb_prediction),
                'feature_analysis': self._analyze_key_features(data),
                'market_context': self._provide_market_context(ticker, data),
                'risk_factors': self._identify_risk_factors(data),
                'confidence_analysis': self._analyze_confidence_levels(rf_prediction, lstm_prediction, xgb_prediction),
                'actionable_insights': self._generate_actionable_insights(ticker, data, rf_prediction, lstm_prediction, xgb_prediction),
                'scenario_analysis': self._perform_scenario_analysis(ticker, data)
            }
            
            # Store explanation
            self._store_explanation(explanations)
            
            return explanations
            
        except Exception as e:
            logging.error(f"AI explanation error for {ticker}: {str(e)}")
            return {'error': str(e)}
    
    def _explain_all_models(self, ticker: str, rf_pred: Dict, lstm_pred: Dict, xgb_pred: Dict) -> Dict[str, Any]:
        """Explain predictions from all models"""
        try:
            model_explanations = {}
            
            # Random Forest explanation
            if 'error' not in rf_pred:
                model_explanations['random_forest'] = {
                    'prediction': rf_pred.get('predicted_price', 0),
                    'confidence': rf_pred.get('confidence', 0),
                    'explanation': self._explain_random_forest(rf_pred),
                    'key_factors': rf_pred.get('features_used', [])[:5],
                    'model_reasoning': self._generate_rf_reasoning(rf_pred)
                }
            
            # LSTM explanation
            if 'error' not in lstm_pred:
                model_explanations['lstm'] = {
                    'prediction': lstm_pred.get('predicted_price', 0),
                    'confidence': lstm_pred.get('confidence', 0),
                    'explanation': self._explain_lstm(lstm_pred),
                    'pattern_recognition': self._describe_lstm_patterns(lstm_pred),
                    'model_reasoning': self._generate_lstm_reasoning(lstm_pred)
                }
            
            # XGBoost explanation
            if 'error' not in xgb_pred:
                model_explanations['xgboost'] = {
                    'prediction': xgb_pred.get('predicted_price', 0),
                    'confidence': xgb_pred.get('confidence', 0),
                    'explanation': self._explain_xgboost(xgb_pred),
                    'feature_importance': xgb_pred.get('feature_importance', []),
                    'model_reasoning': self._generate_xgb_reasoning(xgb_pred)
                }
            
            # Model consensus analysis
            consensus_analysis = self._analyze_model_consensus(model_explanations)
            
            return {
                'individual_models': model_explanations,
                'consensus_analysis': consensus_analysis,
                'recommendation_strength': self._calculate_recommendation_strength(model_explanations)
            }
            
        except Exception as e:
            logging.error(f"Model explanation error: {str(e)}")
            return {}
    
    def _explain_random_forest(self, prediction: Dict) -> str:
        """Generate explanation for Random Forest model"""
        confidence = prediction.get('confidence', 0)
        change_percent = prediction.get('change_percent', 0)
        
        if confidence > 80:
            confidence_desc = "very confident"
        elif confidence > 60:
            confidence_desc = "moderately confident"
        else:
            confidence_desc = "somewhat uncertain"
        
        direction = "increase" if change_percent > 0 else "decrease"
        
        return f"The Random Forest model is {confidence_desc} that the price will {direction} by {abs(change_percent):.1f}% based on historical patterns and technical indicators."
    
    def _explain_lstm(self, prediction: Dict) -> str:
        """Generate explanation for LSTM model"""
        confidence = prediction.get('confidence', 0)
        change_percent = prediction.get('change_percent', 0)
        
        direction = "upward" if change_percent > 0 else "downward"
        strength = "strong" if abs(change_percent) > 2 else "moderate" if abs(change_percent) > 1 else "weak"
        
        return f"The LSTM neural network detects a {strength} {direction} trend continuation with {confidence:.1f}% confidence, analyzing sequential price patterns over recent trading sessions."
    
    def _explain_xgboost(self, prediction: Dict) -> str:
        """Generate explanation for XGBoost model"""
        confidence = prediction.get('confidence', 0)
        change_percent = prediction.get('change_percent', 0)
        feature_importance = prediction.get('feature_importance', [])
        
        direction = "positive" if change_percent > 0 else "negative"
        top_feature = feature_importance[0]['feature'] if feature_importance else "technical indicators"
        
        return f"XGBoost predicts a {direction} move with {confidence:.1f}% confidence, with {top_feature} being the most influential factor in this prediction."
    
    def _generate_rf_reasoning(self, prediction: Dict) -> str:
        """Generate reasoning for Random Forest prediction"""
        features = prediction.get('features_used', [])
        signal = prediction.get('signal', 'HOLD')
        
        reasoning = f"Random Forest generated a {signal} signal by analyzing {len(features)} technical features. "
        reasoning += "The model combines multiple decision trees to create a robust prediction based on "
        reasoning += "price patterns, volume trends, and momentum indicators."
        
        return reasoning
    
    def _generate_lstm_reasoning(self, prediction: Dict) -> str:
        """Generate reasoning for LSTM prediction"""
        change_percent = prediction.get('change_percent', 0)
        
        reasoning = "The LSTM model processes sequential price data through neural network layers, "
        reasoning += "capturing complex temporal patterns and dependencies. "
        
        if abs(change_percent) > 2:
            reasoning += "The model detected strong momentum patterns suggesting continued price movement."
        else:
            reasoning += "The model indicates consolidation with modest directional bias."
        
        return reasoning
    
    def _generate_xgb_reasoning(self, prediction: Dict) -> str:
        """Generate reasoning for XGBoost prediction"""
        feature_importance = prediction.get('feature_importance', [])
        
        reasoning = "XGBoost uses gradient boosting to iteratively improve predictions, "
        reasoning += "focusing on features that provide the most predictive power. "
        
        if feature_importance:
            top_features = [f['feature'] for f in feature_importance[:3]]
            reasoning += f"Key drivers include: {', '.join(top_features)}."
        
        return reasoning
    
    def _describe_lstm_patterns(self, prediction: Dict) -> str:
        """Describe patterns recognized by LSTM"""
        change_percent = prediction.get('change_percent', 0)
        
        if abs(change_percent) > 3:
            return "Strong momentum pattern detected with clear directional bias"
        elif abs(change_percent) > 1:
            return "Moderate trend pattern with consistent directional movement"
        else:
            return "Consolidation pattern with sideways price action"
    
    def _analyze_key_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze key features influencing predictions"""
        try:
            current_price = data['Close'].iloc[-1]
            
            # Calculate key technical indicators
            features = {
                'price_momentum': {
                    'value': ((current_price / data['Close'].iloc[-11] - 1) * 100),
                    'interpretation': self._interpret_momentum(((current_price / data['Close'].iloc[-11] - 1) * 100)),
                    'importance': 'High'
                },
                'volume_trend': {
                    'value': (data['Volume'].tail(5).mean() / data['Volume'].tail(20).mean()),
                    'interpretation': self._interpret_volume_trend(data['Volume'].tail(5).mean() / data['Volume'].tail(20).mean()),
                    'importance': 'Medium'
                },
                'volatility': {
                    'value': (data['Close'].pct_change().tail(20).std() * np.sqrt(252) * 100),
                    'interpretation': self._interpret_volatility(data['Close'].pct_change().tail(20).std() * np.sqrt(252) * 100),
                    'importance': 'High'
                },
                'rsi': {
                    'value': self.tech_indicators.calculate_rsi(data['Close']).iloc[-1],
                    'interpretation': self._interpret_rsi(self.tech_indicators.calculate_rsi(data['Close']).iloc[-1]),
                    'importance': 'Medium'
                },
                'trend_strength': {
                    'value': self.tech_indicators.calculate_trend_strength(data['Close']),
                    'interpretation': self._interpret_trend_strength(self.tech_indicators.calculate_trend_strength(data['Close'])),
                    'importance': 'High'
                }
            }
            
            return features
            
        except Exception as e:
            logging.error(f"Feature analysis error: {str(e)}")
            return {}
    
    def _interpret_momentum(self, momentum: float) -> str:
        """Interpret price momentum"""
        if momentum > 5:
            return "Strong upward momentum"
        elif momentum > 2:
            return "Moderate upward momentum"
        elif momentum > -2:
            return "Sideways momentum"
        elif momentum > -5:
            return "Moderate downward momentum"
        else:
            return "Strong downward momentum"
    
    def _interpret_volume_trend(self, ratio: float) -> str:
        """Interpret volume trend"""
        if ratio > 1.5:
            return "Significantly above average volume"
        elif ratio > 1.2:
            return "Above average volume"
        elif ratio > 0.8:
            return "Normal volume levels"
        else:
            return "Below average volume"
    
    def _interpret_volatility(self, volatility: float) -> str:
        """Interpret volatility levels"""
        if volatility > 40:
            return "Very high volatility"
        elif volatility > 25:
            return "High volatility"
        elif volatility > 15:
            return "Moderate volatility"
        else:
            return "Low volatility"
    
    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI levels"""
        if rsi > 70:
            return "Overbought condition"
        elif rsi > 50:
            return "Bullish momentum"
        elif rsi > 30:
            return "Bearish momentum"
        else:
            return "Oversold condition"
    
    def _interpret_trend_strength(self, strength: float) -> str:
        """Interpret trend strength"""
        if abs(strength) > 0.7:
            return "Strong trend" + (" (upward)" if strength > 0 else " (downward)")
        elif abs(strength) > 0.4:
            return "Moderate trend" + (" (upward)" if strength > 0 else " (downward)")
        else:
            return "Weak or sideways trend"
    
    def _provide_market_context(self, ticker: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Provide market context for the prediction"""
        try:
            # Get market indices data for context
            market_data = self.data_fetcher.get_market_indices()
            
            current_price = data['Close'].iloc[-1]
            high_52w = data['High'].tail(252).max() if len(data) >= 252 else data['High'].max()
            low_52w = data['Low'].tail(252).min() if len(data) >= 252 else data['Low'].min()
            
            # Calculate position in 52-week range
            range_position = (current_price - low_52w) / (high_52w - low_52w) * 100
            
            context = {
                'market_environment': self._assess_market_environment(market_data),
                'stock_position': {
                    'vs_52w_high': ((current_price / high_52w - 1) * 100),
                    'vs_52w_low': ((current_price / low_52w - 1) * 100),
                    'range_position': range_position,
                    'interpretation': self._interpret_range_position(range_position)
                },
                'sector_performance': "Analysis requires sector data",  # Would need sector classification
                'correlation_analysis': self._analyze_market_correlation(ticker, data, market_data)
            }
            
            return context
            
        except Exception as e:
            logging.error(f"Market context error: {str(e)}")
            return {}
    
    def _assess_market_environment(self, market_data: Dict) -> str:
        """Assess overall market environment"""
        if not market_data:
            return "Market environment assessment unavailable"
        
        positive_indices = 0
        total_indices = 0
        
        for index_data in market_data.values():
            if 'change_percent' in index_data:
                total_indices += 1
                if index_data['change_percent'] > 0:
                    positive_indices += 1
        
        if total_indices == 0:
            return "Market environment assessment unavailable"
        
        positive_ratio = positive_indices / total_indices
        
        if positive_ratio >= 0.75:
            return "Strong bullish market environment"
        elif positive_ratio >= 0.5:
            return "Mixed to positive market environment"
        elif positive_ratio >= 0.25:
            return "Mixed to negative market environment"
        else:
            return "Bearish market environment"
    
    def _interpret_range_position(self, position: float) -> str:
        """Interpret position within 52-week range"""
        if position > 90:
            return "Near 52-week high"
        elif position > 70:
            return "In upper range"
        elif position > 30:
            return "In middle range"
        elif position > 10:
            return "In lower range"
        else:
            return "Near 52-week low"
    
    def _analyze_market_correlation(self, ticker: str, data: pd.DataFrame, market_data: Dict) -> str:
        """Analyze correlation with market indices"""
        try:
            # Simplified correlation analysis
            recent_change = (data['Close'].iloc[-1] / data['Close'].iloc[-6] - 1) * 100
            
            # Compare with SPY if available
            spy_data = market_data.get('SPY', {})
            if 'change_percent' in spy_data:
                spy_change = spy_data['change_percent']
                if abs(recent_change - spy_change) < 1:
                    return "Highly correlated with market"
                elif abs(recent_change - spy_change) < 3:
                    return "Moderately correlated with market"
                else:
                    return "Low correlation with market - independent movement"
            
            return "Market correlation analysis unavailable"
            
        except Exception as e:
            logging.error(f"Correlation analysis error: {str(e)}")
            return "Correlation analysis error"
    
    def _identify_risk_factors(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify key risk factors"""
        risks = []
        
        try:
            # Volatility risk
            volatility = data['Close'].pct_change().tail(20).std() * np.sqrt(252) * 100
            if volatility > 30:
                risks.append({
                    'type': 'High Volatility',
                    'level': 'High',
                    'description': f'Stock shows high volatility ({volatility:.1f}%), indicating increased price uncertainty'
                })
            
            # Volume risk
            recent_volume = data['Volume'].tail(5).mean()
            avg_volume = data['Volume'].mean()
            if recent_volume < avg_volume * 0.5:
                risks.append({
                    'type': 'Low Volume',
                    'level': 'Medium',
                    'description': 'Recent trading volume is significantly below average, reducing liquidity'
                })
            
            # Gap risk
            gaps = (data['Open'] - data['Close'].shift(1)) / data['Close'].shift(1)
            recent_gaps = gaps.tail(10)
            if recent_gaps.abs().max() > 0.03:
                risks.append({
                    'type': 'Gap Risk',
                    'level': 'Medium',
                    'description': 'Recent price gaps indicate potential news-driven volatility'
                })
            
            # Trend consistency risk
            trend_strength = self.tech_indicators.calculate_trend_strength(data['Close'])
            if abs(trend_strength) < 0.3:
                risks.append({
                    'type': 'Weak Trend',
                    'level': 'Low',
                    'description': 'Weak trend strength suggests potential direction uncertainty'
                })
            
            return risks
            
        except Exception as e:
            logging.error(f"Risk factor identification error: {str(e)}")
            return []
    
    def _analyze_confidence_levels(self, rf_pred: Dict, lstm_pred: Dict, xgb_pred: Dict) -> Dict[str, Any]:
        """Analyze confidence levels across models"""
        try:
            confidences = []
            predictions = []
            
            if 'error' not in rf_pred:
                confidences.append(rf_pred.get('confidence', 0))
                predictions.append(rf_pred.get('predicted_price', 0))
            
            if 'error' not in lstm_pred:
                confidences.append(lstm_pred.get('confidence', 0))
                predictions.append(lstm_pred.get('predicted_price', 0))
            
            if 'error' not in xgb_pred:
                confidences.append(xgb_pred.get('confidence', 0))
                predictions.append(xgb_pred.get('predicted_price', 0))
            
            if not confidences:
                return {'error': 'No confidence data available'}
            
            avg_confidence = np.mean(confidences)
            confidence_std = np.std(confidences) if len(confidences) > 1 else 0
            prediction_std = np.std(predictions) if len(predictions) > 1 else 0
            prediction_mean = np.mean(predictions) if predictions else 0
            
            analysis = {
                'average_confidence': round(avg_confidence, 1),
                'confidence_consistency': 'High' if confidence_std < 10 else 'Medium' if confidence_std < 20 else 'Low',
                'prediction_agreement': 'High' if prediction_std < (prediction_mean * 0.02) else 'Medium' if prediction_std < (prediction_mean * 0.05) else 'Low',
                'overall_reliability': self._assess_overall_reliability(avg_confidence, confidence_std, prediction_std, prediction_mean),
                'confidence_range': f"{min(confidences):.1f}% - {max(confidences):.1f}%"
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"Confidence analysis error: {str(e)}")
            return {}
    
    def _assess_overall_reliability(self, avg_conf: float, conf_std: float, pred_std: float, pred_mean: float) -> str:
        """Assess overall reliability of predictions"""
        reliability_score = 0
        
        # High average confidence increases reliability
        if avg_conf > 80:
            reliability_score += 3
        elif avg_conf > 60:
            reliability_score += 2
        elif avg_conf > 40:
            reliability_score += 1
        
        # Low confidence variance increases reliability
        if conf_std < 10:
            reliability_score += 2
        elif conf_std < 20:
            reliability_score += 1
        
        # Low prediction variance increases reliability
        if pred_mean > 0 and pred_std < (pred_mean * 0.02):
            reliability_score += 2
        elif pred_mean > 0 and pred_std < (pred_mean * 0.05):
            reliability_score += 1
        
        if reliability_score >= 6:
            return "Very High"
        elif reliability_score >= 4:
            return "High"
        elif reliability_score >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _analyze_model_consensus(self, model_explanations: Dict) -> Dict[str, Any]:
        """Analyze consensus among models"""
        try:
            models = model_explanations
            if not models:
                return {}
            
            predictions = []
            confidences = []
            signals = []
            
            for model_name, model_data in models.items():
                if 'prediction' in model_data:
                    predictions.append(model_data['prediction'])
                    confidences.append(model_data['confidence'])
                    
                    # Determine signal based on current vs predicted price
                    if model_data['prediction'] > model_data.get('current_price', model_data['prediction']):
                        signals.append('BUY')
                    else:
                        signals.append('SELL')
            
            if not predictions:
                return {}
            
            # Calculate consensus metrics
            pred_std = np.std(predictions)
            pred_mean = np.mean(predictions)
            agreement_pct = (1 - pred_std / pred_mean) * 100 if pred_mean > 0 else 0
            
            # Signal consensus
            buy_votes = signals.count('BUY')
            sell_votes = signals.count('SELL')
            consensus_signal = 'BUY' if buy_votes > sell_votes else 'SELL' if sell_votes > buy_votes else 'HOLD'
            
            return {
                'price_agreement_pct': round(max(0, agreement_pct), 1),
                'consensus_signal': consensus_signal,
                'signal_strength': f"{max(buy_votes, sell_votes)}/{len(signals)}",
                'average_confidence': round(np.mean(confidences), 1),
                'prediction_range': {
                    'min': round(min(predictions), 2),
                    'max': round(max(predictions), 2),
                    'avg': round(pred_mean, 2)
                }
            }
            
        except Exception as e:
            logging.error(f"Model consensus analysis error: {str(e)}")
            return {}
    
    def _calculate_recommendation_strength(self, model_explanations: Dict) -> str:
        """Calculate overall recommendation strength"""
        try:
            if not model_explanations:
                return "Insufficient data"
            
            total_confidence = 0
            model_count = 0
            agreement_score = 0
            
            predictions = []
            for model_data in model_explanations.values():
                if 'confidence' in model_data:
                    total_confidence += model_data['confidence']
                    model_count += 1
                    predictions.append(model_data.get('prediction', 0))
            
            if model_count == 0:
                return "No confidence data"
            
            avg_confidence = total_confidence / model_count
            
            # Calculate agreement (inverse of standard deviation)
            if len(predictions) > 1:
                pred_std = np.std(predictions)
                pred_mean = np.mean(predictions)
                agreement_score = (1 - pred_std / pred_mean) * 100 if pred_mean > 0 else 0
            else:
                agreement_score = 100  # Perfect agreement with one model
            
            # Combine confidence and agreement
            strength_score = (avg_confidence + agreement_score) / 2
            
            if strength_score > 80:
                return "Very Strong"
            elif strength_score > 65:
                return "Strong"
            elif strength_score > 50:
                return "Moderate"
            elif strength_score > 35:
                return "Weak"
            else:
                return "Very Weak"
                
        except Exception as e:
            logging.error(f"Recommendation strength calculation error: {str(e)}")
            return "Unknown"
    
    def _generate_actionable_insights(self, ticker: str, data: pd.DataFrame, rf_pred: Dict, lstm_pred: Dict, xgb_pred: Dict) -> List[str]:
        """Generate actionable insights for traders"""
        insights = []
        
        try:
            current_price = data['Close'].iloc[-1]
            
            # Price level insights
            predictions = []
            if 'error' not in rf_pred:
                predictions.append(rf_pred.get('predicted_price', 0))
            if 'error' not in lstm_pred:
                predictions.append(lstm_pred.get('predicted_price', 0))
            if 'error' not in xgb_pred:
                predictions.append(xgb_pred.get('predicted_price', 0))
            
            if predictions:
                avg_prediction = np.mean(predictions)
                expected_change = ((avg_prediction / current_price - 1) * 100)
                
                if expected_change > 2:
                    insights.append(f"Models suggest upside potential of {expected_change:.1f}% - consider long positions")
                elif expected_change < -2:
                    insights.append(f"Models indicate downside risk of {abs(expected_change):.1f}% - consider defensive positions")
                else:
                    insights.append("Models suggest limited price movement - consider range-bound strategies")
            
            # Volume insights
            recent_volume = data['Volume'].tail(5).mean()
            avg_volume = data['Volume'].mean()
            if recent_volume > avg_volume * 1.5:
                insights.append("Elevated volume suggests increased institutional interest - monitor for breakouts")
            elif recent_volume < avg_volume * 0.7:
                insights.append("Low volume may indicate limited conviction - wait for volume confirmation")
            
            # Volatility insights
            volatility = data['Close'].pct_change().tail(20).std() * np.sqrt(252) * 100
            if volatility > 30:
                insights.append("High volatility creates opportunity for swing trades but increases risk")
            elif volatility < 15:
                insights.append("Low volatility environment - consider selling options strategies")
            
            # Technical level insights
            high_52w = data['High'].tail(252).max() if len(data) >= 252 else data['High'].max()
            low_52w = data['Low'].tail(252).min() if len(data) >= 252 else data['Low'].min()
            
            if current_price > high_52w * 0.95:
                insights.append("Price near 52-week high - monitor for resistance or breakout")
            elif current_price < low_52w * 1.05:
                insights.append("Price near 52-week low - potential value opportunity with risk management")
            
            # RSI insights
            rsi = self.tech_indicators.calculate_rsi(data['Close']).iloc[-1]
            if rsi > 70:
                insights.append("Overbought conditions - consider profit-taking or wait for pullback")
            elif rsi < 30:
                insights.append("Oversold conditions - potential buying opportunity with proper risk management")
            
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            logging.error(f"Actionable insights error: {str(e)}")
            return ["Analysis completed - review individual model predictions for trading decisions"]
    
    def _perform_scenario_analysis(self, ticker: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Perform scenario analysis for different market conditions"""
        try:
            current_price = data['Close'].iloc[-1]
            volatility = data['Close'].pct_change().tail(20).std()
            
            scenarios = {
                'bull_market': {
                    'probability': 0.3,
                    'expected_return': 0.15,
                    'price_target': current_price * 1.15,
                    'description': "Strong market rally with increased risk appetite"
                },
                'normal_market': {
                    'probability': 0.4,
                    'expected_return': 0.03,
                    'price_target': current_price * 1.03,
                    'description': "Stable market conditions with normal volatility"
                },
                'bear_market': {
                    'probability': 0.3,
                    'expected_return': -0.12,
                    'price_target': current_price * 0.88,
                    'description': "Market decline with increased volatility and risk aversion"
                }
            }
            
            # Adjust probabilities based on current market conditions
            recent_trend = (data['Close'].iloc[-1] / data['Close'].iloc[-21] - 1)
            if recent_trend > 0.05:
                scenarios['bull_market']['probability'] += 0.1
                scenarios['bear_market']['probability'] -= 0.1
            elif recent_trend < -0.05:
                scenarios['bear_market']['probability'] += 0.1
                scenarios['bull_market']['probability'] -= 0.1
            
            # Calculate expected value
            expected_value = sum(
                scenario['expected_return'] * scenario['probability'] 
                for scenario in scenarios.values()
            )
            
            return {
                'scenarios': scenarios,
                'expected_value': round(expected_value * 100, 1),
                'risk_reward_ratio': self._calculate_risk_reward(scenarios),
                'recommended_strategy': self._recommend_strategy_for_scenarios(scenarios)
            }
            
        except Exception as e:
            logging.error(f"Scenario analysis error: {str(e)}")
            return {}
    
    def _calculate_risk_reward(self, scenarios: Dict) -> float:
        """Calculate risk-reward ratio from scenarios"""
        try:
            upside = scenarios['bull_market']['expected_return'] * scenarios['bull_market']['probability']
            downside = abs(scenarios['bear_market']['expected_return']) * scenarios['bear_market']['probability']
            
            if downside > 0:
                return round(upside / downside, 2)
            else:
                return float('inf')
                
        except Exception as e:
            logging.error(f"Risk-reward calculation error: {str(e)}")
            return 1.0
    
    def _recommend_strategy_for_scenarios(self, scenarios: Dict) -> str:
        """Recommend strategy based on scenario analysis"""
        try:
            bull_prob = scenarios['bull_market']['probability']
            bear_prob = scenarios['bear_market']['probability']
            
            if bull_prob > 0.4:
                return "Aggressive growth strategy - consider call options or leveraged positions"
            elif bear_prob > 0.4:
                return "Defensive strategy - consider puts, cash positions, or defensive sectors"
            else:
                return "Balanced strategy - consider straddles, covered calls, or diversified positions"
                
        except Exception as e:
            logging.error(f"Strategy recommendation error: {str(e)}")
            return "Balanced approach recommended"
    
    def _store_explanation(self, explanation: Dict[str, Any]):
        """Store explanation for future reference"""
        try:
            ticker = explanation['ticker']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"explanation_{ticker}_{timestamp}.json"
            filepath = os.path.join(self.explanations_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(explanation, f, indent=2)
                
            # Clean up old explanations (keep last 50)
            files = sorted([f for f in os.listdir(self.explanations_dir) if f.startswith('explanation_')], reverse=True)
            for old_file in files[50:]:
                try:
                    os.remove(os.path.join(self.explanations_dir, old_file))
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Explanation storage error: {str(e)}")
    
    def get_explanation_summary(self, ticker: str) -> Dict[str, Any]:
        """Get a simplified explanation summary"""
        try:
            full_explanation = self.explain(ticker)
            
            if 'error' in full_explanation:
                return full_explanation
            
            # Create simplified summary
            summary = {
                'ticker': ticker,
                'overall_signal': self._determine_overall_signal(full_explanation),
                'confidence_level': full_explanation.get('confidence_analysis', {}).get('average_confidence', 0),
                'key_insights': full_explanation.get('actionable_insights', [])[:3],
                'main_risks': [risk['description'] for risk in full_explanation.get('risk_factors', [])[:2]],
                'recommendation': self._generate_simple_recommendation(full_explanation)
            }
            
            return summary
            
        except Exception as e:
            logging.error(f"Explanation summary error: {str(e)}")
            return {'error': str(e)}
    
    def _determine_overall_signal(self, explanation: Dict) -> str:
        """Determine overall trading signal from explanation"""
        try:
            consensus = explanation.get('model_explanations', {}).get('consensus_analysis', {})
            return consensus.get('consensus_signal', 'HOLD')
        except:
            return 'HOLD'
    
    def _generate_simple_recommendation(self, explanation: Dict) -> str:
        """Generate simple trading recommendation"""
        try:
            signal = self._determine_overall_signal(explanation)
            confidence = explanation.get('confidence_analysis', {}).get('average_confidence', 0)
            
            if signal == 'BUY' and confidence > 70:
                return "Strong buy recommendation with high confidence"
            elif signal == 'BUY':
                return "Moderate buy recommendation - consider position sizing"
            elif signal == 'SELL' and confidence > 70:
                return "Strong sell recommendation with high confidence"
            elif signal == 'SELL':
                return "Moderate sell recommendation - consider risk management"
            else:
                return "Hold or wait for better risk-reward opportunity"
                
        except Exception as e:
            logging.error(f"Simple recommendation error: {str(e)}")
            return "Insufficient data for recommendation"
