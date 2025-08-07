import json
import os
import logging
from datetime import datetime

class UserProfileManager:
    """User Preference Management System"""
    
    def __init__(self):
        self.profile_file = 'data/user_profiles.json'
        self.default_profile = {
            'risk_tolerance': 'moderate',
            'investment_style': 'balanced',
            'preferred_assets': ['stocks'],
            'notification_preferences': {
                'price_alerts': True,
                'portfolio_updates': True,
                'market_news': False,
                'oracle_insights': True
            },
            'ui_preferences': {
                'theme': 'dark',
                'chart_type': 'candlestick',
                'default_timeframe': '1d',
                'show_advanced_metrics': False
            },
            'trading_preferences': {
                'position_sizing': 'conservative',
                'stop_loss_percentage': 5.0,
                'take_profit_percentage': 10.0,
                'max_portfolio_allocation': 20.0
            },
            'oracle_settings': {
                'emotional_sensitivity': 'medium',
                'archetype_preference': 'balanced',
                'mystical_level': 'moderate'
            },
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Initialize profile file if it doesn't exist
        if not os.path.exists(self.profile_file):
            self._save_profile(self.default_profile)
    
    def get_profile(self, user_id='default'):
        """Get user profile"""
        try:
            if not os.path.exists(self.profile_file):
                return self.default_profile
            
            with open(self.profile_file, 'r') as f:
                profiles = json.load(f)
            
            profile = profiles.get(user_id, self.default_profile.copy())
            
            # Ensure all required fields exist
            for key, value in self.default_profile.items():
                if key not in profile:
                    profile[key] = value
            
            return profile
            
        except Exception as e:
            logging.error(f"Error loading user profile: {str(e)}")
            return self.default_profile
    
    def update_profile(self, profile_data, user_id='default'):
        """Update user profile"""
        try:
            # Load existing profiles
            profiles = {}
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r') as f:
                    profiles = json.load(f)
            
            # Get current profile or default
            current_profile = profiles.get(user_id, self.default_profile.copy())
            
            # Update with new data
            current_profile.update(profile_data)
            current_profile['last_updated'] = datetime.now().isoformat()
            
            # Validate profile data
            validated_profile = self._validate_profile(current_profile)
            
            # Save updated profile
            profiles[user_id] = validated_profile
            
            with open(self.profile_file, 'w') as f:
                json.dump(profiles, f, indent=2)
            
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'profile': validated_profile
            }
            
        except Exception as e:
            logging.error(f"Error updating user profile: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'profile': self.get_profile(user_id)
            }
    
    def _validate_profile(self, profile):
        """Validate and sanitize profile data"""
        try:
            # Risk tolerance validation
            valid_risk_levels = ['conservative', 'moderate', 'aggressive']
            if profile.get('risk_tolerance') not in valid_risk_levels:
                profile['risk_tolerance'] = 'moderate'
            
            # Investment style validation
            valid_styles = ['conservative', 'balanced', 'growth', 'aggressive']
            if profile.get('investment_style') not in valid_styles:
                profile['investment_style'] = 'balanced'
            
            # Preferred assets validation
            valid_assets = ['stocks', 'crypto', 'options', 'futures']
            preferred_assets = profile.get('preferred_assets', [])
            profile['preferred_assets'] = [asset for asset in preferred_assets if asset in valid_assets]
            if not profile['preferred_assets']:
                profile['preferred_assets'] = ['stocks']
            
            # Notification preferences validation
            notif_prefs = profile.get('notification_preferences', {})
            for key in ['price_alerts', 'portfolio_updates', 'market_news', 'oracle_insights']:
                if key not in notif_prefs:
                    notif_prefs[key] = True
                elif not isinstance(notif_prefs[key], bool):
                    notif_prefs[key] = True
            profile['notification_preferences'] = notif_prefs
            
            # UI preferences validation
            ui_prefs = profile.get('ui_preferences', {})
            if ui_prefs.get('theme') not in ['light', 'dark']:
                ui_prefs['theme'] = 'dark'
            if ui_prefs.get('chart_type') not in ['line', 'candlestick', 'area']:
                ui_prefs['chart_type'] = 'candlestick'
            if ui_prefs.get('default_timeframe') not in ['1m', '5m', '15m', '1h', '1d', '1w']:
                ui_prefs['default_timeframe'] = '1d'
            profile['ui_preferences'] = ui_prefs
            
            # Trading preferences validation
            trading_prefs = profile.get('trading_preferences', {})
            
            # Ensure numeric values are within reasonable ranges
            stop_loss = trading_prefs.get('stop_loss_percentage', 5.0)
            trading_prefs['stop_loss_percentage'] = max(1.0, min(50.0, float(stop_loss)))
            
            take_profit = trading_prefs.get('take_profit_percentage', 10.0)
            trading_prefs['take_profit_percentage'] = max(2.0, min(100.0, float(take_profit)))
            
            max_allocation = trading_prefs.get('max_portfolio_allocation', 20.0)
            trading_prefs['max_portfolio_allocation'] = max(5.0, min(100.0, float(max_allocation)))
            
            profile['trading_preferences'] = trading_prefs
            
            # Oracle settings validation
            oracle_settings = profile.get('oracle_settings', {})
            if oracle_settings.get('emotional_sensitivity') not in ['low', 'medium', 'high']:
                oracle_settings['emotional_sensitivity'] = 'medium'
            if oracle_settings.get('archetype_preference') not in ['phoenix', 'titan', 'serpent', 'oracle', 'storm', 'mountain', 'balanced']:
                oracle_settings['archetype_preference'] = 'balanced'
            if oracle_settings.get('mystical_level') not in ['minimal', 'moderate', 'high']:
                oracle_settings['mystical_level'] = 'moderate'
            profile['oracle_settings'] = oracle_settings
            
            return profile
            
        except Exception as e:
            logging.error(f"Profile validation error: {str(e)}")
            return self.default_profile
    
    def _save_profile(self, profile, user_id='default'):
        """Save profile to file"""
        try:
            profiles = {}
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r') as f:
                    profiles = json.load(f)
            
            profiles[user_id] = profile
            
            with open(self.profile_file, 'w') as f:
                json.dump(profiles, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving profile: {str(e)}")
    
    def get_personalized_recommendations(self, user_id='default'):
        """Get personalized recommendations based on user profile"""
        try:
            profile = self.get_profile(user_id)
            recommendations = {
                'asset_suggestions': [],
                'strategy_recommendations': [],
                'ui_optimizations': {},
                'oracle_customizations': {}
            }
            
            risk_tolerance = profile.get('risk_tolerance', 'moderate')
            investment_style = profile.get('investment_style', 'balanced')
            preferred_assets = profile.get('preferred_assets', ['stocks'])
            
            # Asset suggestions based on profile
            if risk_tolerance == 'conservative':
                if 'stocks' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['SPY', 'VTI', 'MSFT', 'AAPL'])
                if 'crypto' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['BTC-USD', 'ETH-USD'])
            elif risk_tolerance == 'aggressive':
                if 'stocks' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['TSLA', 'NVDA', 'AMZN', 'GOOGL'])
                if 'crypto' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD'])
            else:  # moderate
                if 'stocks' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['SPY', 'MSFT', 'AAPL', 'TSLA'])
                if 'crypto' in preferred_assets:
                    recommendations['asset_suggestions'].extend(['BTC-USD', 'ETH-USD', 'ADA-USD'])
            
            # Strategy recommendations
            if risk_tolerance == 'conservative':
                recommendations['strategy_recommendations'].extend([
                    'Dollar Cost Averaging',
                    'Buy and Hold',
                    'Dividend Growth Strategy'
                ])
            elif risk_tolerance == 'aggressive':
                recommendations['strategy_recommendations'].extend([
                    'Momentum Trading',
                    'Growth Stock Strategy',
                    'Swing Trading'
                ])
            else:
                recommendations['strategy_recommendations'].extend([
                    'Balanced Portfolio',
                    'Index Fund Strategy',
                    'Value Investing'
                ])
            
            # UI optimizations
            ui_prefs = profile.get('ui_preferences', {})
            recommendations['ui_optimizations'] = {
                'recommended_theme': ui_prefs.get('theme', 'dark'),
                'chart_suggestions': [ui_prefs.get('chart_type', 'candlestick')],
                'dashboard_layout': 'compact' if risk_tolerance == 'conservative' else 'detailed'
            }
            
            # Oracle customizations
            oracle_settings = profile.get('oracle_settings', {})
            recommendations['oracle_customizations'] = {
                'emotional_tone': oracle_settings.get('emotional_sensitivity', 'medium'),
                'recommended_archetypes': self._get_archetype_recommendations(risk_tolerance),
                'insight_frequency': 'high' if oracle_settings.get('mystical_level') == 'high' else 'moderate'
            }
            
            return recommendations
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            return {}
    
    def _get_archetype_recommendations(self, risk_tolerance):
        """Get archetype recommendations based on risk tolerance"""
        archetype_map = {
            'conservative': ['Mountain', 'Oracle'],
            'moderate': ['Titan', 'Serpent', 'Oracle'],
            'aggressive': ['Phoenix', 'Storm', 'Titan']
        }
        
        return archetype_map.get(risk_tolerance, ['Oracle'])
    
    def export_profile(self, user_id='default'):
        """Export user profile for backup"""
        try:
            profile = self.get_profile(user_id)
            
            return {
                'export_timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'profile_data': profile,
                'version': '1.0'
            }
            
        except Exception as e:
            logging.error(f"Profile export error: {str(e)}")
            return {'error': str(e)}
    
    def import_profile(self, profile_export, user_id='default'):
        """Import user profile from backup"""
        try:
            if 'profile_data' not in profile_export:
                return {'success': False, 'error': 'Invalid profile export format'}
            
            profile_data = profile_export['profile_data']
            result = self.update_profile(profile_data, user_id)
            
            if result['success']:
                result['message'] = 'Profile imported successfully'
            
            return result
            
        except Exception as e:
            logging.error(f"Profile import error: {str(e)}")
            return {'success': False, 'error': str(e)}
