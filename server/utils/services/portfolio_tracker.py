import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from app import db
from models import Portfolio, User
from server.utils.services.data_fetcher import DataFetcher
from server.utils.services.crypto_predictor import CryptoPredictor
import json

class PortfolioTracker:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.crypto_predictor = CryptoPredictor()
    
    def get_performance(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio performance for a user"""
        try:
            # Get user's portfolio positions
            positions = Portfolio.query.filter_by(user_id=user_id).all()
            
            if not positions:
                return {
                    'total_value': 0,
                    'total_cost': 0,
                    'total_pnl': 0,
                    'total_pnl_percent': 0,
                    'positions': [],
                    'daily_change': 0,
                    'daily_change_percent': 0
                }
            
            portfolio_data = []
            total_value = 0
            total_cost = 0
            daily_change = 0
            
            for position in positions:
                try:
                    # Get current price
                    if position.asset_type == 'crypto':
                        current_price = self._get_crypto_price(position.ticker)
                    else:
                        current_price = self.data_fetcher.get_current_price(position.ticker)
                    
                    if current_price == 0:
                        continue
                    
                    # Calculate position metrics
                    current_value = position.quantity * current_price
                    cost_basis = position.quantity * position.purchase_price
                    pnl = current_value - cost_basis
                    pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    # Get daily change
                    prev_price = self._get_previous_price(position.ticker, position.asset_type)
                    daily_pos_change = position.quantity * (current_price - prev_price) if prev_price > 0 else 0
                    
                    portfolio_data.append({
                        'ticker': position.ticker,
                        'asset_type': position.asset_type,
                        'quantity': position.quantity,
                        'purchase_price': position.purchase_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'cost_basis': cost_basis,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'daily_change': daily_pos_change,
                        'purchase_date': position.purchase_date.isoformat() if position.purchase_date else None,
                        'weight': 0  # Will calculate after totals
                    })
                    
                    total_value += current_value
                    total_cost += cost_basis
                    daily_change += daily_pos_change
                    
                except Exception as e:
                    logging.error(f"Error processing position {position.ticker}: {str(e)}")
                    continue
            
            # Calculate weights and additional metrics
            for position in portfolio_data:
                position['weight'] = (position['current_value'] / total_value * 100) if total_value > 0 else 0
            
            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            daily_change_percent = (daily_change / (total_value - daily_change) * 100) if (total_value - daily_change) > 0 else 0
            
            # Get additional analytics
            analytics = self._calculate_portfolio_analytics(portfolio_data)
            
            return {
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percent': round(total_pnl_percent, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_percent': round(daily_change_percent, 2),
                'positions': portfolio_data,
                'positions_count': len(portfolio_data),
                'analytics': analytics,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Portfolio performance error for user {user_id}: {str(e)}")
            return {'error': str(e)}
    
    def add_position(self, user_id: int, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new position to user's portfolio"""
        try:
            # Validate required fields
            required_fields = ['ticker', 'quantity', 'purchase_price']
            for field in required_fields:
                if field not in position_data:
                    return {'error': f'Missing required field: {field}'}
            
            ticker = position_data['ticker'].upper()
            quantity = float(position_data['quantity'])
            purchase_price = float(position_data['purchase_price'])
            asset_type = position_data.get('asset_type', 'stock')
            
            # Validate ticker exists
            if asset_type == 'crypto':
                price_check = self._get_crypto_price(ticker)
            else:
                price_check = self.data_fetcher.get_current_price(ticker)
            
            if price_check == 0:
                return {'error': f'Invalid ticker: {ticker}'}
            
            # Check if position already exists
            existing_position = Portfolio.query.filter_by(
                user_id=user_id, 
                ticker=ticker,
                asset_type=asset_type
            ).first()
            
            if existing_position:
                # Update existing position (average cost)
                total_cost = (existing_position.quantity * existing_position.purchase_price) + (quantity * purchase_price)
                total_quantity = existing_position.quantity + quantity
                existing_position.purchase_price = total_cost / total_quantity
                existing_position.quantity = total_quantity
                existing_position.purchase_date = datetime.now(timezone.utc)
            else:
                # Create new position
                new_position = Portfolio(
                    user_id=user_id,
                    ticker=ticker,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    asset_type=asset_type,
                    purchase_date=datetime.now(timezone.utc)
                )
                db.session.add(new_position)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Added {quantity} shares of {ticker} at ${purchase_price}',
                'ticker': ticker,
                'quantity': quantity,
                'purchase_price': purchase_price,
                'asset_type': asset_type
            }
            
        except Exception as e:
            logging.error(f"Add position error: {str(e)}")
            db.session.rollback()
            return {'error': str(e)}
    
    def remove_position(self, user_id: int, ticker: str, asset_type: str = 'stock') -> Dict[str, Any]:
        """Remove a position from user's portfolio"""
        try:
            position = Portfolio.query.filter_by(
                user_id=user_id,
                ticker=ticker.upper(),
                asset_type=asset_type
            ).first()
            
            if not position:
                return {'error': f'Position {ticker} not found'}
            
            db.session.delete(position)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Removed position {ticker}',
                'ticker': ticker
            }
            
        except Exception as e:
            logging.error(f"Remove position error: {str(e)}")
            db.session.rollback()
            return {'error': str(e)}
    
    def get_portfolio_predictions(self, user_id: int) -> Dict[str, Any]:
        """Get predictions for all positions in user's portfolio"""
        try:
            positions = Portfolio.query.filter_by(user_id=user_id).all()
            
            if not positions:
                return {'error': 'No positions in portfolio'}
            
            predictions = {}
            total_predicted_change = 0
            total_value = 0
            
            for position in positions:
                try:
                    if position.asset_type == 'crypto':
                        pred = self.crypto_predictor.predict(position.ticker)
                    else:
                        # Use regular stock prediction (would need to import from ml_models)
                        pred = {'error': 'Stock predictions not implemented in this method'}
                    
                    if 'error' not in pred:
                        # Calculate position impact
                        position_value = position.quantity * pred['current_price']
                        predicted_value_change = position.quantity * pred['price_change']
                        
                        predictions[position.ticker] = {
                            **pred,
                            'position_value': position_value,
                            'predicted_value_change': predicted_value_change,
                            'quantity_held': position.quantity
                        }
                        
                        total_predicted_change += predicted_value_change
                        total_value += position_value
                        
                except Exception as e:
                    logging.error(f"Error predicting {position.ticker}: {str(e)}")
                    continue
            
            if not predictions:
                return {'error': 'No predictions available'}
            
            portfolio_predicted_change_percent = (total_predicted_change / total_value * 100) if total_value > 0 else 0
            
            return {
                'predictions': predictions,
                'portfolio_summary': {
                    'total_current_value': round(total_value, 2),
                    'total_predicted_change': round(total_predicted_change, 2),
                    'portfolio_predicted_change_percent': round(portfolio_predicted_change_percent, 2),
                    'positions_analyzed': len(predictions)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Portfolio predictions error: {str(e)}")
            return {'error': str(e)}
    
    def _get_crypto_price(self, ticker: str) -> float:
        """Get current crypto price"""
        try:
            crypto_ticker = f"{ticker}-USD" if not ticker.endswith('-USD') else ticker
            data = self.crypto_predictor._get_crypto_data(crypto_ticker, period='1d')
            if data is not None and not data.empty:
                return float(data['Close'].iloc[-1])
            return 0.0
        except:
            return 0.0
    
    def _get_previous_price(self, ticker: str, asset_type: str) -> float:
        """Get previous day's closing price"""
        try:
            if asset_type == 'crypto':
                crypto_ticker = f"{ticker}-USD" if not ticker.endswith('-USD') else ticker
                data = self.crypto_predictor._get_crypto_data(crypto_ticker, period='2d')
                if data is not None and len(data) >= 2:
                    return float(data['Close'].iloc[-2])
            else:
                data = self.data_fetcher.get_stock_data(ticker, period='2d')
                if data is not None and len(data) >= 2:
                    return float(data['Close'].iloc[-2])
            return 0.0
        except:
            return 0.0
    
    def _calculate_portfolio_analytics(self, portfolio_data: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced portfolio analytics"""
        try:
            if not portfolio_data:
                return {}
            
            # Asset allocation
            stock_value = sum(pos['current_value'] for pos in portfolio_data if pos['asset_type'] == 'stock')
            crypto_value = sum(pos['current_value'] for pos in portfolio_data if pos['asset_type'] == 'crypto')
            total_value = stock_value + crypto_value
            
            # Performance metrics
            winners = [pos for pos in portfolio_data if pos['pnl'] > 0]
            losers = [pos for pos in portfolio_data if pos['pnl'] < 0]
            
            # Risk metrics (simplified)
            position_weights = [pos['weight'] for pos in portfolio_data]
            concentration_risk = max(position_weights) if position_weights else 0
            
            return {
                'asset_allocation': {
                    'stocks_percent': round((stock_value / total_value * 100) if total_value > 0 else 0, 1),
                    'crypto_percent': round((crypto_value / total_value * 100) if total_value > 0 else 0, 1)
                },
                'performance_metrics': {
                    'winning_positions': len(winners),
                    'losing_positions': len(losers),
                    'win_rate': round((len(winners) / len(portfolio_data) * 100) if portfolio_data else 0, 1),
                    'best_performer': max(portfolio_data, key=lambda x: x['pnl_percent'])['ticker'] if portfolio_data else None,
                    'worst_performer': min(portfolio_data, key=lambda x: x['pnl_percent'])['ticker'] if portfolio_data else None
                },
                'risk_metrics': {
                    'concentration_risk': round(concentration_risk, 1),
                    'diversification_score': round((100 - concentration_risk), 1),
                    'total_positions': len(portfolio_data)
                }
            }
            
        except Exception as e:
            logging.error(f"Portfolio analytics error: {str(e)}")
            return {}
    
    def get_portfolio_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get historical portfolio performance (placeholder for future implementation)"""
        try:
            # This would require storing daily portfolio snapshots
            # For now, return current data
            current_performance = self.get_performance(user_id)
            
            return {
                'current_performance': current_performance,
                'historical_data': [],
                'message': 'Historical tracking not yet implemented'
            }
            
        except Exception as e:
            logging.error(f"Portfolio history error: {str(e)}")
            return {'error': str(e)}
