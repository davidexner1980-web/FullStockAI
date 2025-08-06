import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from .data_fetcher import DataFetcher
from .prediction_engine import PredictionEngine

class BacktestingEngine:
    """Backtesting engine for strategy validation"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.prediction_engine = PredictionEngine()
    
    def run_backtest(self, ticker, strategy, start_date, end_date, initial_capital=10000):
        """Run backtest for a trading strategy"""
        try:
            # Convert date strings to datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get historical data
            period = self._calculate_period(start_dt, end_dt)
            data = self.data_fetcher.get_stock_data(ticker, period=period)
            
            # Filter data by date range
            data = data.loc[start_dt:end_dt]
            
            if len(data) < 30:
                raise ValueError("Insufficient data for backtesting")
            
            # Run strategy-specific backtest
            if strategy == 'buy_and_hold':
                results = self._backtest_buy_and_hold(data, initial_capital)
            elif strategy == 'moving_average_crossover':
                results = self._backtest_ma_crossover(data, initial_capital)
            elif strategy == 'rsi_mean_reversion':
                results = self._backtest_rsi_strategy(data, initial_capital)
            elif strategy == 'bollinger_bands':
                results = self._backtest_bollinger_strategy(data, initial_capital)
            elif strategy == 'momentum':
                results = self._backtest_momentum_strategy(data, initial_capital)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(results, data)
            
            return {
                'ticker': ticker,
                'strategy': strategy,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_capital': performance['final_capital'],
                'total_return': performance['total_return'],
                'annualized_return': performance['annualized_return'],
                'sharpe_ratio': performance['sharpe_ratio'],
                'max_drawdown': performance['max_drawdown'],
                'volatility': performance['volatility'],
                'win_rate': performance['win_rate'],
                'trades': performance['trades'],
                'daily_returns': results['daily_returns'][:100],  # Limit for response size
                'equity_curve': results['equity_curve'][:100],
                'signals': results['signals'][:100]
            }
            
        except Exception as e:
            logging.error(f"Backtesting error: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_period(self, start_dt, end_dt):
        """Calculate appropriate period string for yfinance"""
        days_diff = (end_dt - start_dt).days
        
        if days_diff <= 7:
            return '1mo'
        elif days_diff <= 60:
            return '3mo'
        elif days_diff <= 180:
            return '6mo'
        elif days_diff <= 365:
            return '1y'
        elif days_diff <= 730:
            return '2y'
        else:
            return '5y'
    
    def _backtest_buy_and_hold(self, data, initial_capital):
        """Backtest buy and hold strategy"""
        entry_price = data['Close'].iloc[0]
        shares = initial_capital / entry_price
        
        equity_curve = shares * data['Close']
        daily_returns = equity_curve.pct_change().dropna()
        
        signals = ['BUY'] + ['HOLD'] * (len(data) - 1)
        
        return {
            'equity_curve': equity_curve.tolist(),
            'daily_returns': daily_returns.tolist(),
            'signals': signals
        }
    
    def _backtest_ma_crossover(self, data, initial_capital):
        """Backtest moving average crossover strategy"""
        equity = initial_capital
        position = 0
        equity_curve = []
        daily_returns = []
        signals = []
        trades = []
        
        for i in range(len(data)):
            current_price = data['Close'].iloc[i]
            
            if i == 0:
                equity_curve.append(equity)
                daily_returns.append(0)
                signals.append('HOLD')
                continue
            
            # Check for crossover signal
            if i >= 20:  # Need 20 days for MA
                ma_short = data['SMA_10'].iloc[i]
                ma_long = data['SMA_20'].iloc[i]
                ma_short_prev = data['SMA_10'].iloc[i-1]
                ma_long_prev = data['SMA_20'].iloc[i-1]
                
                # Buy signal: short MA crosses above long MA
                if ma_short > ma_long and ma_short_prev <= ma_long_prev and position == 0:
                    position = equity / current_price
                    equity = 0
                    signals.append('BUY')
                    trades.append({'type': 'BUY', 'price': current_price, 'date': data.index[i]})
                
                # Sell signal: short MA crosses below long MA
                elif ma_short < ma_long and ma_short_prev >= ma_long_prev and position > 0:
                    equity = position * current_price
                    position = 0
                    signals.append('SELL')
                    trades.append({'type': 'SELL', 'price': current_price, 'date': data.index[i]})
                
                else:
                    signals.append('HOLD')
            else:
                signals.append('HOLD')
            
            # Calculate current equity
            current_equity = equity + (position * current_price)
            equity_curve.append(current_equity)
            
            # Calculate daily return
            if len(equity_curve) > 1:
                daily_return = (current_equity - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)
        
        return {
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'signals': signals,
            'trades': trades
        }
    
    def _backtest_rsi_strategy(self, data, initial_capital):
        """Backtest RSI mean reversion strategy"""
        equity = initial_capital
        position = 0
        equity_curve = []
        daily_returns = []
        signals = []
        trades = []
        
        for i in range(len(data)):
            current_price = data['Close'].iloc[i]
            
            if i == 0:
                equity_curve.append(equity)
                daily_returns.append(0)
                signals.append('HOLD')
                continue
            
            # RSI strategy
            if i >= 14:  # Need 14 days for RSI
                rsi = data['RSI'].iloc[i]
                
                # Buy signal: RSI < 30 (oversold)
                if rsi < 30 and position == 0:
                    position = equity / current_price
                    equity = 0
                    signals.append('BUY')
                    trades.append({'type': 'BUY', 'price': current_price, 'date': data.index[i]})
                
                # Sell signal: RSI > 70 (overbought)
                elif rsi > 70 and position > 0:
                    equity = position * current_price
                    position = 0
                    signals.append('SELL')
                    trades.append({'type': 'SELL', 'price': current_price, 'date': data.index[i]})
                
                else:
                    signals.append('HOLD')
            else:
                signals.append('HOLD')
            
            current_equity = equity + (position * current_price)
            equity_curve.append(current_equity)
            
            if len(equity_curve) > 1:
                daily_return = (current_equity - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)
        
        return {
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'signals': signals,
            'trades': trades
        }
    
    def _backtest_bollinger_strategy(self, data, initial_capital):
        """Backtest Bollinger Bands strategy"""
        equity = initial_capital
        position = 0
        equity_curve = []
        daily_returns = []
        signals = []
        trades = []
        
        for i in range(len(data)):
            current_price = data['Close'].iloc[i]
            
            if i == 0:
                equity_curve.append(equity)
                daily_returns.append(0)
                signals.append('HOLD')
                continue
            
            # Bollinger Bands strategy
            if i >= 20:  # Need 20 days for Bollinger Bands
                bb_upper = data['BB_Upper'].iloc[i]
                bb_lower = data['BB_Lower'].iloc[i]
                
                # Buy signal: price touches lower band
                if current_price <= bb_lower and position == 0:
                    position = equity / current_price
                    equity = 0
                    signals.append('BUY')
                    trades.append({'type': 'BUY', 'price': current_price, 'date': data.index[i]})
                
                # Sell signal: price touches upper band
                elif current_price >= bb_upper and position > 0:
                    equity = position * current_price
                    position = 0
                    signals.append('SELL')
                    trades.append({'type': 'SELL', 'price': current_price, 'date': data.index[i]})
                
                else:
                    signals.append('HOLD')
            else:
                signals.append('HOLD')
            
            current_equity = equity + (position * current_price)
            equity_curve.append(current_equity)
            
            if len(equity_curve) > 1:
                daily_return = (current_equity - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)
        
        return {
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'signals': signals,
            'trades': trades
        }
    
    def _backtest_momentum_strategy(self, data, initial_capital):
        """Backtest momentum strategy"""
        equity = initial_capital
        position = 0
        equity_curve = []
        daily_returns = []
        signals = []
        trades = []
        
        for i in range(len(data)):
            current_price = data['Close'].iloc[i]
            
            if i == 0:
                equity_curve.append(equity)
                daily_returns.append(0)
                signals.append('HOLD')
                continue
            
            # Momentum strategy (10-day momentum)
            if i >= 10:
                momentum = data['Close'].pct_change(10).iloc[i]
                
                # Buy signal: positive momentum > 5%
                if momentum > 0.05 and position == 0:
                    position = equity / current_price
                    equity = 0
                    signals.append('BUY')
                    trades.append({'type': 'BUY', 'price': current_price, 'date': data.index[i]})
                
                # Sell signal: negative momentum < -5%
                elif momentum < -0.05 and position > 0:
                    equity = position * current_price
                    position = 0
                    signals.append('SELL')
                    trades.append({'type': 'SELL', 'price': current_price, 'date': data.index[i]})
                
                else:
                    signals.append('HOLD')
            else:
                signals.append('HOLD')
            
            current_equity = equity + (position * current_price)
            equity_curve.append(current_equity)
            
            if len(equity_curve) > 1:
                daily_return = (current_equity - equity_curve[-2]) / equity_curve[-2]
                daily_returns.append(daily_return)
            else:
                daily_returns.append(0)
        
        return {
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'signals': signals,
            'trades': trades
        }
    
    def _calculate_performance_metrics(self, results, data):
        """Calculate comprehensive performance metrics"""
        equity_curve = results['equity_curve']
        daily_returns = results['daily_returns']
        
        if not equity_curve or len(equity_curve) < 2:
            return {'error': 'Insufficient data for performance calculation'}
        
        initial_capital = equity_curve[0]
        final_capital = equity_curve[-1]
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Annualized return
        days = len(equity_curve)
        years = days / 252  # Trading days per year
        annualized_return = (final_capital / initial_capital) ** (1 / years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # Win rate
        trades = results.get('trades', [])
        if len(trades) >= 2:
            winning_trades = 0
            for i in range(1, len(trades), 2):  # Pairs of buy/sell
                if i < len(trades):
                    buy_price = trades[i-1]['price']
                    sell_price = trades[i]['price']
                    if sell_price > buy_price:
                        winning_trades += 1
            
            win_rate = winning_trades / (len(trades) // 2) if len(trades) >= 2 else 0
        else:
            win_rate = 0
        
        return {
            'final_capital': final_capital,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': len(trades)
        }
    
    def get_strategy_comparison(self, ticker, start_date, end_date):
        """Compare multiple strategies"""
        try:
            strategies = [
                'buy_and_hold',
                'moving_average_crossover',
                'rsi_mean_reversion',
                'bollinger_bands',
                'momentum'
            ]
            
            results = {}
            
            for strategy in strategies:
                result = self.run_backtest(ticker, strategy, start_date, end_date)
                if 'error' not in result:
                    results[strategy] = {
                        'total_return': result['total_return'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'max_drawdown': result['max_drawdown'],
                        'win_rate': result['win_rate']
                    }
            
            # Rank strategies by Sharpe ratio
            ranked_strategies = sorted(
                results.items(),
                key=lambda x: x[1]['sharpe_ratio'],
                reverse=True
            )
            
            return {
                'ticker': ticker,
                'period': f"{start_date} to {end_date}",
                'strategy_results': results,
                'ranked_strategies': ranked_strategies,
                'best_strategy': ranked_strategies[0][0] if ranked_strategies else None
            }
            
        except Exception as e:
            logging.error(f"Strategy comparison error: {str(e)}")
            return {'error': str(e)}
