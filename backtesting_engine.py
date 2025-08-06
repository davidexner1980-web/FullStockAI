import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from trading_strategies import TradingStrategies
import logging

class BacktestingEngine:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.trading_strategies = TradingStrategies()
        
    def run_backtest(self, strategy_name, ticker, start_date, end_date, initial_capital=10000):
        """Run a backtest for a specific strategy"""
        try:
            # Get historical data
            df = self.data_fetcher.get_stock_data(ticker, period='2y')  # Get more data for better backtest
            if df.empty:
                raise ValueError(f"No data available for {ticker}")
            
            # Filter data by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            
            if df.empty:
                raise ValueError(f"No data in specified date range for {ticker}")
            
            # Initialize backtest variables
            capital = initial_capital
            position = 0  # Number of shares
            trades = []
            portfolio_values = []
            
            # Run strategy on each day
            for i, (date, row) in enumerate(df.iterrows()):
                current_price = row['Close']
                
                # Get signal from strategy
                signal_data = self.get_strategy_signal(strategy_name, ticker, df.iloc[:i+1])
                signal = signal_data.get('signal', 'HOLD')
                confidence = signal_data.get('confidence', 50)
                
                # Execute trades based on signal
                if signal == 'BUY' and position == 0 and confidence > 60:
                    # Buy signal - enter long position
                    shares_to_buy = int(capital / current_price)
                    if shares_to_buy > 0:
                        position = shares_to_buy
                        cost = shares_to_buy * current_price
                        capital -= cost
                        
                        trades.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'type': 'BUY',
                            'price': current_price,
                            'shares': shares_to_buy,
                            'cost': cost,
                            'confidence': confidence
                        })
                
                elif signal == 'SELL' and position > 0:
                    # Sell signal - exit long position
                    proceeds = position * current_price
                    capital += proceeds
                    
                    trades.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'type': 'SELL',
                        'price': current_price,
                        'shares': position,
                        'proceeds': proceeds,
                        'confidence': confidence
                    })
                    
                    position = 0
                
                # Calculate current portfolio value
                portfolio_value = capital + (position * current_price)
                portfolio_values.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': portfolio_value,
                    'cash': capital,
                    'position_value': position * current_price,
                    'shares': position
                })
            
            # Final portfolio value
            final_value = capital + (position * df['Close'].iloc[-1])
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # Calculate performance metrics
            metrics = self.calculate_backtest_metrics(portfolio_values, trades, initial_capital, final_value)
            
            return {
                'strategy': strategy_name,
                'ticker': ticker,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_value': round(final_value, 2),
                'total_return': round(total_return, 2),
                'total_trades': len(trades),
                'portfolio_history': portfolio_values,
                'trades': trades,
                'metrics': metrics
            }
        except Exception as e:
            logging.error(f"Backtest error for {strategy_name} on {ticker}: {str(e)}")
            return {
                'error': str(e),
                'strategy': strategy_name,
                'ticker': ticker
            }

    def get_strategy_signal(self, strategy_name, ticker, historical_data):
        """Get signal from a specific strategy using historical data"""
        try:
            # Create a temporary data fetcher that uses historical data
            temp_df = historical_data.copy()
            
            if strategy_name.lower() == 'moving_average':
                return self.ma_strategy_signal(temp_df)
            elif strategy_name.lower() == 'rsi':
                return self.rsi_strategy_signal(temp_df)
            elif strategy_name.lower() == 'macd':
                return self.macd_strategy_signal(temp_df)
            elif strategy_name.lower() == 'bollinger_bands':
                return self.bb_strategy_signal(temp_df)
            elif strategy_name.lower() == 'mean_reversion':
                return self.mean_reversion_signal(temp_df)
            elif strategy_name.lower() == 'momentum':
                return self.momentum_strategy_signal(temp_df)
            elif strategy_name.lower() == 'buy_and_hold':
                return self.buy_hold_signal(temp_df)
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except Exception as e:
            logging.error(f"Strategy signal error: {str(e)}")
            return {'signal': 'HOLD', 'confidence': 50}

    def ma_strategy_signal(self, df):
        """Moving Average Crossover Strategy"""
        try:
            if len(df) < 50:
                return {'signal': 'HOLD', 'confidence': 50}
            
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            
            current_ma20 = df['MA_20'].iloc[-1]
            current_ma50 = df['MA_50'].iloc[-1]
            prev_ma20 = df['MA_20'].iloc[-2] if len(df) > 1 else current_ma20
            prev_ma50 = df['MA_50'].iloc[-2] if len(df) > 1 else current_ma50
            
            if current_ma20 > current_ma50 and prev_ma20 <= prev_ma50:
                return {'signal': 'BUY', 'confidence': 75}
            elif current_ma20 < current_ma50 and prev_ma20 >= prev_ma50:
                return {'signal': 'SELL', 'confidence': 75}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def rsi_strategy_signal(self, df):
        """RSI Strategy"""
        try:
            if len(df) < 20:
                return {'signal': 'HOLD', 'confidence': 50}
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            if current_rsi < 30:
                return {'signal': 'BUY', 'confidence': min(90, 30 + (30 - current_rsi) * 2)}
            elif current_rsi > 70:
                return {'signal': 'SELL', 'confidence': min(90, 30 + (current_rsi - 70) * 2)}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def macd_strategy_signal(self, df):
        """MACD Strategy"""
        try:
            if len(df) < 35:
                return {'signal': 'HOLD', 'confidence': 50}
            
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd.iloc[-2] if len(df) > 1 else current_macd
            prev_signal = signal_line.iloc[-2] if len(df) > 1 else current_signal
            
            if current_macd > current_signal and prev_macd <= prev_signal:
                return {'signal': 'BUY', 'confidence': 70}
            elif current_macd < current_signal and prev_macd >= prev_signal:
                return {'signal': 'SELL', 'confidence': 70}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def bb_strategy_signal(self, df):
        """Bollinger Bands Strategy"""
        try:
            if len(df) < 25:
                return {'signal': 'HOLD', 'confidence': 50}
            
            bb_period = 20
            bb_std = 2
            df['BB_middle'] = df['Close'].rolling(window=bb_period).mean()
            bb_std_dev = df['Close'].rolling(window=bb_period).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std_dev * bb_std)
            df['BB_lower'] = df['BB_middle'] - (bb_std_dev * bb_std)
            
            current_price = df['Close'].iloc[-1]
            current_upper = df['BB_upper'].iloc[-1]
            current_lower = df['BB_lower'].iloc[-1]
            
            if current_price <= current_lower:
                return {'signal': 'BUY', 'confidence': 80}
            elif current_price >= current_upper:
                return {'signal': 'SELL', 'confidence': 80}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def mean_reversion_signal(self, df):
        """Mean Reversion Strategy"""
        try:
            if len(df) < 20:
                return {'signal': 'HOLD', 'confidence': 50}
            
            # Calculate deviation from moving average
            df['MA'] = df['Close'].rolling(window=20).mean()
            df['deviation'] = (df['Close'] - df['MA']) / df['MA']
            
            current_deviation = df['deviation'].iloc[-1]
            
            if current_deviation < -0.05:  # 5% below MA
                return {'signal': 'BUY', 'confidence': 70}
            elif current_deviation > 0.05:  # 5% above MA
                return {'signal': 'SELL', 'confidence': 70}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def momentum_strategy_signal(self, df):
        """Momentum Strategy"""
        try:
            if len(df) < 10:
                return {'signal': 'HOLD', 'confidence': 50}
            
            # Calculate momentum
            momentum = df['Close'].pct_change(periods=5).iloc[-1]
            
            if momentum > 0.05:  # 5% gain in 5 days
                return {'signal': 'BUY', 'confidence': 75}
            elif momentum < -0.05:  # 5% loss in 5 days
                return {'signal': 'SELL', 'confidence': 75}
            else:
                return {'signal': 'HOLD', 'confidence': 50}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def buy_hold_signal(self, df):
        """Buy and Hold Strategy"""
        try:
            # Always buy on first day, hold thereafter
            if len(df) <= 2:
                return {'signal': 'BUY', 'confidence': 100}
            else:
                return {'signal': 'HOLD', 'confidence': 100}
        except:
            return {'signal': 'HOLD', 'confidence': 50}

    def calculate_backtest_metrics(self, portfolio_values, trades, initial_capital, final_value):
        """Calculate comprehensive backtest metrics"""
        try:
            if not portfolio_values:
                return {}
            
            # Extract values for calculations
            values = [pv['value'] for pv in portfolio_values]
            dates = [pv['date'] for pv in portfolio_values]
            
            # Calculate returns
            returns = []
            for i in range(1, len(values)):
                daily_return = (values[i] - values[i-1]) / values[i-1] if values[i-1] > 0 else 0
                returns.append(daily_return)
            
            if not returns:
                returns = [0]
            
            # Total return
            total_return = ((final_value - initial_capital) / initial_capital) * 100
            
            # Annualized return (assuming 252 trading days per year)
            days = len(values)
            years = days / 252 if days > 0 else 1
            annualized_return = ((final_value / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
            
            # Volatility (annualized)
            volatility = np.std(returns) * np.sqrt(252) * 100 if returns else 0
            
            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            excess_return = (annualized_return / 100) - risk_free_rate
            sharpe_ratio = excess_return / (volatility / 100) if volatility > 0 else 0
            
            # Maximum drawdown
            peak = initial_capital
            max_drawdown = 0
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            max_drawdown *= 100
            
            # Win rate
            winning_trades = 0
            total_trades = 0
            
            for i in range(1, len(trades)):
                if trades[i]['type'] == 'SELL' and trades[i-1]['type'] == 'BUY':
                    total_trades += 1
                    if trades[i]['price'] > trades[i-1]['price']:
                        winning_trades += 1
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Best and worst trades
            trade_returns = []
            for i in range(1, len(trades)):
                if trades[i]['type'] == 'SELL' and trades[i-1]['type'] == 'BUY':
                    trade_return = ((trades[i]['price'] - trades[i-1]['price']) / trades[i-1]['price']) * 100
                    trade_returns.append(trade_return)
            
            best_trade = max(trade_returns) if trade_returns else 0
            worst_trade = min(trade_returns) if trade_returns else 0
            
            return {
                'total_return': round(total_return, 2),
                'annualized_return': round(annualized_return, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'best_trade': round(best_trade, 2),
                'worst_trade': round(worst_trade, 2),
                'avg_trade_return': round(np.mean(trade_returns), 2) if trade_returns else 0
            }
        except Exception as e:
            logging.error(f"Metrics calculation error: {str(e)}")
            return {}

    def compare_strategies(self, strategies, ticker, start_date, end_date, initial_capital=10000):
        """Compare multiple strategies on the same ticker"""
        try:
            results = []
            
            for strategy in strategies:
                backtest_result = self.run_backtest(strategy, ticker, start_date, end_date, initial_capital)
                if 'error' not in backtest_result:
                    results.append({
                        'strategy': strategy,
                        'total_return': backtest_result['total_return'],
                        'sharpe_ratio': backtest_result['metrics'].get('sharpe_ratio', 0),
                        'max_drawdown': backtest_result['metrics'].get('max_drawdown', 0),
                        'win_rate': backtest_result['metrics'].get('win_rate', 0),
                        'total_trades': backtest_result['total_trades']
                    })
            
            # Rank strategies by Sharpe ratio
            results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
            
            return {
                'comparison': results,
                'best_strategy': results[0] if results else None,
                'ticker': ticker,
                'period': f"{start_date} to {end_date}"
            }
        except Exception as e:
            logging.error(f"Strategy comparison error: {str(e)}")
            return {'error': str(e)}

    def get_available_strategies(self):
        """Get list of available backtesting strategies"""
        return [
            'moving_average',
            'rsi',
            'macd',
            'bollinger_bands',
            'mean_reversion',
            'momentum',
            'buy_and_hold'
        ]

