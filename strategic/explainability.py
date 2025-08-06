import numpy as np
import pandas as pd
import logging
from datetime import datetime
from services.data_fetcher import DataFetcher
from services.ml_models import MLModelManager
import json
import os

class ExplainabilityService:
    """AI Explainability-as-a-Service for transparent predictions"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.ml_manager = MLModelManager()
        self.explanations_cache = {}
        
        # Feature importance categories
        self.feature_categories = {
            'technical_indicators': ['RSI', 'MACD', 'MACD_Signal', 'Stoch_K', 'Stoch_D', 'Williams_R'],
            'moving_averages': ['SMA_20', 'SMA_50', 'EMA_12', 'EMA_26'],
            'volatility_indicators': ['BB_Upper', 'BB_Lower', 'ATR', 'Volatility'],
            'volume_indicators': ['OBV', 'AD', 'Volume_Ratio'],
            'momentum_indicators': ['MOM', 'ROC'],
            'price_action': ['Price_Change', 'Support', 'Resistance']
        }
        
        # Explanation templates
        self.explanation_templates = {
            'bullish': {
                'high_confidence': "Strong bullish signals detected with high confidence.",
                'medium_confidence': "Moderate bullish indicators present.",
                'low_confidence': "Weak bullish signals with uncertainty."
            },
            'bearish': {
                'high_confidence': "Strong bearish signals detected with high confidence.",
                'medium_confidence': "Moderate bearish indicators present.",
                'low_confidence': "Weak bearish signals with uncertainty."
            },
            'neutral': {
                'high_confidence': "Conflicting signals result in neutral outlook.",
                'medium_confidence': "Mixed indicators suggest sideways movement.",
                'low_confidence': "Unclear market direction with low confidence."
            }
        }
    
    def explain_prediction(self, ticker):
        """Generate comprehensive explanation for prediction"""
        try:
            # Get data and predictions
            data = self.data_fetcher.get_stock_data(ticker)
            if data is None:
                return {'error': 'Failed to fetch data for explanation'}
            
            # Get predictions from all models
            rf_prediction = self.ml_manager.predict_random_forest(data)
            lstm_prediction = self.ml_manager.predict_lstm(data)
            xgb_prediction = self.ml_manager.predict_xgboost(data)
            
            # Get trading signals
            trading_signals = self.ml_manager.get_trading_signals(data)
            
            # Analyze feature importance
            feature_analysis = self._analyze_feature_importance(data, rf_prediction)
            
            # Generate model-specific explanations
            model_explanations = self._generate_model_explanations(
                rf_prediction, lstm_prediction, xgb_prediction, data
            )
            
            # Analyze prediction factors
            prediction_factors = self._analyze_prediction_factors(data, trading_signals)
            
            # Generate human-readable explanation
            human_explanation = self._generate_human_explanation(
                ticker, data, feature_analysis, model_explanations, prediction_factors
            )
            
            # Calculate explanation confidence
            explanation_confidence = self._calculate_explanation_confidence(
                rf_prediction, lstm_prediction, xgb_prediction
            )
            
            # Generate strategy alignment
            strategy_alignment = self._analyze_strategy_alignment(trading_signals)
            
            explanation = {
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat(),
                'explanation_confidence': explanation_confidence,
                'human_explanation': human_explanation,
                'model_explanations': model_explanations,
                'feature_analysis': feature_analysis,
                'prediction_factors': prediction_factors,
                'strategy_alignment': strategy_alignment,
                'key_insights': self._generate_key_insights(data, feature_analysis),
                'risk_factors': self._identify_risk_factors(data, prediction_factors),
                'confidence_breakdown': self._breakdown_confidence_sources(
                    rf_prediction, lstm_prediction, xgb_prediction
                )
            }
            
            # Cache explanation
            self.explanations_cache[ticker] = explanation
            
            return explanation
            
        except Exception as e:
            logging.error(f"Error explaining prediction for {ticker}: {str(e)}")
            return {'error': f'Explanation failed: {str(e)}'}
    
    def _analyze_feature_importance(self, data, rf_prediction):
        """Analyze feature importance from Random Forest model"""
        try:
            if 'error' in rf_prediction or self.ml_manager.models['random_forest'] is None:
                return {'error': 'Random Forest model not available'}
            
            # Get feature importance from Random Forest
            model = self.ml_manager.models['random_forest']
            feature_names = self.ml_manager.feature_columns
            
            # Get available features
            available_features = [f for f in feature_names if f in data.columns]
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_[:len(available_features)]
                
                # Create feature importance dictionary
                feature_importance = {
                    feature: float(importance) 
                    for feature, importance in zip(available_features, importances)
                }
                
                # Sort by importance
                sorted_features = sorted(
                    feature_importance.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                # Categorize features
                categorized_importance = self._categorize_feature_importance(sorted_features)
                
                # Get top influential features
                top_features = sorted_features[:5]
                
                return {
                    'top_features': [{'feature': f, 'importance': i} for f, i in top_features],
                    'all_features': feature_importance,
                    'categorized_importance': categorized_importance,
                    'total_features': len(available_features)
                }
            else:
                return {'error': 'Feature importance not available'}
                
        except Exception as e:
            logging.error(f"Error analyzing feature importance: {str(e)}")
            return {'error': str(e)}
    
    def _categorize_feature_importance(self, sorted_features):
        """Categorize features by type and calculate category importance"""
        category_importance = {}
        
        for category, features in self.feature_categories.items():
            category_score = 0
            feature_count = 0
            
            for feature_name, importance in sorted_features:
                if feature_name in features:
                    category_score += importance
                    feature_count += 1
            
            if feature_count > 0:
                category_importance[category] = {
                    'total_importance': float(category_score),
                    'average_importance': float(category_score / feature_count),
                    'feature_count': feature_count
                }
        
        return category_importance
    
    def _generate_model_explanations(self, rf_pred, lstm_pred, xgb_pred, data):
        """Generate explanations for each model's prediction"""
        explanations = {}
        
        current_price = data['Close'].iloc[-1]
        
        # Random Forest explanation
        if 'prediction' in rf_pred:
            price_change = rf_pred['prediction'] - current_price
            direction = 'bullish' if price_change > 0 else 'bearish' if price_change < 0 else 'neutral'
            confidence_level = 'high' if rf_pred['confidence'] > 0.7 else 'medium' if rf_pred['confidence'] > 0.4 else 'low'
            
            explanations['random_forest'] = {
                'prediction': rf_pred['prediction'],
                'confidence': rf_pred['confidence'],
                'direction': direction,
                'price_change': float(price_change),
                'explanation': self._get_rf_explanation(direction, confidence_level, price_change),
                'reasoning': self._get_rf_reasoning(data)
            }
        
        # LSTM explanation
        if 'prediction' in lstm_pred:
            price_change = lstm_pred['prediction'] - current_price
            direction = 'bullish' if price_change > 0 else 'bearish' if price_change < 0 else 'neutral'
            
            explanations['lstm'] = {
                'prediction': lstm_pred['prediction'],
                'confidence': lstm_pred['confidence'],
                'direction': direction,
                'price_change': float(price_change),
                'explanation': self._get_lstm_explanation(data, direction),
                'reasoning': "LSTM analyzes sequential patterns and temporal dependencies in price movements."
            }
        
        # XGBoost explanation
        if 'prediction' in xgb_pred:
            price_change = xgb_pred['prediction'] - current_price
            direction = 'bullish' if price_change > 0 else 'bearish' if price_change < 0 else 'neutral'
            
            explanations['xgboost'] = {
                'prediction': xgb_pred['prediction'],
                'confidence': xgb_pred['confidence'],
                'direction': direction,
                'price_change': float(price_change),
                'explanation': self._get_xgb_explanation(direction),
                'reasoning': "XGBoost uses gradient boosting to identify complex feature interactions."
            }
        
        return explanations
    
    def _get_rf_explanation(self, direction, confidence_level, price_change):
        """Get Random Forest specific explanation"""
        base_explanation = self.explanation_templates[direction][confidence_level]
        
        if abs(price_change) > 5:
            magnitude = "significant"
        elif abs(price_change) > 1:
            magnitude = "moderate"
        else:
            magnitude = "minor"
        
        return f"{base_explanation} Random Forest predicts a {magnitude} price movement based on technical indicator patterns."
    
    def _get_lstm_explanation(self, data, direction):
        """Get LSTM specific explanation"""
        # Analyze recent price trends
        recent_trend = data['Close'].tail(10).pct_change().mean()
        
        if direction == 'bullish':
            if recent_trend > 0:
                return "LSTM identifies continuation of current upward price momentum based on sequential pattern analysis."
            else:
                return "LSTM detects potential trend reversal to the upside based on historical price sequences."
        elif direction == 'bearish':
            if recent_trend < 0:
                return "LSTM confirms continuation of current downward trend based on temporal patterns."
            else:
                return "LSTM suggests potential trend reversal to the downside based on sequence analysis."
        else:
            return "LSTM indicates consolidation phase with uncertain directional bias."
    
    def _get_xgb_explanation(self, direction):
        """Get XGBoost specific explanation"""
        explanations = {
            'bullish': "XGBoost ensemble identifies positive feature interactions suggesting upward price pressure.",
            'bearish': "XGBoost model detects negative feature combinations indicating downward price momentum.",
            'neutral': "XGBoost finds balanced feature interactions resulting in neutral price direction."
        }
        return explanations[direction]
    
    def _get_rf_reasoning(self, data):
        """Get Random Forest reasoning based on current data"""
        reasoning = []
        
        # RSI reasoning
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if rsi > 70:
                reasoning.append("RSI indicates overbought conditions")
            elif rsi < 30:
                reasoning.append("RSI shows oversold conditions")
            else:
                reasoning.append("RSI is in neutral territory")
        
        # Moving average reasoning
        if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
            current_price = data['Close'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                reasoning.append("Price above both short and long-term moving averages")
            elif current_price < sma_20 < sma_50:
                reasoning.append("Price below both moving averages indicating bearish trend")
        
        return reasoning
    
    def _analyze_prediction_factors(self, data, trading_signals):
        """Analyze factors influencing the prediction"""
        factors = {
            'bullish_factors': [],
            'bearish_factors': [],
            'neutral_factors': [],
            'factor_strength': {}
        }
        
        # Analyze individual trading signals
        if 'individual_signals' in trading_signals:
            for signal_name, signal_data in trading_signals['individual_signals'].items():
                signal = signal_data['signal']
                confidence = signal_data['confidence']
                
                factor_description = self._get_factor_description(signal_name, signal, confidence, data)
                
                if signal == 'BUY':
                    factors['bullish_factors'].append(factor_description)
                elif signal == 'SELL':
                    factors['bearish_factors'].append(factor_description)
                else:
                    factors['neutral_factors'].append(factor_description)
                
                factors['factor_strength'][signal_name] = confidence
        
        # Overall signal analysis
        overall_signal = trading_signals.get('overall_signal', 'HOLD')
        overall_confidence = trading_signals.get('overall_confidence', 0.5)
        
        factors['overall_sentiment'] = {
            'signal': overall_signal,
            'confidence': overall_confidence,
            'explanation': self._explain_overall_sentiment(overall_signal, overall_confidence)
        }
        
        return factors
    
    def _get_factor_description(self, signal_name, signal, confidence, data):
        """Get human-readable description of prediction factor"""
        descriptions = {
            'RSI': self._describe_rsi_factor(signal, confidence, data),
            'MACD': self._describe_macd_factor(signal, confidence, data),
            'MA': self._describe_ma_factor(signal, confidence, data),
            'BB': self._describe_bb_factor(signal, confidence, data),
            'STOCH': self._describe_stoch_factor(signal, confidence, data),
            'WILLIAMS': self._describe_williams_factor(signal, confidence, data),
            'VOLUME': self._describe_volume_factor(signal, confidence, data)
        }
        
        return descriptions.get(signal_name, f"{signal_name} indicates {signal.lower()} with {confidence:.1%} confidence")
    
    def _describe_rsi_factor(self, signal, confidence, data):
        """Describe RSI factor"""
        if 'RSI' in data.columns:
            rsi_value = data['RSI'].iloc[-1]
            if signal == 'BUY':
                return f"RSI ({rsi_value:.1f}) indicates oversold conditions with {confidence:.1%} confidence"
            elif signal == 'SELL':
                return f"RSI ({rsi_value:.1f}) shows overbought conditions with {confidence:.1%} confidence"
            else:
                return f"RSI ({rsi_value:.1f}) is neutral with {confidence:.1%} confidence"
        return f"RSI suggests {signal.lower()} with {confidence:.1%} confidence"
    
    def _describe_macd_factor(self, signal, confidence, data):
        """Describe MACD factor"""
        if signal == 'BUY':
            return f"MACD bullish crossover detected with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"MACD bearish crossover identified with {confidence:.1%} confidence"
        else:
            return f"MACD shows neutral momentum with {confidence:.1%} confidence"
    
    def _describe_ma_factor(self, signal, confidence, data):
        """Describe Moving Average factor"""
        if signal == 'BUY':
            return f"Moving averages support upward trend with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"Moving averages indicate downward trend with {confidence:.1%} confidence"
        else:
            return f"Moving averages show sideways trend with {confidence:.1%} confidence"
    
    def _describe_bb_factor(self, signal, confidence, data):
        """Describe Bollinger Bands factor"""
        if signal == 'BUY':
            return f"Price near lower Bollinger Band suggests oversold with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"Price near upper Bollinger Band indicates overbought with {confidence:.1%} confidence"
        else:
            return f"Price within Bollinger Bands shows neutral with {confidence:.1%} confidence"
    
    def _describe_stoch_factor(self, signal, confidence, data):
        """Describe Stochastic factor"""
        if signal == 'BUY':
            return f"Stochastic oscillator suggests oversold bounce with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"Stochastic indicates overbought correction with {confidence:.1%} confidence"
        else:
            return f"Stochastic shows neutral momentum with {confidence:.1%} confidence"
    
    def _describe_williams_factor(self, signal, confidence, data):
        """Describe Williams %R factor"""
        if signal == 'BUY':
            return f"Williams %R indicates oversold reversal with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"Williams %R suggests overbought decline with {confidence:.1%} confidence"
        else:
            return f"Williams %R shows neutral with {confidence:.1%} confidence"
    
    def _describe_volume_factor(self, signal, confidence, data):
        """Describe Volume factor"""
        if signal == 'BUY':
            return f"Volume confirms bullish momentum with {confidence:.1%} confidence"
        elif signal == 'SELL':
            return f"Volume supports bearish pressure with {confidence:.1%} confidence"
        else:
            return f"Volume shows neutral activity with {confidence:.1%} confidence"
    
    def _explain_overall_sentiment(self, signal, confidence):
        """Explain overall market sentiment"""
        if signal == 'BUY':
            if confidence > 0.8:
                return "Strong consensus among indicators favors buying opportunity"
            elif confidence > 0.6:
                return "Moderate bullish signals suggest potential upside"
            else:
                return "Weak bullish indicators with limited conviction"
        elif signal == 'SELL':
            if confidence > 0.8:
                return "Strong consensus among indicators suggests selling pressure"
            elif confidence > 0.6:
                return "Moderate bearish signals indicate potential downside"
            else:
                return "Weak bearish indicators with limited conviction"
        else:
            return "Mixed signals result in neutral outlook with sideways movement expected"
    
    def _generate_human_explanation(self, ticker, data, feature_analysis, model_explanations, factors):
        """Generate comprehensive human-readable explanation"""
        current_price = data['Close'].iloc[-1]
        
        # Start with overview
        explanation = f"Analysis of {ticker} at ${current_price:.2f}:\n\n"
        
        # Model consensus
        predictions = []
        for model_name, model_data in model_explanations.items():
            if 'prediction' in model_data:
                predictions.append(model_data['prediction'])
        
        if predictions:
            avg_prediction = np.mean(predictions)
            price_change = avg_prediction - current_price
            change_percent = (price_change / current_price) * 100
            
            direction = "upward" if price_change > 0 else "downward" if price_change < 0 else "sideways"
            explanation += f"Model Consensus: Expecting {direction} movement of {change_percent:.1f}% to ${avg_prediction:.2f}\n\n"
        
        # Key factors
        explanation += "Key Analysis Factors:\n"
        
        if 'top_features' in feature_analysis:
            explanation += "• Most Influential Indicators:\n"
            for feature in feature_analysis['top_features'][:3]:
                explanation += f"  - {feature['feature']}: {feature['importance']:.1%} influence\n"
            explanation += "\n"
        
        # Bullish factors
        if factors['bullish_factors']:
            explanation += "• Bullish Signals:\n"
            for factor in factors['bullish_factors'][:3]:
                explanation += f"  - {factor}\n"
            explanation += "\n"
        
        # Bearish factors
        if factors['bearish_factors']:
            explanation += "• Bearish Signals:\n"
            for factor in factors['bearish_factors'][:3]:
                explanation += f"  - {factor}\n"
            explanation += "\n"
        
        # Overall assessment
        overall = factors.get('overall_sentiment', {})
        if overall:
            explanation += f"Overall Assessment: {overall.get('explanation', 'Analysis complete')}"
        
        return explanation
    
    def _analyze_strategy_alignment(self, trading_signals):
        """Analyze how well different strategies align"""
        if 'individual_signals' not in trading_signals:
            return {'error': 'No individual signals available'}
        
        signals = trading_signals['individual_signals']
        signal_values = [s['signal'] for s in signals.values()]
        
        # Count signal types
        buy_count = signal_values.count('BUY')
        sell_count = signal_values.count('SELL')
        hold_count = signal_values.count('HOLD')
        total_signals = len(signal_values)
        
        # Calculate alignment
        if buy_count > sell_count and buy_count > hold_count:
            alignment = 'bullish'
            consensus = buy_count / total_signals
        elif sell_count > buy_count and sell_count > hold_count:
            alignment = 'bearish'
            consensus = sell_count / total_signals
        else:
            alignment = 'mixed'
            consensus = max(buy_count, sell_count, hold_count) / total_signals
        
        return {
            'alignment': alignment,
            'consensus_strength': float(consensus),
            'signal_distribution': {
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count
            },
            'agreement_level': 'high' if consensus > 0.7 else 'medium' if consensus > 0.5 else 'low'
        }
    
    def _generate_key_insights(self, data, feature_analysis):
        """Generate key insights from analysis"""
        insights = []
        
        # Feature importance insights
        if 'categorized_importance' in feature_analysis:
            cat_importance = feature_analysis['categorized_importance']
            
            # Find most important category
            if cat_importance:
                top_category = max(cat_importance.items(), key=lambda x: x[1]['total_importance'])
                insights.append(f"{top_category[0].replace('_', ' ').title()} are the most influential factors")
        
        # Price trend insights
        recent_change = data['Close'].pct_change().tail(5).mean()
        if abs(recent_change) > 0.02:
            trend = "strong upward" if recent_change > 0 else "strong downward"
            insights.append(f"Recent price shows {trend} momentum")
        
        # Volume insights
        if 'Volume_Ratio' in data.columns:
            vol_ratio = data['Volume_Ratio'].iloc[-1]
            if vol_ratio > 2:
                insights.append("Exceptional volume activity suggests institutional interest")
            elif vol_ratio < 0.5:
                insights.append("Low volume indicates reduced market participation")
        
        # Volatility insights
        if 'Volatility' in data.columns:
            current_vol = data['Volatility'].iloc[-1]
            avg_vol = data['Volatility'].mean()
            
            if current_vol > 2 * avg_vol:
                insights.append("High volatility environment increases prediction uncertainty")
            elif current_vol < 0.5 * avg_vol:
                insights.append("Low volatility suggests stable price environment")
        
        return insights if insights else ["Standard market conditions observed"]
    
    def _identify_risk_factors(self, data, factors):
        """Identify potential risk factors"""
        risks = []
        
        # Conflicting signals risk
        bullish_count = len(factors['bullish_factors'])
        bearish_count = len(factors['bearish_factors'])
        
        if abs(bullish_count - bearish_count) <= 1 and bullish_count > 0 and bearish_count > 0:
            risks.append("Conflicting technical signals increase prediction uncertainty")
        
        # Volatility risk
        if 'Volatility' in data.columns:
            vol = data['Volatility'].iloc[-1]
            if vol > 0.05:  # 5% daily volatility
                risks.append("High volatility increases position risk")
        
        # Volume risk
        if 'Volume_Ratio' in data.columns:
            vol_ratio = data['Volume_Ratio'].iloc[-1]
            if vol_ratio < 0.3:
                risks.append("Low volume may indicate poor liquidity")
        
        # Extreme indicator readings
        if 'RSI' in data.columns:
            rsi = data['RSI'].iloc[-1]
            if rsi > 80 or rsi < 20:
                risks.append("Extreme RSI readings suggest potential reversal risk")
        
        return risks if risks else ["No significant risk factors identified"]
    
    def _breakdown_confidence_sources(self, rf_pred, lstm_pred, xgb_pred):
        """Break down confidence sources from different models"""
        breakdown = {}
        
        if 'confidence' in rf_pred:
            breakdown['random_forest'] = {
                'confidence': rf_pred['confidence'],
                'source': 'Technical indicator patterns and feature importance'
            }
        
        if 'confidence' in lstm_pred:
            breakdown['lstm'] = {
                'confidence': lstm_pred['confidence'],
                'source': 'Sequential price patterns and temporal dependencies'
            }
        
        if 'confidence' in xgb_pred:
            breakdown['xgboost'] = {
                'confidence': xgb_pred['confidence'],
                'source': 'Gradient boosting and feature interactions'
            }
        
        # Calculate model agreement
        confidences = [pred.get('confidence', 0) for pred in [rf_pred, lstm_pred, xgb_pred] if 'confidence' in pred]
        if confidences:
            agreement = 1.0 - (max(confidences) - min(confidences))
            breakdown['model_agreement'] = {
                'agreement_score': float(agreement),
                'interpretation': 'high' if agreement > 0.8 else 'medium' if agreement > 0.6 else 'low'
            }
        
        return breakdown
    
    def _calculate_explanation_confidence(self, rf_pred, lstm_pred, xgb_pred):
        """Calculate overall confidence in the explanation"""
        confidences = []
        
        # Model confidences
        for pred in [rf_pred, lstm_pred, xgb_pred]:
            if 'confidence' in pred:
                confidences.append(pred['confidence'])
        
        if not confidences:
            return 0.0
        
        # Average confidence
        avg_confidence = np.mean(confidences)
        
        # Penalty for high disagreement
        if len(confidences) > 1:
            std_confidence = np.std(confidences)
            agreement_penalty = min(std_confidence * 2, 0.3)  # Cap penalty at 0.3
            avg_confidence = max(0.0, avg_confidence - agreement_penalty)
        
        return float(avg_confidence)
