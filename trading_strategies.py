import numpy as np
import pandas as pd
import talib
from backend.data_fetcher import DataFetcher
import logging

class TradingStrategies:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        try:
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line
            return macd, signal_line, histogram
        except:
            return pd.Series([0] * len(prices), index=prices.index), \
                   pd.Series([0] * len(prices), index=prices.index), \
                   pd.Series([0] * len(prices), index=prices.index)

    def bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            return upper, middle, lower
        except:
            return pd.Series([0] * len(prices), index=prices.index), \
                   pd.Series([0] * len(prices), index=prices.index), \
                   pd.Series([0] * len(prices), index=prices.index)

    def moving_average_crossover(self, ticker):
        """Moving Average Crossover Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate moving averages
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            
            current_ma20 = df['MA_20'].iloc[-1]
            current_ma50 = df['MA_50'].iloc[-1]
            prev_ma20 = df['MA_20'].iloc[-2]
            prev_ma50 = df['MA_50'].iloc[-2]
            
            # Determine signal
            if current_ma20 > current_ma50 and prev_ma20 <= prev_ma50:
                signal = 'BUY'
                confidence = 75
            elif current_ma20 < current_ma50 and prev_ma20 >= prev_ma50:
                signal = 'SELL'
                confidence = 75
            elif current_ma20 > current_ma50:
                signal = 'HOLD_BULLISH'
                confidence = 60
            else:
                signal = 'HOLD_BEARISH'
                confidence = 60
            
            return {
                'strategy': 'Moving Average Crossover',
                'signal': signal,
                'confidence': confidence,
                'ma_20': round(current_ma20, 2),
                'ma_50': round(current_ma50, 2)
            }
        except Exception as e:
            logging.error(f"MA Crossover error for {ticker}: {str(e)}")
            return {'strategy': 'Moving Average Crossover', 'signal': 'HOLD', 'confidence': 50}

    def rsi_strategy(self, ticker):
        """RSI Overbought/Oversold Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            rsi = self.calculate_rsi(df['Close'])
            current_rsi = rsi.iloc[-1]
            
            if current_rsi < 30:
                signal = 'BUY'
                confidence = min(90, 30 + (30 - current_rsi) * 2)
            elif current_rsi > 70:
                signal = 'SELL'
                confidence = min(90, 30 + (current_rsi - 70) * 2)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'RSI',
                'signal': signal,
                'confidence': round(confidence, 1),
                'rsi': round(current_rsi, 2)
            }
        except Exception as e:
            logging.error(f"RSI strategy error for {ticker}: {str(e)}")
            return {'strategy': 'RSI', 'signal': 'HOLD', 'confidence': 50}

    def macd_strategy(self, ticker):
        """MACD Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            macd, signal_line, histogram = self.calculate_macd(df['Close'])
            
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            
            # MACD crossover signals
            if current_macd > current_signal and prev_macd <= prev_signal:
                signal = 'BUY'
                confidence = 70
            elif current_macd < current_signal and prev_macd >= prev_signal:
                signal = 'SELL'
                confidence = 70
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'MACD',
                'signal': signal,
                'confidence': confidence,
                'macd': round(current_macd, 4),
                'signal_line': round(current_signal, 4)
            }
        except Exception as e:
            logging.error(f"MACD strategy error for {ticker}: {str(e)}")
            return {'strategy': 'MACD', 'signal': 'HOLD', 'confidence': 50}

    def bollinger_bands_strategy(self, ticker):
        """Bollinger Bands Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            upper, middle, lower = self.bollinger_bands(df['Close'])
            current_price = df['Close'].iloc[-1]
            current_upper = upper.iloc[-1]
            current_lower = lower.iloc[-1]
            current_middle = middle.iloc[-1]
            
            # Calculate position within bands
            band_width = current_upper - current_lower
            position = (current_price - current_lower) / band_width if band_width > 0 else 0.5
            
            if position < 0.2:  # Near lower band
                signal = 'BUY'
                confidence = min(85, 50 + (0.2 - position) * 175)
            elif position > 0.8:  # Near upper band
                signal = 'SELL'
                confidence = min(85, 50 + (position - 0.8) * 175)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'Bollinger Bands',
                'signal': signal,
                'confidence': round(confidence, 1),
                'bb_position': round(position * 100, 1),
                'upper_band': round(current_upper, 2),
                'lower_band': round(current_lower, 2)
            }
        except Exception as e:
            logging.error(f"Bollinger Bands strategy error for {ticker}: {str(e)}")
            return {'strategy': 'Bollinger Bands', 'signal': 'HOLD', 'confidence': 50}

    def volume_strategy(self, ticker):
        """Volume-based Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate volume moving average
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            current_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume_MA'].iloc[-1]
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price change
            price_change = df['Close'].pct_change().iloc[-1]
            
            if volume_ratio > 1.5 and price_change > 0.02:
                signal = 'BUY'
                confidence = min(80, 50 + volume_ratio * 15)
            elif volume_ratio > 1.5 and price_change < -0.02:
                signal = 'SELL'
                confidence = min(80, 50 + volume_ratio * 15)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'Volume Analysis',
                'signal': signal,
                'confidence': round(confidence, 1),
                'volume_ratio': round(volume_ratio, 2),
                'price_change': round(price_change * 100, 2)
            }
        except Exception as e:
            logging.error(f"Volume strategy error for {ticker}: {str(e)}")
            return {'strategy': 'Volume Analysis', 'signal': 'HOLD', 'confidence': 50}

    def momentum_strategy(self, ticker):
        """Momentum Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate momentum indicators
            df['Returns_5'] = df['Close'].pct_change(periods=5)
            df['Returns_20'] = df['Close'].pct_change(periods=20)
            
            momentum_5 = df['Returns_5'].iloc[-1]
            momentum_20 = df['Returns_20'].iloc[-1]
            
            # Strong momentum in both timeframes
            if momentum_5 > 0.05 and momentum_20 > 0.1:
                signal = 'BUY'
                confidence = min(85, 60 + abs(momentum_5) * 250)
            elif momentum_5 < -0.05 and momentum_20 < -0.1:
                signal = 'SELL'
                confidence = min(85, 60 + abs(momentum_5) * 250)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'Momentum',
                'signal': signal,
                'confidence': round(confidence, 1),
                'momentum_5d': round(momentum_5 * 100, 2),
                'momentum_20d': round(momentum_20 * 100, 2)
            }
        except Exception as e:
            logging.error(f"Momentum strategy error for {ticker}: {str(e)}")
            return {'strategy': 'Momentum', 'signal': 'HOLD', 'confidence': 50}

    def support_resistance_strategy(self, ticker):
        """Support and Resistance Strategy"""
        try:
            df = self.data_fetcher.get_stock_data(ticker, period='6mo')
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            
            # Calculate support and resistance levels
            highs = df['High'].rolling(window=20).max()
            lows = df['Low'].rolling(window=20).min()
            
            current_price = df['Close'].iloc[-1]
            resistance = highs.iloc[-1]
            support = lows.iloc[-1]
            
            # Calculate distance from support/resistance
            distance_to_resistance = (resistance - current_price) / current_price
            distance_to_support = (current_price - support) / current_price
            
            if distance_to_support < 0.02:  # Near support
                signal = 'BUY'
                confidence = min(80, 60 + (0.02 - distance_to_support) * 1000)
            elif distance_to_resistance < 0.02:  # Near resistance
                signal = 'SELL'
                confidence = min(80, 60 + (0.02 - distance_to_resistance) * 1000)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'strategy': 'Support/Resistance',
                'signal': signal,
                'confidence': round(confidence, 1),
                'support': round(support, 2),
                'resistance': round(resistance, 2),
                'current_price': round(current_price, 2)
            }
        except Exception as e:
            logging.error(f"Support/Resistance strategy error for {ticker}: {str(e)}")
            return {'strategy': 'Support/Resistance', 'signal': 'HOLD', 'confidence': 50}

    def get_all_signals(self, ticker):
        """Get signals from all strategies"""
        try:
            strategies = [
                self.moving_average_crossover,
                self.rsi_strategy,
                self.macd_strategy,
                self.bollinger_bands_strategy,
                self.volume_strategy,
                self.momentum_strategy,
                self.support_resistance_strategy
            ]
            
            signals = []
            buy_votes = 0
            sell_votes = 0
            total_confidence = 0
            
            for strategy_func in strategies:
                try:
                    result = strategy_func(ticker)
                    signals.append(result)
                    
                    if result['signal'] in ['BUY', 'HOLD_BULLISH']:
                        buy_votes += 1
                    elif result['signal'] in ['SELL', 'HOLD_BEARISH']:
                        sell_votes += 1
                    
                    total_confidence += result.get('confidence', 50)
                except Exception as e:
                    logging.error(f"Strategy error: {str(e)}")
                    signals.append({
                        'strategy': 'Error',
                        'signal': 'HOLD',
                        'confidence': 50
                    })
            
            # Determine overall signal
            if buy_votes > sell_votes + 2:
                overall_signal = 'BUY'
            elif sell_votes > buy_votes + 2:
                overall_signal = 'SELL'
            else:
                overall_signal = 'HOLD'
            
            avg_confidence = total_confidence / len(signals) if signals else 50
            
            return {
                'overall_signal': overall_signal,
                'overall_confidence': round(avg_confidence, 1),
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'individual_strategies': signals
            }
        except Exception as e:
            logging.error(f"Error getting all signals for {ticker}: {str(e)}")
            return {
                'overall_signal': 'HOLD',
                'overall_confidence': 50,
                'buy_votes': 0,
                'sell_votes': 0,
                'individual_strategies': []
            }

    def analyze_options(self, options_data):
        """Analyze options for strategy recommendations"""
        try:
            if 'error' in options_data:
                return {'error': options_data['error']}
            
            current_price = options_data.get('current_price', 0)
            atm_call = options_data.get('atm_call')
            atm_put = options_data.get('atm_put')
            
            recommendations = []
            
            if atm_call and atm_put:
                call_price = atm_call.get('lastPrice', 0)
                put_price = atm_put.get('lastPrice', 0)
                call_iv = atm_call.get('impliedVolatility', 0)
                put_iv = atm_put.get('impliedVolatility', 0)
                
                # Put-Call Ratio Analysis
                put_call_ratio = put_price / call_price if call_price > 0 else 1
                
                if put_call_ratio > 1.2:
                    recommendations.append({
                        'strategy': 'Bullish Call Spread',
                        'reason': 'High put-call ratio suggests oversold condition',
                        'confidence': 70
                    })
                elif put_call_ratio < 0.8:
                    recommendations.append({
                        'strategy': 'Protective Put',
                        'reason': 'Low put-call ratio suggests potential downside protection needed',
                        'confidence': 65
                    })
                
                # Implied Volatility Analysis
                avg_iv = (call_iv + put_iv) / 2
                if avg_iv > 0.3:
                    recommendations.append({
                        'strategy': 'Iron Condor',
                        'reason': 'High implied volatility favors premium selling strategies',
                        'confidence': 75
                    })
                elif avg_iv < 0.15:
                    recommendations.append({
                        'strategy': 'Long Straddle',
                        'reason': 'Low implied volatility suggests potential for increased volatility',
                        'confidence': 70
                    })
            
            if not recommendations:
                recommendations.append({
                    'strategy': 'Hold Cash',
                    'reason': 'Insufficient options data for clear strategy',
                    'confidence': 50
                })
            
            return {
                'current_price': current_price,
                'put_call_ratio': round(put_call_ratio, 2) if 'put_call_ratio' in locals() else None,
                'avg_implied_volatility': round(avg_iv * 100, 1) if 'avg_iv' in locals() else None,
                'recommendations': recommendations,
                'expiration_date': options_data.get('expiration_date')
            }
        except Exception as e:
            logging.error(f"Options analysis error: {str(e)}")
            return {'error': str(e)}
