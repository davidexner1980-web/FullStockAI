import numpy as np
import pandas as pd
from server.utils.services.data_fetcher import DataFetcher
from ml_models.random_forest_predictor import RandomForestPredictor
from ml_models.xgboost_predictor import XGBoostPredictor
from ml_models.lstm_predictor import LSTMPredictor
import logging
from datetime import datetime

class ExplainabilityService:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.rf_model = RandomForestPredictor()
        self.xgb_model = XGBoostPredictor()
        self.lstm_model = LSTMPredictor()
        
    def explain_prediction(self, ticker):
        """Provide detailed explanation of prediction"""
        try:
            # Get predictions from all models
            predictions = self.get_model_predictions(ticker)
            
            # Get feature importance analysis
            feature_analysis = self.analyze_feature_importance(ticker)
            
            # Get technical indicator explanations
            technical_explanation = self.explain_technical_indicators(ticker)
            
            # Get market context
            market_context = self.get_market_context(ticker)
            
            # Generate human-readable explanation
            explanation = self.generate_explanation_narrative(
                ticker, predictions, feature_analysis, technical_explanation, market_context
            )
            
            return {
                'ticker': ticker,
                'explanation_summary': explanation,
                'model_predictions': predictions,
                'feature_importance': feature_analysis,
                'technical_indicators': technical_explanation,
                'market_context': market_context,
                'confidence_factors': self.analyze_confidence_factors(predictions, feature_analysis),
                'risk_factors': self.identify_risk_factors(ticker, technical_explanation),
                'recommendation_reasoning': self.explain_recommendation_logic(predictions, feature_analysis),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Explainability service error for {ticker}: {str(e)}")
            return self.generate_error_explanation(ticker, str(e))

    def get_model_predictions(self, ticker):
        """Get predictions from all available models"""
        predictions = {}
        
        # Random Forest prediction
        try:
            rf_result = self.rf_model.predict(ticker)
            predictions['random_forest'] = {
                'prediction': rf_result.get('prediction'),
                'confidence': rf_result.get('confidence'),
                'signal': rf_result.get('signal'),
                'model_type': 'ensemble_tree',
                'strengths': ['Pattern recognition', 'Non-linear relationships', 'Robust to outliers'],
                'explanation': 'Random Forest analyzes multiple decision trees to identify patterns in historical price and volume data.'
            }
        except Exception as e:
            predictions['random_forest'] = {'error': str(e)}
        
        # XGBoost prediction
        try:
            xgb_result = self.xgb_model.predict(ticker)
            predictions['xgboost'] = {
                'prediction': xgb_result.get('prediction'),
                'confidence': xgb_result.get('confidence'),
                'signal': xgb_result.get('signal'),
                'model_type': 'gradient_boosting',
                'strengths': ['Feature importance ranking', 'Handles missing data', 'High accuracy'],
                'explanation': 'XGBoost uses gradient boosting to iteratively improve predictions by learning from previous errors.'
            }
        except Exception as e:
            predictions['xgboost'] = {'error': str(e)}
        
        # LSTM prediction
        try:
            lstm_result = self.lstm_model.predict(ticker)
            predictions['lstm'] = {
                'prediction': lstm_result.get('prediction'),
                'confidence': lstm_result.get('confidence'),
                'signal': lstm_result.get('signal'),
                'model_type': 'neural_network',
                'strengths': ['Sequential pattern learning', 'Long-term dependencies', 'Time series expertise'],
                'explanation': 'LSTM neural network specializes in learning from sequential price movements and temporal patterns.'
            }
        except Exception as e:
            predictions['lstm'] = {'error': str(e)}
        
        return predictions

    def analyze_feature_importance(self, ticker):
        """Analyze feature importance across models"""
        try:
            # Get feature importance from tree-based models
            rf_importance = self.rf_model.get_feature_importance()
            xgb_importance = self.xgb_model.get_feature_importance()
            
            # Combine and analyze
            all_features = set(list(rf_importance.keys()) + list(xgb_importance.keys()))
            
            feature_analysis = {}
            for feature in all_features:
                rf_score = rf_importance.get(feature, 0)
                xgb_score = xgb_importance.get(feature, 0)
                avg_importance = (rf_score + xgb_score) / 2
                
                feature_analysis[feature] = {
                    'average_importance': float(avg_importance),
                    'rf_importance': float(rf_score),
                    'xgb_importance': float(xgb_score),
                    'explanation': self.get_feature_explanation(feature),
                    'impact': 'High' if avg_importance > 0.1 else 'Medium' if avg_importance > 0.05 else 'Low'
                }
            
            # Sort by importance
            sorted_features = sorted(feature_analysis.items(), key=lambda x: x[1]['average_importance'], reverse=True)
            
            return {
                'top_features': dict(sorted_features[:10]),
                'feature_categories': self.categorize_features(feature_analysis),
                'interpretation': self.interpret_feature_importance(sorted_features[:5])
            }
            
        except Exception as e:
            logging.error(f"Feature importance analysis error: {str(e)}")
            return {'error': str(e)}

    def get_feature_explanation(self, feature):
        """Get human-readable explanation for each feature"""
        explanations = {
            'sma_5': 'Short-term price trend (5-day average)',
            'sma_10': 'Short-term price trend (10-day average)',
            'sma_20': 'Medium-term price trend (20-day average)',
            'sma_50': 'Long-term price trend (50-day average)',
            'ema_12': 'Exponential moving average emphasizing recent prices',
            'ema_26': 'Longer exponential moving average for trend confirmation',
            'macd': 'Momentum indicator showing trend changes',
            'macd_signal': 'Signal line for MACD crossover strategies',
            'macd_histogram': 'Difference between MACD and signal line',
            'rsi': 'Relative Strength Index measuring overbought/oversold conditions',
            'bb_position': 'Position within Bollinger Bands indicating volatility',
            'bb_width': 'Bollinger Band width showing market volatility',
            'volume_ratio': 'Trading volume compared to average',
            'momentum_5': '5-day price momentum',
            'momentum_10': '10-day price momentum',
            'momentum_20': '20-day price momentum',
            'volatility': 'Price volatility measurement',
            'volatility_ratio': 'Current volatility vs historical average',
            'support_distance': 'Distance from support level',
            'resistance_distance': 'Distance from resistance level',
            'high_low_ratio': 'Daily high-to-low price ratio',
            'close_open_ratio': 'Closing price relative to opening price'
        }
        
        return explanations.get(feature, 'Technical indicator contributing to price prediction')

    def categorize_features(self, feature_analysis):
        """Categorize features by type"""
        categories = {
            'trend_indicators': [],
            'momentum_indicators': [],
            'volatility_indicators': [],
            'volume_indicators': [],
            'support_resistance': []
        }
        
        for feature, data in feature_analysis.items():
            if any(term in feature for term in ['sma', 'ema', 'trend']):
                categories['trend_indicators'].append(feature)
            elif any(term in feature for term in ['macd', 'rsi', 'momentum']):
                categories['momentum_indicators'].append(feature)
            elif any(term in feature for term in ['volatility', 'bb_']):
                categories['volatility_indicators'].append(feature)
            elif 'volume' in feature:
                categories['volume_indicators'].append(feature)
            elif any(term in feature for term in ['support', 'resistance']):
                categories['support_resistance'].append(feature)
        
        return categories

    def interpret_feature_importance(self, top_features):
        """Generate interpretation of top features"""
        interpretations = []
        
        for feature_name, feature_data in top_features:
            importance = feature_data['average_importance']
            explanation = feature_data['explanation']
            
            if importance > 0.15:
                interpretations.append(f"Strong influence: {explanation} (importance: {importance:.3f})")
            elif importance > 0.08:
                interpretations.append(f"Moderate influence: {explanation} (importance: {importance:.3f})")
            else:
                interpretations.append(f"Minor influence: {explanation} (importance: {importance:.3f})")
        
        return interpretations

    def explain_technical_indicators(self, ticker):
        """Explain current technical indicator values"""
        try:
            # Get recent data
            data = self.data_fetcher.get_historical_data(ticker, period='3mo')
            
            if data.empty:
                return {'error': 'No data available for technical analysis'}
            
            current_price = data['Close'].iloc[-1]
            
            # Calculate key indicators
            indicators = {
                'price_trend': self.analyze_price_trend(data),
                'momentum': self.analyze_momentum(data),
                'volatility': self.analyze_volatility(data),
                'volume_analysis': self.analyze_volume(data),
                'support_resistance': self.analyze_support_resistance(data)
            }
            
            return {
                'current_price': float(current_price),
                'indicators': indicators,
                'overall_technical_outlook': self.determine_technical_outlook(indicators)
            }
            
        except Exception as e:
            logging.error(f"Technical indicator explanation error: {str(e)}")
            return {'error': str(e)}

    def analyze_price_trend(self, data):
        """Analyze price trend indicators"""
        sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1] if len(data) >= 50 else sma_20
        current_price = data['Close'].iloc[-1]
        
        trend_direction = 'Uptrend' if current_price > sma_20 > sma_50 else \
                         'Downtrend' if current_price < sma_20 < sma_50 else 'Sideways'
        
        return {
            'direction': trend_direction,
            'current_price': float(current_price),
            'sma_20': float(sma_20),
            'sma_50': float(sma_50),
            'explanation': f'Price is {"above" if current_price > sma_20 else "below"} the 20-day moving average, indicating {trend_direction.lower()} momentum.'
        }

    def analyze_momentum(self, data):
        """Analyze momentum indicators"""
        # RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # MACD calculation
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        current_macd = macd.iloc[-1]
        
        rsi_condition = 'Overbought' if current_rsi > 70 else 'Oversold' if current_rsi < 30 else 'Neutral'
        macd_condition = 'Bullish' if current_macd > 0 else 'Bearish'
        
        return {
            'rsi': float(current_rsi),
            'rsi_condition': rsi_condition,
            'macd': float(current_macd),
            'macd_condition': macd_condition,
            'explanation': f'RSI at {current_rsi:.1f} suggests {rsi_condition.lower()} conditions. MACD indicates {macd_condition.lower()} momentum.'
        }

    def analyze_volatility(self, data):
        """Analyze volatility indicators"""
        returns = data['Close'].pct_change()
        current_volatility = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252)  # Annualized
        avg_volatility = returns.std() * np.sqrt(252)
        
        volatility_level = 'High' if current_volatility > avg_volatility * 1.5 else \
                          'Low' if current_volatility < avg_volatility * 0.7 else 'Normal'
        
        # Bollinger Bands
        sma_20 = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        bb_upper = sma_20 + (bb_std * 2)
        bb_lower = sma_20 - (bb_std * 2)
        current_price = data['Close'].iloc[-1]
        bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
        
        return {
            'current_volatility': float(current_volatility),
            'volatility_level': volatility_level,
            'bollinger_position': float(bb_position),
            'explanation': f'Current volatility is {volatility_level.lower()}. Price is at {bb_position:.1%} of Bollinger Band range.'
        }

    def analyze_volume(self, data):
        """Analyze volume patterns"""
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        volume_condition = 'High' if volume_ratio > 1.5 else 'Low' if volume_ratio < 0.7 else 'Average'
        
        return {
            'current_volume': int(current_volume),
            'average_volume': int(avg_volume),
            'volume_ratio': float(volume_ratio),
            'volume_condition': volume_condition,
            'explanation': f'Trading volume is {volume_condition.lower()} at {volume_ratio:.1f}x the 20-day average.'
        }

    def analyze_support_resistance(self, data):
        """Analyze support and resistance levels"""
        recent_high = data['High'].rolling(window=20).max().iloc[-1]
        recent_low = data['Low'].rolling(window=20).min().iloc[-1]
        current_price = data['Close'].iloc[-1]
        
        resistance_distance = (recent_high - current_price) / current_price
        support_distance = (current_price - recent_low) / current_price
        
        return {
            'resistance_level': float(recent_high),
            'support_level': float(recent_low),
            'resistance_distance': float(resistance_distance),
            'support_distance': float(support_distance),
            'explanation': f'Price is {resistance_distance:.1%} below resistance at ${recent_high:.2f} and {support_distance:.1%} above support at ${recent_low:.2f}.'
        }

    def determine_technical_outlook(self, indicators):
        """Determine overall technical outlook"""
        bullish_signals = 0
        bearish_signals = 0
        
        # Price trend
        if indicators['price_trend']['direction'] == 'Uptrend':
            bullish_signals += 1
        elif indicators['price_trend']['direction'] == 'Downtrend':
            bearish_signals += 1
        
        # Momentum
        if indicators['momentum']['macd_condition'] == 'Bullish':
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if indicators['momentum']['rsi_condition'] == 'Oversold':
            bullish_signals += 1
        elif indicators['momentum']['rsi_condition'] == 'Overbought':
            bearish_signals += 1
        
        # Determine outlook
        if bullish_signals > bearish_signals:
            outlook = 'Bullish'
        elif bearish_signals > bullish_signals:
            outlook = 'Bearish'
        else:
            outlook = 'Neutral'
        
        return {
            'outlook': outlook,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'confidence': abs(bullish_signals - bearish_signals) / max(1, bullish_signals + bearish_signals)
        }

    def get_market_context(self, ticker):
        """Get broader market context"""
        try:
            # Get market indices for context
            market_data = {}
            indices = ['SPY', 'QQQ', 'DIA']
            
            for index in indices:
                try:
                    index_data = self.data_fetcher.get_historical_data(index, period='1mo')
                    if not index_data.empty:
                        current = index_data['Close'].iloc[-1]
                        prev = index_data['Close'].iloc[-2] if len(index_data) > 1 else current
                        change = (current - prev) / prev
                        
                        market_data[index] = {
                            'current_price': float(current),
                            'daily_change': float(change),
                            'trend': 'Positive' if change > 0 else 'Negative' if change < 0 else 'Neutral'
                        }
                except:
                    continue
            
            # Determine market sentiment
            if market_data:
                avg_change = np.mean([data['daily_change'] for data in market_data.values()])
                market_sentiment = 'Bullish' if avg_change > 0.005 else 'Bearish' if avg_change < -0.005 else 'Mixed'
            else:
                market_sentiment = 'Unknown'
            
            return {
                'market_indices': market_data,
                'overall_market_sentiment': market_sentiment,
                'context_explanation': f'Broader market sentiment appears {market_sentiment.lower()} based on major indices performance.'
            }
            
        except Exception as e:
            logging.error(f"Market context error: {str(e)}")
            return {'error': str(e)}

    def analyze_confidence_factors(self, predictions, feature_analysis):
        """Analyze factors affecting prediction confidence"""
        confidence_factors = []
        
        # Model agreement
        working_predictions = [p for p in predictions.values() if 'prediction' in p]
        if len(working_predictions) > 1:
            pred_values = [p['prediction'] for p in working_predictions]
            pred_std = np.std(pred_values)
            pred_mean = np.mean(pred_values)
            agreement_score = 1 - (pred_std / pred_mean) if pred_mean != 0 else 0
            
            if agreement_score > 0.8:
                confidence_factors.append("High model agreement increases confidence")
            elif agreement_score > 0.6:
                confidence_factors.append("Moderate model agreement")
            else:
                confidence_factors.append("Low model agreement reduces confidence")
        
        # Feature importance concentration
        if 'top_features' in feature_analysis:
            top_importance = feature_analysis['top_features']
            if top_importance:
                max_importance = max(data['average_importance'] for data in top_importance.values())
                if max_importance > 0.2:
                    confidence_factors.append("Strong feature signals support the prediction")
                elif max_importance > 0.1:
                    confidence_factors.append("Moderate feature signals")
                else:
                    confidence_factors.append("Weak feature signals reduce confidence")
        
        return confidence_factors

    def identify_risk_factors(self, ticker, technical_explanation):
        """Identify potential risk factors"""
        risk_factors = []
        
        if 'indicators' in technical_explanation:
            indicators = technical_explanation['indicators']
            
            # Volatility risk
            if indicators.get('volatility', {}).get('volatility_level') == 'High':
                risk_factors.append("High volatility increases prediction uncertainty")
            
            # Overbought/oversold risk
            momentum = indicators.get('momentum', {})
            if momentum.get('rsi_condition') == 'Overbought':
                risk_factors.append("Overbought conditions suggest potential price correction")
            elif momentum.get('rsi_condition') == 'Oversold':
                risk_factors.append("Oversold conditions may indicate oversold bounce potential")
            
            # Volume risk
            volume = indicators.get('volume_analysis', {})
            if volume.get('volume_condition') == 'Low':
                risk_factors.append("Low volume reduces reliability of price movements")
            
            # Support/resistance proximity
            sr = indicators.get('support_resistance', {})
            if sr.get('resistance_distance', 1) < 0.02:
                risk_factors.append("Price near resistance level - potential reversal risk")
            elif sr.get('support_distance', 1) < 0.02:
                risk_factors.append("Price near support level - potential breakdown risk")
        
        if not risk_factors:
            risk_factors.append("No significant risk factors identified")
        
        return risk_factors

    def explain_recommendation_logic(self, predictions, feature_analysis):
        """Explain the logic behind recommendations"""
        explanations = []
        
        # Get working predictions
        working_predictions = [p for p in predictions.values() if 'prediction' in p and 'signal' in p]
        
        if working_predictions:
            signals = [p['signal'] for p in working_predictions]
            signal_counts = {signal: signals.count(signal) for signal in set(signals)}
            dominant_signal = max(signal_counts, key=signal_counts.get)
            
            if dominant_signal == 'BUY':
                explanations.append("Models suggest bullish momentum with upward price potential")
            elif dominant_signal == 'SELL':
                explanations.append("Models indicate bearish pressure with downward price risk")
            else:
                explanations.append("Models suggest neutral stance with limited directional bias")
            
            # Feature-based explanation
            if 'top_features' in feature_analysis:
                top_feature = list(feature_analysis['top_features'].keys())[0]
                feature_explanation = feature_analysis['top_features'][top_feature]['explanation']
                explanations.append(f"Primary driver: {feature_explanation}")
        
        return explanations

    def generate_explanation_narrative(self, ticker, predictions, feature_analysis, technical_explanation, market_context):
        """Generate comprehensive human-readable explanation"""
        narrative_parts = []
        
        # Introduction
        narrative_parts.append(f"Analysis for {ticker}:")
        
        # Model consensus
        working_predictions = [p for p in predictions.values() if 'prediction' in p]
        if working_predictions:
            avg_prediction = np.mean([p['prediction'] for p in working_predictions])
            current_price = technical_explanation.get('current_price', 0)
            
            if current_price > 0:
                expected_change = (avg_prediction - current_price) / current_price * 100
                narrative_parts.append(f"Models predict a {expected_change:+.1f}% price movement to ${avg_prediction:.2f}")
        
        # Key factors
        if 'top_features' in feature_analysis and feature_analysis['top_features']:
            top_feature_name = list(feature_analysis['top_features'].keys())[0]
            top_feature_data = feature_analysis['top_features'][top_feature_name]
            narrative_parts.append(f"Primary factor: {top_feature_data['explanation']}")
        
        # Technical outlook
        if 'overall_technical_outlook' in technical_explanation:
            outlook = technical_explanation['overall_technical_outlook']['outlook']
            narrative_parts.append(f"Technical analysis indicates a {outlook.lower()} outlook")
        
        # Market context
        if 'overall_market_sentiment' in market_context:
            sentiment = market_context['overall_market_sentiment']
            narrative_parts.append(f"Broader market sentiment is {sentiment.lower()}")
        
        return '. '.join(narrative_parts) + '.'

    def generate_error_explanation(self, ticker, error_message):
        """Generate error explanation when analysis fails"""
        return {
            'ticker': ticker,
            'explanation_summary': f"Unable to generate explanation for {ticker} due to: {error_message}",
            'model_predictions': {},
            'feature_importance': {},
            'technical_indicators': {},
            'market_context': {},
            'confidence_factors': ["Analysis could not be completed"],
            'risk_factors': ["Unable to assess risks due to data issues"],
            'recommendation_reasoning': ["Recommendation logic unavailable"],
            'timestamp': datetime.now().isoformat(),
            'error': error_message
        }
