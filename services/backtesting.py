import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import yfinance as yf
from services.data_fetcher import DataFetcher
from services.ml_models import MLModelManager
import json

class BacktestingEngine:
    """Advanced backtesting engine for trading strategies"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.ml_manager = MLModelManager()
        
        # Available strategies
        self.strategies = {
            'buy_and_hold': self._buy_and_hold_strategy,
            'moving_average_crossover': self._ma_crossover_strategy,
            'rsi_mean_reversion': self._rsi_mean_reversion_strategy,
            'bollinger_bands': self._bollinger_bands_strategy,
            'momentum': self._momentum_strategy,
            'ml_signals': self._ml_signals_strategy,
            'oracle_guided': self._oracle_guided_strategy
        }
    
    def run_backtest(self, strategy, ticker, start_date, end_date, initial_capital=10000, **kwargs):
        """Run comprehensive backtest"""
        try:
            # Get data for backtesting period
            data = self._get_backtest_data(ticker, start_date, end_date)
            if data is None:
                return {'error': 'Failed to fetch data for backtesting'}
            
            # Run strategy
            if strategy not in self.strategies:
                return {'error': f'Strategy {strategy} not supported'}
            
            trades, portfolio_values = self.strategies[strategy](data, initial_capital, **kwargs)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(
                portfolio_values, trades, initial_capital, data
            )
            
            # Generate detailed results
            results = {
                'strategy': strategy,
                'ticker': ticker,
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'duration_days': (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
                },
                'initial_capital': initial_capital,
                'final_value': portfolio_values[-1] if portfolio_values else initial_capital,
                'performance': performance,
                'trades': trades,
                'portfolio_values': portfolio_values,
                'benchmark': self._calculate_benchmark(data, initial_capital),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return results
            
        except Exception as e:
            logging.error(f"Backtesting error: {str(e)}")
            return {'error': f'Backtesting failed: {str(e)}'}
    
    def _get_backtest_data(self, ticker, start_date, end_date):
        """Get data for backtesting period"""
        try:
            # Calculate period needed
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            # Get extra data for technical indicators
            buffer_start = start - timedelta(days=100)
            
            if ticker.endswith('-USD'):
                stock = yf.Ticker(ticker)
            else:
                stock = yf.Ticker(ticker)
            
            data = stock.history(start=buffer_start.strftime('%Y-%m-%d'), 
                               end=end.strftime('%Y-%m-%d'))
            
            if data.empty:
                return None
            
            # Add technical indicators
            data = self.data_fetcher._add_technical_indicators(data)
            
            # Trim to actual backtest period
            data = data[start:end]
            
            return data
            
        except Exception as e:
            logging.error(f"Error getting backtest data: {str(e)}")
            return None
    
    def _buy_and_hold_strategy(self, data, initial_capital, **kwargs):
        """Simple buy and hold strategy"""
        trades = []
        portfolio_values = []
        
        entry_price = data['Close'].iloc[0]
        shares = initial_capital / entry_price
        
        # Entry trade
        trades.append({
            'date': data.index[0].isoformat(),
            'action': 'BUY',
            'price': entry_price,
            'shares': shares,
            'value': initial_capital,
            'reason': 'Initial purchase'
        })
        
        # Calculate daily portfolio values
        for i, (date, row) in enumerate(data.iterrows()):
            portfolio_value = shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _ma_crossover_strategy(self, data, initial_capital, short_window=20, long_window=50):
        """Moving average crossover strategy"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        for i, (date, row) in enumerate(data.iterrows()):
            if i < long_window:  # Not enough data for signals
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            sma_short = data['Close'].iloc[i-short_window+1:i+1].mean()
            sma_long = data['Close'].iloc[i-long_window+1:i+1].mean()
            
            # Buy signal: short MA crosses above long MA
            if position == 'cash' and sma_short > sma_long:
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'BUY',
                    'price': row['Close'],
                    'shares': shares,
                    'value': shares * row['Close'],
                    'reason': 'MA crossover bullish'
                })
            
            # Sell signal: short MA crosses below long MA
            elif position == 'long' and sma_short < sma_long:
                cash = shares * row['Close']
                shares = 0
                position = 'cash'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'value': cash,
                    'reason': 'MA crossover bearish'
                })
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _rsi_mean_reversion_strategy(self, data, initial_capital, rsi_oversold=30, rsi_overbought=70):
        """RSI mean reversion strategy"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        for i, (date, row) in enumerate(data.iterrows()):
            if pd.isna(row['RSI']):
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            # Buy signal: RSI oversold
            if position == 'cash' and row['RSI'] < rsi_oversold:
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'BUY',
                    'price': row['Close'],
                    'shares': shares,
                    'value': shares * row['Close'],
                    'reason': f'RSI oversold ({row["RSI"]:.1f})'
                })
            
            # Sell signal: RSI overbought
            elif position == 'long' and row['RSI'] > rsi_overbought:
                cash = shares * row['Close']
                shares = 0
                position = 'cash'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'value': cash,
                    'reason': f'RSI overbought ({row["RSI"]:.1f})'
                })
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _bollinger_bands_strategy(self, data, initial_capital):
        """Bollinger Bands strategy"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        for i, (date, row) in enumerate(data.iterrows()):
            if pd.isna(row['BB_Upper']) or pd.isna(row['BB_Lower']):
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            # Buy signal: price touches lower Bollinger Band
            if position == 'cash' and row['Close'] <= row['BB_Lower']:
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'BUY',
                    'price': row['Close'],
                    'shares': shares,
                    'value': shares * row['Close'],
                    'reason': 'Price at lower Bollinger Band'
                })
            
            # Sell signal: price touches upper Bollinger Band
            elif position == 'long' and row['Close'] >= row['BB_Upper']:
                cash = shares * row['Close']
                shares = 0
                position = 'cash'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'value': cash,
                    'reason': 'Price at upper Bollinger Band'
                })
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _momentum_strategy(self, data, initial_capital, lookback=10, threshold=0.02):
        """Momentum strategy"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        for i, (date, row) in enumerate(data.iterrows()):
            if i < lookback:
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            # Calculate momentum
            momentum = (row['Close'] / data['Close'].iloc[i-lookback] - 1)
            
            # Buy signal: positive momentum above threshold
            if position == 'cash' and momentum > threshold:
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'BUY',
                    'price': row['Close'],
                    'shares': shares,
                    'value': shares * row['Close'],
                    'reason': f'Positive momentum ({momentum:.2%})'
                })
            
            # Sell signal: negative momentum below negative threshold
            elif position == 'long' and momentum < -threshold:
                cash = shares * row['Close']
                shares = 0
                position = 'cash'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'value': cash,
                    'reason': f'Negative momentum ({momentum:.2%})'
                })
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _ml_signals_strategy(self, data, initial_capital):
        """ML-based trading strategy"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        # Generate ML signals for each day
        for i, (date, row) in enumerate(data.iterrows()):
            if i < 50:  # Need enough data for ML models
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            # Get historical data up to current point
            historical_data = data.iloc[:i+1]
            
            # Generate trading signals
            try:
                signals = self.ml_manager.get_trading_signals(historical_data)
                overall_signal = signals.get('overall_signal', 'HOLD')
                confidence = signals.get('overall_confidence', 0.5)
                
                # Buy signal: ML recommends BUY with high confidence
                if position == 'cash' and overall_signal == 'BUY' and confidence > 0.7:
                    shares = cash / row['Close']
                    cash = 0
                    position = 'long'
                    
                    trades.append({
                        'date': date.isoformat(),
                        'action': 'BUY',
                        'price': row['Close'],
                        'shares': shares,
                        'value': shares * row['Close'],
                        'reason': f'ML BUY signal (confidence: {confidence:.2f})'
                    })
                
                # Sell signal: ML recommends SELL with high confidence
                elif position == 'long' and overall_signal == 'SELL' and confidence > 0.7:
                    cash = shares * row['Close']
                    shares = 0
                    position = 'cash'
                    
                    trades.append({
                        'date': date.isoformat(),
                        'action': 'SELL',
                        'price': row['Close'],
                        'shares': shares,
                        'value': cash,
                        'reason': f'ML SELL signal (confidence: {confidence:.2f})'
                    })
                    
            except Exception as e:
                logging.warning(f"ML signals failed for date {date}: {str(e)}")
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _oracle_guided_strategy(self, data, initial_capital):
        """Oracle-guided trading strategy (simplified)"""
        trades = []
        portfolio_values = []
        
        cash = initial_capital
        shares = 0
        position = 'cash'
        
        # Simulate Oracle guidance based on market conditions
        for i, (date, row) in enumerate(data.iterrows()):
            if i < 20:
                portfolio_value = cash + shares * row['Close']
                portfolio_values.append({
                    'date': date.isoformat(),
                    'value': portfolio_value,
                    'price': row['Close']
                })
                continue
            
            # Oracle factors (simplified)
            rsi = row.get('RSI', 50)
            volume_ratio = row.get('Volume_Ratio', 1)
            volatility = data['Close'].iloc[i-20:i].std() / data['Close'].iloc[i-20:i].mean()
            
            # Oracle buy signal: oversold + high volume + low volatility
            oracle_buy = (rsi < 35 and volume_ratio > 1.2 and volatility < 0.02)
            
            # Oracle sell signal: overbought + high volume + high volatility
            oracle_sell = (rsi > 70 and volume_ratio > 1.5 and volatility > 0.04)
            
            if position == 'cash' and oracle_buy:
                shares = cash / row['Close']
                cash = 0
                position = 'long'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'BUY',
                    'price': row['Close'],
                    'shares': shares,
                    'value': shares * row['Close'],
                    'reason': 'Oracle guided BUY'
                })
            
            elif position == 'long' and oracle_sell:
                cash = shares * row['Close']
                shares = 0
                position = 'cash'
                
                trades.append({
                    'date': date.isoformat(),
                    'action': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'value': cash,
                    'reason': 'Oracle guided SELL'
                })
            
            portfolio_value = cash + shares * row['Close']
            portfolio_values.append({
                'date': date.isoformat(),
                'value': portfolio_value,
                'price': row['Close']
            })
        
        return trades, portfolio_values
    
    def _calculate_performance_metrics(self, portfolio_values, trades, initial_capital, data):
        """Calculate comprehensive performance metrics"""
        if not portfolio_values:
            return {'error': 'No portfolio data available'}
        
        # Extract values
        values = [pv['value'] for pv in portfolio_values]
        dates = [pd.to_datetime(pv['date']) for pv in portfolio_values]
        
        # Basic metrics
        final_value = values[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        # Annualized return
        duration_years = (dates[-1] - dates[0]).days / 365.25
        annualized_return = (final_value / initial_capital) ** (1 / duration_years) - 1 if duration_years > 0 else 0
        
        # Volatility (annualized)
        returns = pd.Series(values).pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Assuming daily data
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        peak = pd.Series(values).expanding().max()
        drawdown = (pd.Series(values) - peak) / peak
        max_drawdown = drawdown.min()
        
        # Win rate and trade statistics
        profitable_trades = 0
        total_trades = len([t for t in trades if t['action'] == 'SELL'])
        
        if total_trades > 0:
            # Simple calculation - need to pair buy/sell trades for accurate calculation
            # This is a simplified version
            win_rate = 0.5  # Placeholder
        else:
            win_rate = 0
        
        return {
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'total_trades': total_trades,
            'final_value': float(final_value),
            'duration_years': float(duration_years)
        }
    
    def _calculate_benchmark(self, data, initial_capital):
        """Calculate buy-and-hold benchmark performance"""
        entry_price = data['Close'].iloc[0]
        exit_price = data['Close'].iloc[-1]
        benchmark_return = (exit_price - entry_price) / entry_price
        
        return {
            'strategy': 'Buy and Hold',
            'return': float(benchmark_return),
            'final_value': float(initial_capital * (1 + benchmark_return))
        }
    
    def get_strategy_descriptions(self):
        """Get descriptions of available strategies"""
        return {
            'buy_and_hold': 'Simple buy and hold strategy for baseline comparison',
            'moving_average_crossover': 'Buy when short MA crosses above long MA, sell when opposite',
            'rsi_mean_reversion': 'Buy when RSI is oversold, sell when overbought',
            'bollinger_bands': 'Buy at lower band, sell at upper band',
            'momentum': 'Follow price momentum with configurable lookback period',
            'ml_signals': 'Use machine learning models to generate trading signals',
            'oracle_guided': 'Mystical Oracle wisdom combined with technical analysis'
        }
