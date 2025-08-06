import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import requests
from services.data_fetcher import DataFetcher
from services.ml_models import MLModelManager

class CryptoService:
    """Cryptocurrency prediction and analysis service"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.ml_manager = MLModelManager()
        
        # Major cryptocurrencies supported
        self.supported_cryptos = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'Binance Coin',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'DOGE': 'Dogecoin',
            'MATIC': 'Polygon',
            'SOL': 'Solana',
            'DOT': 'Polkadot',
            'AVAX': 'Avalanche',
            'SHIB': 'Shiba Inu',
            'LTC': 'Litecoin',
            'ATOM': 'Cosmos',
            'LINK': 'Chainlink',
            'UNI': 'Uniswap'
        }
        
        # Crypto-specific indicators
        self.crypto_fear_greed_api = "https://api.alternative.me/fng/"
    
    def get_supported_cryptos(self):
        """Return list of supported cryptocurrencies"""
        return [
            {
                'symbol': symbol,
                'name': name,
                'yahoo_symbol': f"{symbol}-USD"
            }
            for symbol, name in self.supported_cryptos.items()
        ]
    
    def predict_crypto(self, symbol):
        """Generate comprehensive cryptocurrency prediction"""
        try:
            symbol = symbol.upper()
            
            if symbol not in self.supported_cryptos:
                return {'error': f'Cryptocurrency {symbol} not supported'}
            
            # Get crypto data
            data = self.data_fetcher.get_crypto_data(symbol)
            if data is None:
                return {'error': f'Failed to fetch data for {symbol}'}
            
            # Generate predictions using all models
            rf_pred = self.ml_manager.predict_random_forest(data)
            lstm_pred = self.ml_manager.predict_lstm(data)
            xgb_pred = self.ml_manager.predict_xgboost(data)
            
            current_price = data['Close'].iloc[-1]
            
            # Crypto-specific analysis
            volatility_analysis = self._analyze_crypto_volatility(data)
            market_sentiment = self._get_crypto_market_sentiment(symbol)
            technical_analysis = self._crypto_technical_analysis(data)
            
            # Ensemble prediction with crypto adjustments
            predictions = []
            confidences = []
            
            if 'prediction' in rf_pred:
                predictions.append(rf_pred['prediction'])
                confidences.append(rf_pred['confidence'])
            
            if 'prediction' in lstm_pred:
                predictions.append(lstm_pred['prediction'])
                confidences.append(lstm_pred['confidence'])
            
            if 'prediction' in xgb_pred:
                predictions.append(xgb_pred['prediction'])
                confidences.append(xgb_pred['confidence'])
            
            if not predictions:
                return {'error': 'All prediction models failed'}
            
            ensemble_prediction = np.mean(predictions)
            ensemble_confidence = np.mean(confidences)
            
            # Calculate price targets
            price_targets = self._calculate_crypto_price_targets(
                current_price, ensemble_prediction, volatility_analysis
            )
            
            # Risk assessment
            risk_analysis = self._assess_crypto_risk(data, symbol)
            
            return {
                'symbol': symbol,
                'name': self.supported_cryptos[symbol],
                'current_price': float(current_price),
                'predictions': {
                    'random_forest': rf_pred,
                    'lstm': lstm_pred,
                    'xgboost': xgb_pred,
                    'ensemble': {
                        'prediction': float(ensemble_prediction),
                        'confidence': float(ensemble_confidence),
                        'price_change': float(ensemble_prediction - current_price),
                        'price_change_percent': float((ensemble_prediction - current_price) / current_price * 100)
                    }
                },
                'price_targets': price_targets,
                'volatility_analysis': volatility_analysis,
                'market_sentiment': market_sentiment,
                'technical_analysis': technical_analysis,
                'risk_analysis': risk_analysis,
                'trading_signals': self._generate_crypto_signals(data, symbol),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error predicting crypto {symbol}: {str(e)}")
            return {'error': f'Crypto prediction failed: {str(e)}'}
    
    def _analyze_crypto_volatility(self, data):
        """Analyze cryptocurrency volatility patterns"""
        try:
            returns = data['Close'].pct_change().dropna()
            
            # Calculate various volatility measures
            daily_vol = returns.std()
            weekly_vol = returns.rolling(7).std().iloc[-1]
            monthly_vol = returns.rolling(30).std().iloc[-1] if len(returns) >= 30 else daily_vol
            
            # Volatility percentiles
            vol_percentile = (returns.rolling(60).std().iloc[-1] / returns.rolling(252).std().iloc[-1] 
                            if len(returns) >= 252 else 0.5)
            
            # Determine volatility regime
            if vol_percentile > 0.8:
                regime = "HIGH"
            elif vol_percentile < 0.2:
                regime = "LOW"
            else:
                regime = "MEDIUM"
            
            return {
                'daily_volatility': float(daily_vol * 100),
                'weekly_volatility': float(weekly_vol * 100),
                'monthly_volatility': float(monthly_vol * 100),
                'volatility_percentile': float(vol_percentile),
                'volatility_regime': regime,
                'annualized_volatility': float(daily_vol * np.sqrt(365) * 100)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing crypto volatility: {str(e)}")
            return {'error': 'Volatility analysis failed'}
    
    def _get_crypto_market_sentiment(self, symbol):
        """Get crypto market sentiment indicators"""
        try:
            sentiment = {
                'fear_greed_index': self._get_fear_greed_index(),
                'social_sentiment': 'neutral',  # Placeholder for social media sentiment
                'institutional_flow': 'neutral',  # Placeholder for institutional data
                'network_activity': 'moderate'   # Placeholder for on-chain metrics
            }
            
            # Symbol-specific sentiment adjustments
            if symbol in ['BTC', 'ETH']:
                sentiment['market_dominance'] = 'high'
            elif symbol in ['DOGE', 'SHIB']:
                sentiment['meme_factor'] = 'high'
            else:
                sentiment['altcoin_cycle'] = 'active'
            
            return sentiment
            
        except Exception as e:
            logging.error(f"Error getting crypto sentiment: {str(e)}")
            return {'sentiment': 'neutral', 'error': 'Sentiment data unavailable'}
    
    def _get_fear_greed_index(self):
        """Fetch crypto Fear & Greed Index"""
        try:
            response = requests.get(self.crypto_fear_greed_api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    index_value = int(data['data'][0]['value'])
                    classification = data['data'][0]['value_classification']
                    return {
                        'value': index_value,
                        'classification': classification,
                        'timestamp': data['data'][0]['timestamp']
                    }
        except Exception as e:
            logging.error(f"Error fetching Fear & Greed Index: {str(e)}")
        
        # Return neutral if API fails
        return {'value': 50, 'classification': 'neutral', 'timestamp': None}
    
    def _crypto_technical_analysis(self, data):
        """Crypto-specific technical analysis"""
        try:
            current_price = data['Close'].iloc[-1]
            
            # Support and resistance levels
            recent_highs = data['High'].rolling(20).max().iloc[-1]
            recent_lows = data['Low'].rolling(20).min().iloc[-1]
            
            # Moving average analysis
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]
            
            # RSI analysis
            rsi = data['RSI'].iloc[-1]
            
            # Volume analysis
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            momentum_5d = (current_price / data['Close'].iloc[-6] - 1) * 100 if len(data) > 5 else 0
            momentum_10d = (current_price / data['Close'].iloc[-11] - 1) * 100 if len(data) > 10 else 0
            
            return {
                'support_level': float(recent_lows),
                'resistance_level': float(recent_highs),
                'sma_20_signal': 'bullish' if current_price > sma_20 else 'bearish',
                'sma_50_signal': 'bullish' if current_price > sma_50 else 'bearish',
                'rsi_signal': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral',
                'volume_analysis': {
                    'volume_spike': float(volume_spike),
                    'volume_trend': 'high' if volume_spike > 1.5 else 'low' if volume_spike < 0.5 else 'normal'
                },
                'momentum': {
                    '5_day': float(momentum_5d),
                    '10_day': float(momentum_10d)
                }
            }
            
        except Exception as e:
            logging.error(f"Error in crypto technical analysis: {str(e)}")
            return {'error': 'Technical analysis failed'}
    
    def _calculate_crypto_price_targets(self, current_price, prediction, volatility_analysis):
        """Calculate price targets based on volatility"""
        try:
            vol = volatility_analysis.get('daily_volatility', 5) / 100
            
            # Conservative targets (1 standard deviation)
            conservative_upper = prediction * (1 + vol)
            conservative_lower = prediction * (1 - vol)
            
            # Aggressive targets (2 standard deviations)
            aggressive_upper = prediction * (1 + 2 * vol)
            aggressive_lower = prediction * (1 - 2 * vol)
            
            return {
                'conservative': {
                    'upper': float(conservative_upper),
                    'lower': float(conservative_lower),
                    'upside': float((conservative_upper - current_price) / current_price * 100),
                    'downside': float((conservative_lower - current_price) / current_price * 100)
                },
                'aggressive': {
                    'upper': float(aggressive_upper),
                    'lower': float(aggressive_lower),
                    'upside': float((aggressive_upper - current_price) / current_price * 100),
                    'downside': float((aggressive_lower - current_price) / current_price * 100)
                }
            }
            
        except Exception as e:
            logging.error(f"Error calculating price targets: {str(e)}")
            return {'error': 'Price target calculation failed'}
    
    def _assess_crypto_risk(self, data, symbol):
        """Assess cryptocurrency investment risk"""
        try:
            # Volatility risk
            returns = data['Close'].pct_change().dropna()
            var_95 = np.percentile(returns, 5) * 100  # Value at Risk (95% confidence)
            
            # Liquidity risk (based on volume)
            avg_volume = data['Volume'].rolling(30).mean().iloc[-1]
            recent_volume = data['Volume'].iloc[-5:].mean()
            liquidity_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Market cap category risk
            market_cap_risk = self._get_market_cap_risk(symbol)
            
            # Overall risk score (0-100, higher = riskier)
            volatility_score = min(abs(var_95) * 2, 50)  # Cap at 50
            liquidity_score = max(0, min(30, (2 - liquidity_ratio) * 15))  # 0-30 scale
            market_cap_score = market_cap_risk
            
            total_risk_score = volatility_score + liquidity_score + market_cap_score
            
            # Risk category
            if total_risk_score < 30:
                risk_category = "LOW"
            elif total_risk_score < 60:
                risk_category = "MEDIUM"
            else:
                risk_category = "HIGH"
            
            return {
                'total_risk_score': float(total_risk_score),
                'risk_category': risk_category,
                'value_at_risk_95': float(var_95),
                'liquidity_ratio': float(liquidity_ratio),
                'market_cap_risk': market_cap_risk,
                'risk_factors': self._identify_risk_factors(symbol, total_risk_score)
            }
            
        except Exception as e:
            logging.error(f"Error assessing crypto risk: {str(e)}")
            return {'error': 'Risk assessment failed'}
    
    def _get_market_cap_risk(self, symbol):
        """Assess market cap related risk"""
        # Large cap cryptos (lower risk)
        large_cap = ['BTC', 'ETH', 'BNB']
        # Mid cap cryptos (medium risk)
        mid_cap = ['XRP', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LTC', 'LINK', 'UNI', 'ATOM']
        # Small/meme cap (higher risk)
        small_cap = ['DOGE', 'SHIB']
        
        if symbol in large_cap:
            return 5  # Low risk
        elif symbol in mid_cap:
            return 15  # Medium risk
        else:
            return 25  # High risk
    
    def _identify_risk_factors(self, symbol, risk_score):
        """Identify specific risk factors"""
        factors = []
        
        if risk_score > 70:
            factors.append("Extreme volatility warning")
        elif risk_score > 50:
            factors.append("High volatility environment")
        
        if symbol in ['DOGE', 'SHIB']:
            factors.append("Meme coin - social sentiment dependent")
        
        if symbol not in ['BTC', 'ETH', 'BNB']:
            factors.append("Altcoin correlation risk")
        
        return factors
    
    def _generate_crypto_signals(self, data, symbol):
        """Generate crypto-specific trading signals"""
        try:
            signals = self.ml_manager.get_trading_signals(data)
            
            # Add crypto-specific adjustments
            if symbol in ['BTC', 'ETH']:
                # Major cryptos - more weight to technical analysis
                signals['crypto_dominance'] = 'high'
            elif symbol in ['DOGE', 'SHIB']:
                # Meme coins - sentiment driven
                signals['meme_sentiment'] = 'monitor social media closely'
            
            # Add volatility-adjusted confidence
            volatility = data['Close'].pct_change().std() * 100
            if volatility > 10:  # High volatility
                # Reduce confidence in signals during high volatility
                for signal_name in signals.get('individual_signals', {}):
                    signals['individual_signals'][signal_name]['confidence'] *= 0.8
                signals['overall_confidence'] *= 0.8
                signals['volatility_warning'] = True
            
            return signals
            
        except Exception as e:
            logging.error(f"Error generating crypto signals: {str(e)}")
            return {'error': 'Signal generation failed'}
