import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from data_fetcher import DataFetcher
from trading_strategies import TradingStrategies

class BacktestingEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = DataFetcher()
        self.trading_strategies = TradingStrategies()
        
        # Backtesting parameters
        self.commission_rate = 0.001  # 0.1% commission per trade
        self.slippage = 0.0005  # 0.05% slippage
        self.min_trade_size = 100  # Minimum trade value
    
    def run_backtest(self, symbol: str, strategy_name: str, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None,
                     initial_capital: float = 10000) -> Dict:
        """
        Run backtest for a specific strategy
        
        Args:
            symbol: Stock symbol to backtest
            strategy_name: Name of the strategy to test
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            initial_capital: Initial capital for backtest
            
        Returns:
            Dictionary with backtest results
        """
        try:
            symbol = symbol.upper()
            
            # Get historical data
            if start_date and end_date:
                # Custom date range
                data = self._get_data_for_period(symbol, start_date, end_date)
            else:
                # Default to 1 year
                data = self.data_fetcher.get_stock_data(symbol, period="1y")
            
            if data is None or data.empty:
                return {'error': f'No data available for {symbol}'}
            
            # Add technical indicators
            data = self.data_fetcher.calculate_technical_indicators(data)
            
            # Run the backtest
            if strategy_name == 'moving_average':
                results = self._backtest_moving_average(data, initial_capital)
            elif strategy_name == 'rsi':
                results = self._backtest_rsi(data, initial_capital)
            elif strategy_name == 'macd':
                results = self._backtest_macd(data, initial_capital)
            elif strategy_name == 'bollinger_bands':
                results = self._backtest_bollinger_bands(data, initial_capital)
            elif strategy_name == 'momentum':
                results = self._backtest_momentum(data, initial_capital)
            elif strategy_name == 'buy_and_hold':
                results = self._backtest_buy_and_hold(data, initial_capital)
            else:
                return {'error': f'Unknown strategy: {strategy_name}'}
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(results['trades'], initial_capital)
            
            # Add benchmark comparison (buy and hold)
            benchmark = self._backtest_buy_and_hold(data, initial_capital)
            
            return {
                'symbol': symbol,
                'strategy': strategy_name,
                'period': {
                    'start': data.index[0].strftime('%Y-%m-%d'),
                    'end': data.index[-1].strftime('%Y-%m-%d'),
                    'days': len(data)
                },
                'initial_capital': initial_capital,
                'final_capital': results['final_capital'],
                'total_return': results['total_return'],
                'total_return_pct': results['total_return_pct'],
                'trades': results['trades'],
                'performance_metrics': performance_metrics,
                'benchmark': {
                    'strategy': 'Buy and Hold',
                    'final_capital': benchmark['final_capital'],
                    'total_return_pct': benchmark['total_return_pct']
                },
                'backtest_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error running backtest for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _get_data_for_period(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get data for a specific period"""
        try:
            # Get extended data and filter
            data = self.data_fetcher.get_stock_data(symbol, period="2y")
            if data is None or data.empty:
                return pd.DataFrame()
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            mask = (data.index >= start_dt) & (data.index <= end_dt)
            return data.loc[mask]
            
        except Exception as e:
            self.logger.error(f"Error getting data for period: {str(e)}")
            return pd.DataFrame()
    
    def _backtest_moving_average(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest moving average crossover strategy"""
        trades = []
        capital = initial_capital
        position = 0  # 0 = no position, 1 = long position
        shares = 0
        
        for i in range(1, len(data)):
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            # Check if we have the required indicators
            if pd.isna(data['SMA_10'].iloc[i]) or pd.isna(data['SMA_20'].iloc[i]):
                continue
            
            sma_10 = data['SMA_10'].iloc[i]
            sma_20 = data['SMA_20'].iloc[i]
            prev_sma_10 = data['SMA_10'].iloc[i-1]
            prev_sma_20 = data['SMA_20'].iloc[i-1]
            
            # Buy signal: SMA 10 crosses above SMA 20
            if sma_10 > sma_20 and prev_sma_10 <= prev_sma_20 and position == 0:
                shares_to_buy = int((capital * 0.95) / current_price)  # Use 95% of capital
                if shares_to_buy * current_price >= self.min_trade_size:
                    cost = shares_to_buy * current_price * (1 + self.commission_rate + self.slippage)
                    if cost <= capital:
                        shares = shares_to_buy
                        capital -= cost
                        position = 1
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'value': shares * current_price,
                            'commission': shares * current_price * self.commission_rate,
                            'capital_remaining': capital
                        })
            
            # Sell signal: SMA 10 crosses below SMA 20
            elif sma_10 < sma_20 and prev_sma_10 >= prev_sma_20 and position == 1:
                proceeds = shares * current_price * (1 - self.commission_rate - self.slippage)
                capital += proceeds
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'value': shares * current_price,
                    'commission': shares * current_price * self.commission_rate,
                    'capital_remaining': capital
                })
                
                shares = 0
                position = 0
        
        # Close position at end if still holding
        if position == 1:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += proceeds
            
            trades.append({
                'date': data.index[-1].strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': final_price,
                'shares': shares,
                'value': shares * final_price,
                'commission': shares * final_price * self.commission_rate,
                'capital_remaining': capital
            })
        
        final_capital = capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _backtest_rsi(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest RSI strategy"""
        trades = []
        capital = initial_capital
        position = 0
        shares = 0
        
        for i in range(1, len(data)):
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            if pd.isna(data['RSI'].iloc[i]):
                continue
            
            rsi = data['RSI'].iloc[i]
            
            # Buy signal: RSI < 30 (oversold)
            if rsi < 30 and position == 0:
                shares_to_buy = int((capital * 0.95) / current_price)
                if shares_to_buy * current_price >= self.min_trade_size:
                    cost = shares_to_buy * current_price * (1 + self.commission_rate + self.slippage)
                    if cost <= capital:
                        shares = shares_to_buy
                        capital -= cost
                        position = 1
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'value': shares * current_price,
                            'commission': shares * current_price * self.commission_rate,
                            'capital_remaining': capital
                        })
            
            # Sell signal: RSI > 70 (overbought)
            elif rsi > 70 and position == 1:
                proceeds = shares * current_price * (1 - self.commission_rate - self.slippage)
                capital += proceeds
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'value': shares * current_price,
                    'commission': shares * current_price * self.commission_rate,
                    'capital_remaining': capital
                })
                
                shares = 0
                position = 0
        
        # Close position at end if still holding
        if position == 1:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += proceeds
            
            trades.append({
                'date': data.index[-1].strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': final_price,
                'shares': shares,
                'value': shares * final_price,
                'commission': shares * final_price * self.commission_rate,
                'capital_remaining': capital
            })
        
        final_capital = capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _backtest_macd(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest MACD strategy"""
        trades = []
        capital = initial_capital
        position = 0
        shares = 0
        
        for i in range(1, len(data)):
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            if pd.isna(data['MACD'].iloc[i]) or pd.isna(data['MACD_Signal'].iloc[i]):
                continue
            
            macd = data['MACD'].iloc[i]
            macd_signal = data['MACD_Signal'].iloc[i]
            prev_macd = data['MACD'].iloc[i-1]
            prev_signal = data['MACD_Signal'].iloc[i-1]
            
            # Buy signal: MACD crosses above signal line
            if macd > macd_signal and prev_macd <= prev_signal and position == 0:
                shares_to_buy = int((capital * 0.95) / current_price)
                if shares_to_buy * current_price >= self.min_trade_size:
                    cost = shares_to_buy * current_price * (1 + self.commission_rate + self.slippage)
                    if cost <= capital:
                        shares = shares_to_buy
                        capital -= cost
                        position = 1
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'value': shares * current_price,
                            'commission': shares * current_price * self.commission_rate,
                            'capital_remaining': capital
                        })
            
            # Sell signal: MACD crosses below signal line
            elif macd < macd_signal and prev_macd >= prev_signal and position == 1:
                proceeds = shares * current_price * (1 - self.commission_rate - self.slippage)
                capital += proceeds
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'value': shares * current_price,
                    'commission': shares * current_price * self.commission_rate,
                    'capital_remaining': capital
                })
                
                shares = 0
                position = 0
        
        # Close position at end if still holding
        if position == 1:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += proceeds
            
            trades.append({
                'date': data.index[-1].strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': final_price,
                'shares': shares,
                'value': shares * final_price,
                'commission': shares * final_price * self.commission_rate,
                'capital_remaining': capital
            })
        
        final_capital = capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _backtest_bollinger_bands(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest Bollinger Bands strategy"""
        trades = []
        capital = initial_capital
        position = 0
        shares = 0
        
        for i in range(len(data)):
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            if pd.isna(data['BB_Upper'].iloc[i]) or pd.isna(data['BB_Lower'].iloc[i]):
                continue
            
            bb_upper = data['BB_Upper'].iloc[i]
            bb_lower = data['BB_Lower'].iloc[i]
            
            # Buy signal: Price touches lower band
            if current_price <= bb_lower and position == 0:
                shares_to_buy = int((capital * 0.95) / current_price)
                if shares_to_buy * current_price >= self.min_trade_size:
                    cost = shares_to_buy * current_price * (1 + self.commission_rate + self.slippage)
                    if cost <= capital:
                        shares = shares_to_buy
                        capital -= cost
                        position = 1
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'value': shares * current_price,
                            'commission': shares * current_price * self.commission_rate,
                            'capital_remaining': capital
                        })
            
            # Sell signal: Price touches upper band
            elif current_price >= bb_upper and position == 1:
                proceeds = shares * current_price * (1 - self.commission_rate - self.slippage)
                capital += proceeds
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'value': shares * current_price,
                    'commission': shares * current_price * self.commission_rate,
                    'capital_remaining': capital
                })
                
                shares = 0
                position = 0
        
        # Close position at end if still holding
        if position == 1:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += proceeds
            
            trades.append({
                'date': data.index[-1].strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': final_price,
                'shares': shares,
                'value': shares * final_price,
                'commission': shares * final_price * self.commission_rate,
                'capital_remaining': capital
            })
        
        final_capital = capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _backtest_momentum(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest momentum strategy"""
        trades = []
        capital = initial_capital
        position = 0
        shares = 0
        
        for i in range(10, len(data)):  # Need at least 10 days for momentum calculation
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            # Calculate 5-day momentum
            momentum = (current_price / data['Close'].iloc[i-5] - 1) * 100
            
            # Buy signal: Strong positive momentum (>3%)
            if momentum > 3 and position == 0:
                shares_to_buy = int((capital * 0.95) / current_price)
                if shares_to_buy * current_price >= self.min_trade_size:
                    cost = shares_to_buy * current_price * (1 + self.commission_rate + self.slippage)
                    if cost <= capital:
                        shares = shares_to_buy
                        capital -= cost
                        position = 1
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'action': 'BUY',
                            'price': current_price,
                            'shares': shares,
                            'value': shares * current_price,
                            'commission': shares * current_price * self.commission_rate,
                            'capital_remaining': capital
                        })
            
            # Sell signal: Negative momentum (<-2%)
            elif momentum < -2 and position == 1:
                proceeds = shares * current_price * (1 - self.commission_rate - self.slippage)
                capital += proceeds
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'value': shares * current_price,
                    'commission': shares * current_price * self.commission_rate,
                    'capital_remaining': capital
                })
                
                shares = 0
                position = 0
        
        # Close position at end if still holding
        if position == 1:
            final_price = data['Close'].iloc[-1]
            proceeds = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += proceeds
            
            trades.append({
                'date': data.index[-1].strftime('%Y-%m-%d'),
                'action': 'SELL',
                'price': final_price,
                'shares': shares,
                'value': shares * final_price,
                'commission': shares * final_price * self.commission_rate,
                'capital_remaining': capital
            })
        
        final_capital = capital
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _backtest_buy_and_hold(self, data: pd.DataFrame, initial_capital: float) -> Dict:
        """Backtest buy and hold strategy"""
        if data.empty:
            return {
                'final_capital': initial_capital,
                'total_return': 0,
                'total_return_pct': 0,
                'trades': []
            }
        
        initial_price = data['Close'].iloc[0]
        final_price = data['Close'].iloc[-1]
        
        shares = int((initial_capital * 0.99) / initial_price)  # Use 99% to account for commission
        cost = shares * initial_price * (1 + self.commission_rate)
        
        # Buy trade
        trades = [{
            'date': data.index[0].strftime('%Y-%m-%d'),
            'action': 'BUY',
            'price': initial_price,
            'shares': shares,
            'value': shares * initial_price,
            'commission': shares * initial_price * self.commission_rate,
            'capital_remaining': initial_capital - cost
        }]
        
        # Sell trade at end
        proceeds = shares * final_price * (1 - self.commission_rate)
        final_capital = initial_capital - cost + proceeds
        
        trades.append({
            'date': data.index[-1].strftime('%Y-%m-%d'),
            'action': 'SELL',
            'price': final_price,
            'shares': shares,
            'value': shares * final_price,
            'commission': shares * final_price * self.commission_rate,
            'capital_remaining': final_capital
        })
        
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        return {
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'trades': trades
        }
    
    def _calculate_performance_metrics(self, trades: List[Dict], initial_capital: float) -> Dict:
        """Calculate performance metrics from trades"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0
                }
            
            # Group trades into buy/sell pairs
            trade_pairs = []
            buy_trade = None
            
            for trade in trades:
                if trade['action'] == 'BUY':
                    buy_trade = trade
                elif trade['action'] == 'SELL' and buy_trade:
                    # Calculate P&L for this trade pair
                    buy_value = buy_trade['shares'] * buy_trade['price']
                    sell_value = trade['shares'] * trade['price']
                    commission_cost = buy_value * self.commission_rate + sell_value * self.commission_rate
                    pnl = sell_value - buy_value - commission_cost
                    
                    trade_pairs.append({
                        'buy_date': buy_trade['date'],
                        'sell_date': trade['date'],
                        'buy_price': buy_trade['price'],
                        'sell_price': trade['price'],
                        'shares': trade['shares'],
                        'pnl': pnl,
                        'return_pct': (pnl / buy_value) * 100 if buy_value > 0 else 0
                    })
                    buy_trade = None
            
            if not trade_pairs:
                return {
                    'total_trades': len(trades),
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0
                }
            
            # Calculate metrics
            total_trades = len(trade_pairs)
            winning_trades = sum(1 for pair in trade_pairs if pair['pnl'] > 0)
            losing_trades = sum(1 for pair in trade_pairs if pair['pnl'] < 0)
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            wins = [pair['pnl'] for pair in trade_pairs if pair['pnl'] > 0]
            losses = [abs(pair['pnl']) for pair in trade_pairs if pair['pnl'] < 0]
            
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            
            total_wins = sum(wins)
            total_losses = sum(losses)
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Calculate maximum drawdown
            capital_history = [initial_capital]
            running_capital = initial_capital
            
            for i, trade in enumerate(trades):
                if trade['action'] == 'BUY':
                    running_capital -= trade['value'] + trade['commission']
                else:  # SELL
                    running_capital += trade['value'] - trade['commission']
                capital_history.append(running_capital)
            
            peak = initial_capital
            max_drawdown = 0
            
            for capital in capital_history:
                if capital > peak:
                    peak = capital
                drawdown = (peak - capital) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'Inf',
                'max_drawdown': round(max_drawdown, 2),
                'trade_details': trade_pairs
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0
            }
    
    def compare_strategies(self, symbol: str, strategies: List[str], 
                          initial_capital: float = 10000) -> Dict:
        """
        Compare multiple strategies for a symbol
        
        Args:
            symbol: Stock symbol
            strategies: List of strategy names to compare
            initial_capital: Initial capital for each backtest
            
        Returns:
            Dictionary with comparison results
        """
        try:
            comparison_results = {}
            
            for strategy in strategies:
                result = self.run_backtest(symbol, strategy, initial_capital=initial_capital)
                if 'error' not in result:
                    comparison_results[strategy] = {
                        'final_capital': result['final_capital'],
                        'total_return_pct': result['total_return_pct'],
                        'total_trades': result['performance_metrics']['total_trades'],
                        'win_rate': result['performance_metrics']['win_rate'],
                        'max_drawdown': result['performance_metrics']['max_drawdown']
                    }
            
            if not comparison_results:
                return {'error': 'No successful backtests to compare'}
            
            # Find best and worst performing strategies
            best_strategy = max(comparison_results.items(), key=lambda x: x[1]['total_return_pct'])
            worst_strategy = min(comparison_results.items(), key=lambda x: x[1]['total_return_pct'])
            
            return {
                'symbol': symbol,
                'strategies_compared': len(comparison_results),
                'results': comparison_results,
                'best_strategy': {
                    'name': best_strategy[0],
                    'return_pct': best_strategy[1]['total_return_pct']
                },
                'worst_strategy': {
                    'name': worst_strategy[0],
                    'return_pct': worst_strategy[1]['total_return_pct']
                },
                'comparison_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {str(e)}")
            return {'error': str(e)}
