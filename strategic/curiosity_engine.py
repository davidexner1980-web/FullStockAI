import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from services.data_fetcher import DataFetcher
import json
import os

class CuriosityEngine:
    """Anomaly Detection and Market Behavior Analysis Engine"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.scaler = StandardScaler()
        self.anomaly_threshold = 0.1  # Threshold for anomaly detection
        self.curiosity_levels = ['LOW', 'MEDIUM', 'HIGH', 'EXTREME']
    
    def analyze_anomalies(self, ticker):
        """Comprehensive anomaly detection and curiosity analysis"""
        try:
            # Get extended data for better anomaly detection
            data = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if data is None:
                return {'error': 'Failed to fetch data for curiosity analysis'}
            
            # Prepare features for anomaly detection
            features = self._prepare_anomaly_features(data)
            if features is None:
                return {'error': 'Failed to prepare features for analysis'}
            
            # Detect anomalies using multiple methods
            isolation_anomalies = self._detect_isolation_anomalies(features)
            statistical_anomalies = self._detect_statistical_anomalies(data)
            pattern_anomalies = self._detect_pattern_anomalies(data)
            volume_anomalies = self._detect_volume_anomalies(data)
            
            # Calculate overall curiosity score
            curiosity_score = self._calculate_curiosity_score(
                isolation_anomalies, statistical_anomalies, 
                pattern_anomalies, volume_anomalies
            )
            
            # Determine curiosity level
            curiosity_level = self._determine_curiosity_level(curiosity_score)
            
            # Generate curiosity insights
            insights = self._generate_curiosity_insights(
                ticker, data, curiosity_score, curiosity_level
            )
            
            # Detect market behavior patterns
            behavior_patterns = self._analyze_behavior_patterns(data)
            
            # Calculate anomaly flags
            anomaly_flags = self._generate_anomaly_flags(
                isolation_anomalies, statistical_anomalies, 
                pattern_anomalies, volume_anomalies
            )
            
            return {
                'ticker': ticker,
                'timestamp': datetime.utcnow().isoformat(),
                'curiosity_score': float(curiosity_score),
                'curiosity_level': curiosity_level,
                'anomaly_detection': {
                    'isolation_forest': isolation_anomalies,
                    'statistical': statistical_anomalies,
                    'pattern_based': pattern_anomalies,
                    'volume_based': volume_anomalies
                },
                'anomaly_flags': anomaly_flags,
                'behavior_patterns': behavior_patterns,
                'curiosity_insights': insights,
                'recommendation': self._generate_recommendation(curiosity_level, anomaly_flags),
                'market_oddities': self._identify_market_oddities(data),
                'attention_signals': self._generate_attention_signals(curiosity_score, anomaly_flags)
            }
            
        except Exception as e:
            logging.error(f"Error in curiosity analysis for {ticker}: {str(e)}")
            return {'error': f'Curiosity analysis failed: {str(e)}'}
    
    def _prepare_anomaly_features(self, data):
        """Prepare features for anomaly detection"""
        try:
            # Select relevant features for anomaly detection
            feature_columns = [
                'Close', 'Volume', 'RSI', 'MACD', 'BB_Upper', 'BB_Lower',
                'Stoch_K', 'Williams_R', 'ATR', 'Price_Change', 'Volatility', 'Volume_Ratio'
            ]
            
            # Filter available columns
            available_columns = [col for col in feature_columns if col in data.columns]
            
            if len(available_columns) < 5:
                logging.warning("Insufficient features for anomaly detection")
                return None
            
            # Extract features
            features = data[available_columns].fillna(method='ffill').fillna(0)
            
            # Add derived features
            features['price_volume_ratio'] = features['Close'] / (features['Volume'] + 1)
            features['rsi_divergence'] = abs(features['RSI'] - 50)
            
            # Calculate rolling statistics for anomaly detection
            window = min(20, len(features) // 4)
            features['rolling_mean_deviation'] = abs(features['Close'] - features['Close'].rolling(window).mean())
            features['rolling_vol_deviation'] = abs(features['Volume'] - features['Volume'].rolling(window).mean())
            
            return features.fillna(0)
            
        except Exception as e:
            logging.error(f"Error preparing anomaly features: {str(e)}")
            return None
    
    def _detect_isolation_anomalies(self, features):
        """Detect anomalies using Isolation Forest"""
        try:
            if len(features) < 50:  # Need sufficient data
                return {'anomalies_detected': [], 'anomaly_score': 0.0}
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Apply Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(scaled_features)
            anomaly_scores = iso_forest.score_samples(scaled_features)
            
            # Identify anomalous points
            anomalous_indices = np.where(anomaly_labels == -1)[0]
            
            # Get recent anomalies (last 30 days)
            recent_window = min(30, len(features))
            recent_anomalies = [idx for idx in anomalous_indices if idx >= len(features) - recent_window]
            
            # Calculate overall anomaly score
            overall_score = abs(np.mean(anomaly_scores[-10:])) if len(anomaly_scores) > 10 else 0
            
            return {
                'anomalies_detected': len(recent_anomalies),
                'total_anomalies': len(anomalous_indices),
                'anomaly_score': float(overall_score),
                'recent_anomaly_ratio': len(recent_anomalies) / recent_window,
                'anomalous_dates': [features.index[idx].isoformat() for idx in recent_anomalies[-5:]]
            }
            
        except Exception as e:
            logging.error(f"Error in isolation forest anomaly detection: {str(e)}")
            return {'anomalies_detected': 0, 'anomaly_score': 0.0, 'error': str(e)}
    
    def _detect_statistical_anomalies(self, data):
        """Detect statistical anomalies in price and volume"""
        try:
            anomalies = {
                'price_anomalies': 0,
                'volume_anomalies': 0,
                'volatility_anomalies': 0,
                'anomaly_details': []
            }
            
            # Price anomalies (using z-score)
            price_changes = data['Close'].pct_change().dropna()
            if len(price_changes) > 20:
                z_scores = np.abs((price_changes - price_changes.mean()) / price_changes.std())
                price_anomalies = z_scores > 3  # 3-sigma anomalies
                anomalies['price_anomalies'] = int(price_anomalies.sum())
                
                # Recent price anomalies
                recent_price_anomalies = price_anomalies.tail(30).sum()
                if recent_price_anomalies > 0:
                    anomalies['anomaly_details'].append(f"{recent_price_anomalies} significant price movements in last 30 days")
            
            # Volume anomalies
            if 'Volume' in data.columns:
                volume_mean = data['Volume'].rolling(60).mean()
                volume_std = data['Volume'].rolling(60).std()
                volume_z_scores = abs((data['Volume'] - volume_mean) / volume_std)
                volume_anomalies = volume_z_scores > 2.5
                anomalies['volume_anomalies'] = int(volume_anomalies.sum())
                
                # Recent volume spikes
                recent_volume_anomalies = volume_anomalies.tail(30).sum()
                if recent_volume_anomalies > 0:
                    anomalies['anomaly_details'].append(f"{recent_volume_anomalies} volume spikes in last 30 days")
            
            # Volatility anomalies
            if 'Volatility' in data.columns:
                vol_mean = data['Volatility'].mean()
                vol_std = data['Volatility'].std()
                recent_vol = data['Volatility'].tail(5).mean()
                
                if abs(recent_vol - vol_mean) > 2 * vol_std:
                    anomalies['volatility_anomalies'] = 1
                    anomalies['anomaly_details'].append("Unusual volatility pattern detected")
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error in statistical anomaly detection: {str(e)}")
            return {'price_anomalies': 0, 'volume_anomalies': 0, 'error': str(e)}
    
    def _detect_pattern_anomalies(self, data):
        """Detect unusual patterns in technical indicators"""
        try:
            patterns = {
                'rsi_extremes': 0,
                'macd_divergence': 0,
                'bollinger_breakouts': 0,
                'pattern_details': []
            }
            
            # RSI extreme conditions
            if 'RSI' in data.columns:
                rsi_recent = data['RSI'].tail(10)
                extreme_rsi = ((rsi_recent < 20) | (rsi_recent > 80)).sum()
                patterns['rsi_extremes'] = int(extreme_rsi)
                
                if extreme_rsi > 2:
                    patterns['pattern_details'].append(f"RSI in extreme territory {extreme_rsi} times recently")
            
            # MACD signal anomalies
            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                macd_diff = data['MACD'] - data['MACD_Signal']
                recent_macd_changes = macd_diff.diff().tail(10)
                large_changes = abs(recent_macd_changes) > 2 * recent_macd_changes.std()
                patterns['macd_divergence'] = int(large_changes.sum())
            
            # Bollinger Band breakouts
            if all(col in data.columns for col in ['Close', 'BB_Upper', 'BB_Lower']):
                bb_breakouts = ((data['Close'] > data['BB_Upper']) | 
                              (data['Close'] < data['BB_Lower'])).tail(20).sum()
                patterns['bollinger_breakouts'] = int(bb_breakouts)
                
                if bb_breakouts > 3:
                    patterns['pattern_details'].append(f"{bb_breakouts} Bollinger Band breakouts recently")
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error in pattern anomaly detection: {str(e)}")
            return {'rsi_extremes': 0, 'macd_divergence': 0, 'error': str(e)}
    
    def _detect_volume_anomalies(self, data):
        """Detect volume-based anomalies"""
        try:
            volume_analysis = {
                'volume_spikes': 0,
                'volume_droughts': 0,
                'price_volume_divergence': 0,
                'volume_trend_breaks': 0
            }
            
            if 'Volume' not in data.columns:
                return volume_analysis
            
            # Volume spikes (> 3x average)
            avg_volume = data['Volume'].rolling(30).mean()
            volume_spikes = (data['Volume'] > 3 * avg_volume).tail(20).sum()
            volume_analysis['volume_spikes'] = int(volume_spikes)
            
            # Volume droughts (< 0.3x average)
            volume_droughts = (data['Volume'] < 0.3 * avg_volume).tail(20).sum()
            volume_analysis['volume_droughts'] = int(volume_droughts)
            
            # Price-volume divergence
            price_changes = data['Close'].pct_change()
            volume_changes = data['Volume'].pct_change()
            
            # Look for opposite directional movements
            divergences = ((price_changes > 0.02) & (volume_changes < -0.3)) | \
                         ((price_changes < -0.02) & (volume_changes < -0.3))
            volume_analysis['price_volume_divergence'] = int(divergences.tail(20).sum())
            
            return volume_analysis
            
        except Exception as e:
            logging.error(f"Error in volume anomaly detection: {str(e)}")
            return {'volume_spikes': 0, 'volume_droughts': 0, 'error': str(e)}
    
    def _calculate_curiosity_score(self, isolation, statistical, pattern, volume):
        """Calculate overall curiosity score"""
        try:
            # Weighted scoring
            weights = {
                'isolation': 0.3,
                'statistical': 0.25,
                'pattern': 0.25,
                'volume': 0.2
            }
            
            # Normalize scores
            isolation_score = min(isolation.get('anomaly_score', 0) * 10, 1.0)
            
            statistical_score = (
                statistical.get('price_anomalies', 0) * 0.1 + 
                statistical.get('volume_anomalies', 0) * 0.05 + 
                statistical.get('volatility_anomalies', 0) * 0.15
            )
            statistical_score = min(statistical_score, 1.0)
            
            pattern_score = (
                pattern.get('rsi_extremes', 0) * 0.1 + 
                pattern.get('macd_divergence', 0) * 0.05 + 
                pattern.get('bollinger_breakouts', 0) * 0.05
            )
            pattern_score = min(pattern_score, 1.0)
            
            volume_score = (
                volume.get('volume_spikes', 0) * 0.1 + 
                volume.get('volume_droughts', 0) * 0.05 + 
                volume.get('price_volume_divergence', 0) * 0.1
            )
            volume_score = min(volume_score, 1.0)
            
            # Calculate weighted score
            total_score = (
                isolation_score * weights['isolation'] +
                statistical_score * weights['statistical'] +
                pattern_score * weights['pattern'] +
                volume_score * weights['volume']
            )
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logging.error(f"Error calculating curiosity score: {str(e)}")
            return 0.0
    
    def _determine_curiosity_level(self, score):
        """Determine curiosity level based on score"""
        if score < 0.2:
            return 'LOW'
        elif score < 0.5:
            return 'MEDIUM'
        elif score < 0.8:
            return 'HIGH'
        else:
            return 'EXTREME'
    
    def _generate_curiosity_insights(self, ticker, data, score, level):
        """Generate insights based on curiosity analysis"""
        insights = []
        
        # Level-based insights
        if level == 'EXTREME':
            insights.append(f"{ticker} is exhibiting highly unusual market behavior that demands immediate attention")
            insights.append("Multiple anomaly detection systems are flagging significant deviations from normal patterns")
        elif level == 'HIGH':
            insights.append(f"{ticker} shows notable anomalies that warrant careful monitoring")
            insights.append("Several unusual patterns detected - consider increased position size limits")
        elif level == 'MEDIUM':
            insights.append(f"{ticker} displays some interesting behavioral patterns worth investigating")
            insights.append("Moderate anomalies detected - normal trading approach with slight caution")
        else:
            insights.append(f"{ticker} is trading within normal behavioral patterns")
            insights.append("Low anomaly levels suggest predictable market behavior")
        
        # Add specific technical insights
        if 'RSI' in data.columns:
            current_rsi = data['RSI'].iloc[-1]
            if current_rsi > 80:
                insights.append("RSI indicates severely overbought conditions - rare occurrence")
            elif current_rsi < 20:
                insights.append("RSI shows oversold extremes - potential reversal candidate")
        
        # Volume insights
        if 'Volume_Ratio' in data.columns:
            vol_ratio = data['Volume_Ratio'].iloc[-1]
            if vol_ratio > 3:
                insights.append("Exceptional volume activity detected - institutional interest likely")
            elif vol_ratio < 0.3:
                insights.append("Unusually low volume - lack of conviction in current price levels")
        
        return insights
    
    def _analyze_behavior_patterns(self, data):
        """Analyze recurring behavior patterns"""
        try:
            patterns = {
                'trend_consistency': 'unknown',
                'volatility_regime': 'unknown',
                'volume_pattern': 'unknown',
                'mean_reversion_tendency': 'unknown'
            }
            
            if len(data) < 30:
                return patterns
            
            # Trend consistency
            price_changes = data['Close'].pct_change().dropna()
            positive_days = (price_changes > 0).sum()
            trend_ratio = positive_days / len(price_changes)
            
            if trend_ratio > 0.6:
                patterns['trend_consistency'] = 'strongly_bullish'
            elif trend_ratio < 0.4:
                patterns['trend_consistency'] = 'strongly_bearish'
            else:
                patterns['trend_consistency'] = 'choppy'
            
            # Volatility regime
            if 'Volatility' in data.columns:
                recent_vol = data['Volatility'].tail(20).mean()
                historical_vol = data['Volatility'].mean()
                
                if recent_vol > 1.5 * historical_vol:
                    patterns['volatility_regime'] = 'high_volatility'
                elif recent_vol < 0.7 * historical_vol:
                    patterns['volatility_regime'] = 'low_volatility'
                else:
                    patterns['volatility_regime'] = 'normal_volatility'
            
            # Volume pattern
            if 'Volume' in data.columns:
                volume_trend = np.polyfit(range(len(data['Volume'])), data['Volume'], 1)[0]
                if volume_trend > 0:
                    patterns['volume_pattern'] = 'increasing_interest'
                elif volume_trend < 0:
                    patterns['volume_pattern'] = 'decreasing_interest'
                else:
                    patterns['volume_pattern'] = 'stable_interest'
            
            # Mean reversion tendency
            returns = price_changes.tail(60)
            if len(returns) > 20:
                # Check for mean reversion using autocorrelation
                autocorr = returns.autocorr(lag=1)
                if autocorr < -0.1:
                    patterns['mean_reversion_tendency'] = 'strong_mean_reversion'
                elif autocorr > 0.1:
                    patterns['mean_reversion_tendency'] = 'momentum_trending'
                else:
                    patterns['mean_reversion_tendency'] = 'random_walk'
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error analyzing behavior patterns: {str(e)}")
            return {'error': 'Pattern analysis failed'}
    
    def _generate_anomaly_flags(self, isolation, statistical, pattern, volume):
        """Generate specific anomaly flags"""
        flags = []
        
        # Isolation forest flags
        if isolation.get('anomaly_score', 0) > 0.5:
            flags.append('ISOLATION_ANOMALY')
        
        # Statistical flags
        if statistical.get('price_anomalies', 0) > 2:
            flags.append('PRICE_VOLATILITY_EXTREME')
        if statistical.get('volume_anomalies', 0) > 3:
            flags.append('VOLUME_SPIKE_PATTERN')
        
        # Pattern flags
        if pattern.get('rsi_extremes', 0) > 3:
            flags.append('RSI_EXTREME_CONDITION')
        if pattern.get('bollinger_breakouts', 0) > 4:
            flags.append('BOLLINGER_BREAKOUT_SERIES')
        
        # Volume flags
        if volume.get('volume_spikes', 0) > 2:
            flags.append('UNUSUAL_VOLUME_ACTIVITY')
        if volume.get('price_volume_divergence', 0) > 3:
            flags.append('PRICE_VOLUME_DIVERGENCE')
        
        return flags
    
    def _generate_recommendation(self, level, flags):
        """Generate trading recommendation based on curiosity level"""
        if level == 'EXTREME':
            return {
                'action': 'EXTREME_CAUTION',
                'message': 'Highly unusual activity detected. Consider reducing position sizes and increasing monitoring frequency.',
                'risk_level': 'VERY_HIGH'
            }
        elif level == 'HIGH':
            return {
                'action': 'INCREASED_VIGILANCE',
                'message': 'Notable anomalies present. Trade with caution and tighter stops.',
                'risk_level': 'HIGH'
            }
        elif level == 'MEDIUM':
            return {
                'action': 'STANDARD_MONITORING',
                'message': 'Some unusual patterns detected. Normal trading with slight caution advised.',
                'risk_level': 'MODERATE'
            }
        else:
            return {
                'action': 'NORMAL_OPERATIONS',
                'message': 'No significant anomalies detected. Standard trading approach recommended.',
                'risk_level': 'LOW'
            }
    
    def _identify_market_oddities(self, data):
        """Identify specific market oddities"""
        oddities = []
        
        try:
            # Gap analysis
            gaps = abs(data['Open'] - data['Close'].shift(1))
            large_gaps = gaps > 2 * gaps.std()
            recent_gaps = large_gaps.tail(30).sum()
            
            if recent_gaps > 3:
                oddities.append(f"Multiple large price gaps detected ({recent_gaps} in last 30 days)")
            
            # Doji patterns (open ≈ close)
            if all(col in data.columns for col in ['Open', 'Close', 'High', 'Low']):
                body_size = abs(data['Close'] - data['Open'])
                total_range = data['High'] - data['Low']
                doji_ratio = body_size / (total_range + 0.0001)  # Avoid division by zero
                
                recent_dojis = (doji_ratio < 0.1).tail(20).sum()
                if recent_dojis > 5:
                    oddities.append(f"Multiple Doji patterns detected ({recent_dojis} in last 20 days)")
            
            # Unusual closing patterns
            closes = data['Close'].tail(10)
            if len(closes.unique()) == len(closes):  # All different closes
                if closes.std() / closes.mean() < 0.005:  # Very low volatility
                    oddities.append("Unusually consistent closing prices detected")
            
        except Exception as e:
            logging.error(f"Error identifying market oddities: {str(e)}")
        
        return oddities if oddities else ["No unusual market oddities detected"]
    
    def _generate_attention_signals(self, score, flags):
        """Generate attention signals for traders"""
        signals = []
        
        if score > 0.7:
            signals.append("🚨 HIGH ATTENTION REQUIRED")
        elif score > 0.4:
            signals.append("⚠️ INCREASED MONITORING RECOMMENDED")
        else:
            signals.append("✅ NORMAL MONITORING SUFFICIENT")
        
        # Flag-specific signals
        if 'PRICE_VOLATILITY_EXTREME' in flags:
            signals.append("📈 Extreme price movements detected")
        if 'VOLUME_SPIKE_PATTERN' in flags:
            signals.append("📊 Unusual volume patterns observed")
        if 'RSI_EXTREME_CONDITION' in flags:
            signals.append("⚡ RSI in extreme territory")
        if 'PRICE_VOLUME_DIVERGENCE' in flags:
            signals.append("🔄 Price-volume divergence noted")
        
        return signals
