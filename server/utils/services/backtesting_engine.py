import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from server.utils.services.data_fetcher import DataFetcher
import logging

class BacktestingEngine:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        
    def run_backtest(self, strategy, ticker, start_date, end_date, initial_capital=10000):
        """Run backtest for a given strategy"""
        try:
            # Convert string dates to datetime objects
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get historical data
            data = self.get_backtest_data(ticker, start_date, end_date)
            
            if data.empty:
                raise ValueError(f"No data available for {ticker} in the specified period")
            
            # Apply strategy
            if strategy == 'buy_and_hold':
                results = self.buy_and_hold_strategy(data, initial_capital)
            elif strategy == 'moving_average_crossover':
                results = self.moving_average_crossover_strategy(data, initial_capital)
            elif strategy == 'rsi_mean_reversion':
                results = self.rsi_mean_reversion_strategy(data, initial_capital)
            elif strategy == 'bollinger_bands':
                results = self.bollinger_bands_strategy(data, initial_capital)
            elif strategy == 'momentum':
                results = self.momentum_strategy(data, initial_capital)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            # Calculate performance metrics
            metrics = self.calculate_performance_metrics(results, initial_capital)
            
            return {
                'strategy': strategy,
                'ticker': ticker,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'initial_capital': initial_capital,
                'final_value': metrics['final_value'],
                'total_return': metrics['total_return'],
                'annual_return': metrics['annual_return'],
                'volatility': metrics['volatility'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'max_drawdown': metrics['max_drawdown'],
                'win_rate': metrics['win_rate'],
                'total_trades': metrics['total_trades'],
                'profit_factor': metrics['profit_factor'],
                'calmar_ratio': metrics['calmar_ratio'],
                'equity_curve': results['portfolio_value'].tolist(),
                'trade_log': results[results['position'].diff() != 0][['Date', 'Close', 'position', 'portfolio_value']].to_dict('records')
            }
            
        except Exception as e:
            logging.error(f"Backtesting error: {str(e)}")
            raise

    def get_backtest_data(self, ticker, start_date, end_date):
        """Get historical data for backtesting"""
        try:
            # Calculate period for yfinance
            days_diff = (end_date - start_date).days
            
            if days_diff <= 30:
                period = '1mo'
            elif days_diff <= 90:
                period = '3mo'
            elif days_diff <= 180:
                period = '6mo'
            elif days_diff <= 365:
                period = '1y'
            elif days_diff <= 730:
                period = '2y'
            else:
                period = '5y'
            
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, start=start_date, end=end_date)
            
            if data.empty:
                raise ValueError(f"No data found for {ticker}")
            
            # Reset index to make Date a column
            data.reset_index(inplace=True)
            return data
            
        except Exception as e:
            logging.error(f"Error fetching backtest data: {str(e)}")
            raise

    def buy_and_hold_strategy(self, data, initial_capital):
        """Simple buy and hold strategy"""
        data = data.copy()
        
        # Buy on first day, hold until end
        data['position'] = 1.0  # Always long
        data['shares'] = initial_capital / data['Close'].iloc[0]
        data['portfolio_value'] = data['shares'] * data['Close']
        
        return data

    def moving_average_crossover_strategy(self, data, initial_capital, short_window=20, long_window=50):
        """Moving average crossover strategy"""
        data = data.copy()
        
        # Calculate moving averages
        data['SMA_short'] = data['Close'].rolling(window=short_window).mean()
        data['SMA_long'] = data['Close'].rolling(window=long_window).mean()
        
        # Generate signals
        data['signal'] = 0
        data['signal'][short_window:] = np.where(
            data['SMA_short'][short_window:] > data['SMA_long'][short_window:], 1, 0
        )
        data['position'] = data['signal'].diff()
        
        # Calculate portfolio value
        data['portfolio_value'] = initial_capital
        cash = initial_capital
        shares = 0
        
        for i in range(len(data)):
            if data['position'].iloc[i] == 1:  # Buy signal
                shares = cash / data['Close'].iloc[i]
                cash = 0
            elif data['position'].iloc[i] == -1:  # Sell signal
                cash = shares * data['Close'].iloc[i]
                shares = 0
            
            data.loc[data.index[i], 'portfolio_value'] = cash + shares * data['Close'].iloc[i]
        
        return data

    def rsi_mean_reversion_strategy(self, data, initial_capital, rsi_period=14, oversold=30, overbought=70):
        """RSI mean reversion strategy"""
        data = data.copy()
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        data['signal'] = 0
        data['signal'] = np.where(data['RSI'] < oversold, 1, 0)  # Buy when oversold
        data['signal'] = np.where(data['RSI'] > overbought, -1, data['signal'])  # Sell when overbought
        data['position'] = data['signal']
        
        # Calculate portfolio value
        data['portfolio_value'] = initial_capital
        cash = initial_capital
        shares = 0
        
        for i in range(len(data)):
            if data['signal'].iloc[i] == 1 and shares == 0:  # Buy
                shares = cash / data['Close'].iloc[i]
                cash = 0
            elif data['signal'].iloc[i] == -1 and shares > 0:  # Sell
                cash = shares * data['Close'].iloc[i]
                shares = 0
            
            data.loc[data.index[i], 'portfolio_value'] = cash + shares * data['Close'].iloc[i]
        
        return data

    def bollinger_bands_strategy(self, data, initial_capital, window=20, num_std=2):
        """Bollinger Bands strategy"""
        data = data.copy()
        
        # Calculate Bollinger Bands
        data['SMA'] = data['Close'].rolling(window=window).mean()
        data['std'] = data['Close'].rolling(window=window).std()
        data['upper_band'] = data['SMA'] + (data['std'] * num_std)
        data['lower_band'] = data['SMA'] - (data['std'] * num_std)
        
        # Generate signals
        data['signal'] = 0
        data['signal'] = np.where(data['Close'] < data['lower_band'], 1, 0)  # Buy at lower band
        data['signal'] = np.where(data['Close'] > data['upper_band'], -1, data['signal'])  # Sell at upper band
        data['position'] = data['signal']
        
        # Calculate portfolio value
        data['portfolio_value'] = initial_capital
        cash = initial_capital
        shares = 0
        
        for i in range(len(data)):
            if data['signal'].iloc[i] == 1 and shares == 0:  # Buy
                shares = cash / data['Close'].iloc[i]
                cash = 0
            elif data['signal'].iloc[i] == -1 and shares > 0:  # Sell
                cash = shares * data['Close'].iloc[i]
                shares = 0
            
            data.loc[data.index[i], 'portfolio_value'] = cash + shares * data['Close'].iloc[i]
        
        return data

    def momentum_strategy(self, data, initial_capital, lookback=10, holding_period=5):
        """Momentum strategy"""
        data = data.copy()
        
        # Calculate momentum
        data['momentum'] = data['Close'] / data['Close'].shift(lookback) - 1
        
        # Generate signals
        data['signal'] = 0
        data['signal'] = np.where(data['momentum'] > 0.05, 1, 0)  # Buy on strong momentum
        data['signal'] = np.where(data['momentum'] < -0.05, -1, data['signal'])  # Sell on negative momentum
        data['position'] = data['signal']
        
        # Calculate portfolio value with holding period
        data['portfolio_value'] = initial_capital
        cash = initial_capital
        shares = 0
        hold_until = 0
        
        for i in range(len(data)):
            current_date = i
            
            if current_date >= hold_until:
                if data['signal'].iloc[i] == 1 and shares == 0:  # Buy
                    shares = cash / data['Close'].iloc[i]
                    cash = 0
                    hold_until = current_date + holding_period
                elif data['signal'].iloc[i] == -1 and shares > 0:  # Sell
                    cash = shares * data['Close'].iloc[i]
                    shares = 0
                    hold_until = current_date + holding_period
            
            data.loc[data.index[i], 'portfolio_value'] = cash + shares * data['Close'].iloc[i]
        
        return data

    def calculate_performance_metrics(self, results, initial_capital):
        """Calculate comprehensive performance metrics"""
        try:
            portfolio_values = results['portfolio_value']
            final_value = portfolio_values.iloc[-1]
            
            # Basic returns
            total_return = (final_value - initial_capital) / initial_capital
            
            # Calculate daily returns
            daily_returns = portfolio_values.pct_change().dropna()
            
            # Annualized metrics
            trading_days = len(results)
            years = trading_days / 252  # Assuming 252 trading days per year
            annual_return = (final_value / initial_capital) ** (1 / years) - 1 if years > 0 else 0
            
            # Volatility (annualized)
            volatility = daily_returns.std() * np.sqrt(252)
            
            # Sharpe ratio (assuming 0% risk-free rate)
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            running_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Trade analysis
            if 'position' in results.columns:
                position_changes = results['position'].diff()
                trades = position_changes[position_changes != 0]
                total_trades = len(trades)
                
                # Calculate wins and losses
                trade_returns = []
                entry_price = None
                entry_position = 0
                
                for i, row in results.iterrows():
                    if row['position'] != entry_position:
                        if entry_price is not None and entry_position != 0:
                            # Calculate trade return
                            if entry_position > 0:  # Long position
                                trade_return = (row['Close'] - entry_price) / entry_price
                            else:  # Short position
                                trade_return = (entry_price - row['Close']) / entry_price
                            trade_returns.append(trade_return)
                        
                        entry_price = row['Close']
                        entry_position = row['position']
                
                winning_trades = [r for r in trade_returns if r > 0]
                losing_trades = [r for r in trade_returns if r < 0]
                
                win_rate = len(winning_trades) / len(trade_returns) if trade_returns else 0
                avg_win = np.mean(winning_trades) if winning_trades else 0
                avg_loss = np.mean(losing_trades) if losing_trades else 0
                profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if avg_loss != 0 and losing_trades else float('inf')
            else:
                total_trades = 1  # Buy and hold
                win_rate = 1 if total_return > 0 else 0
                profit_factor = float('inf') if total_return > 0 else 0
            
            # Calmar ratio
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
            
            return {
                'final_value': float(final_value),
                'total_return': float(total_return),
                'annual_return': float(annual_return),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate),
                'total_trades': int(total_trades),
                'profit_factor': float(profit_factor),
                'calmar_ratio': float(calmar_ratio)
            }
            
        except Exception as e:
            logging.error(f"Error calculating performance metrics: {str(e)}")
            raise

    def compare_strategies(self, ticker, start_date, end_date, strategies=None, initial_capital=10000):
        """Compare multiple strategies"""
        try:
            if strategies is None:
                strategies = ['buy_and_hold', 'moving_average_crossover', 'rsi_mean_reversion', 'bollinger_bands']
            
            comparison_results = []
            
            for strategy in strategies:
                try:
                    result = self.run_backtest(strategy, ticker, start_date, end_date, initial_capital)
                    comparison_results.append({
                        'strategy': strategy,
                        'total_return': result['total_return'],
                        'annual_return': result['annual_return'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'max_drawdown': result['max_drawdown'],
                        'win_rate': result['win_rate'],
                        'total_trades': result['total_trades']
                    })
                except Exception as e:
                    logging.warning(f"Failed to backtest strategy {strategy}: {str(e)}")
                    continue
            
            # Sort by Sharpe ratio
            comparison_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            
            return {
                'ticker': ticker,
                'period': f"{start_date} to {end_date}",
                'strategies_compared': len(comparison_results),
                'best_strategy': comparison_results[0]['strategy'] if comparison_results else None,
                'results': comparison_results
            }
            
        except Exception as e:
            logging.error(f"Error comparing strategies: {str(e)}")
            raise

    def optimize_strategy_parameters(self, strategy, ticker, start_date, end_date, param_ranges):
        """Optimize strategy parameters using grid search"""
        try:
            best_result = None
            best_sharpe = -float('inf')
            optimization_results = []
            
            # Generate parameter combinations
            param_combinations = self.generate_param_combinations(param_ranges)
            
            for params in param_combinations:
                try:
                    # Run backtest with current parameters
                    if strategy == 'moving_average_crossover':
                        result = self.moving_average_crossover_optimized(
                            ticker, start_date, end_date, params
                        )
                    elif strategy == 'rsi_mean_reversion':
                        result = self.rsi_mean_reversion_optimized(
                            ticker, start_date, end_date, params
                        )
                    else:
                        continue
                    
                    optimization_results.append({
                        'parameters': params,
                        'sharpe_ratio': result['sharpe_ratio'],
                        'total_return': result['total_return'],
                        'max_drawdown': result['max_drawdown']
                    })
                    
                    if result['sharpe_ratio'] > best_sharpe:
                        best_sharpe = result['sharpe_ratio']
                        best_result = {
                            'parameters': params,
                            'metrics': result
                        }
                        
                except Exception as e:
                    logging.warning(f"Parameter optimization failed for {params}: {str(e)}")
                    continue
            
            return {
                'strategy': strategy,
                'ticker': ticker,
                'best_parameters': best_result['parameters'] if best_result else None,
                'best_metrics': best_result['metrics'] if best_result else None,
                'total_combinations_tested': len(optimization_results),
                'all_results': sorted(optimization_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10]
            }
            
        except Exception as e:
            logging.error(f"Strategy optimization error: {str(e)}")
            raise

    def generate_param_combinations(self, param_ranges):
        """Generate all combinations of parameters for optimization"""
        import itertools
        
        keys = list(param_ranges.keys())
        values = list(param_ranges.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        return combinations

    def moving_average_crossover_optimized(self, ticker, start_date, end_date, params):
        """Run moving average crossover with specific parameters"""
        data = self.get_backtest_data(ticker, start_date, end_date)
        result = self.moving_average_crossover_strategy(
            data, 10000, 
            short_window=params['short_window'],
            long_window=params['long_window']
        )
        return self.calculate_performance_metrics(result, 10000)

    def rsi_mean_reversion_optimized(self, ticker, start_date, end_date, params):
        """Run RSI mean reversion with specific parameters"""
        data = self.get_backtest_data(ticker, start_date, end_date)
        result = self.rsi_mean_reversion_strategy(
            data, 10000,
            rsi_period=params['rsi_period'],
            oversold=params['oversold'],
            overbought=params['overbought']
        )
        return self.calculate_performance_metrics(result, 10000)
