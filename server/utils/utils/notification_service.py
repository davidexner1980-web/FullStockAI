import smtplib
import json
import os
import logging
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from flask_mail import Mail, Message
from app import mail, app

class NotificationService:
    """Enhanced notification service for alerts and updates"""
    
    def __init__(self):
        self.notification_log = 'logs/notifications.json'
        self.templates_dir = 'templates/notifications'
        
        # Ensure directories exist
        os.makedirs('logs', exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize notification history
        self.notification_history = self._load_notification_history()
        
        # Email templates
        self.email_templates = {
            'price_alert': {
                'subject': 'FullStock AI - Price Alert for {ticker}',
                'template': 'price_alert_template'
            },
            'portfolio_update': {
                'subject': 'FullStock AI - Portfolio Update',
                'template': 'portfolio_update_template'
            },
            'oracle_insight': {
                'subject': 'FullStock AI - Oracle Vision for {ticker}',
                'template': 'oracle_insight_template'
            },
            'market_summary': {
                'subject': 'FullStock AI - Daily Market Summary',
                'template': 'market_summary_template'
            },
            'system_alert': {
                'subject': 'FullStock AI - System Alert',
                'template': 'system_alert_template'
            }
        }
    
    def _load_notification_history(self):
        """Load notification history from file"""
        try:
            if os.path.exists(self.notification_log):
                with open(self.notification_log, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading notification history: {str(e)}")
        
        return []
    
    def _save_notification_history(self):
        """Save notification history to file"""
        try:
            # Keep only last 1000 notifications
            self.notification_history = self.notification_history[-1000:]
            
            with open(self.notification_log, 'w') as f:
                json.dump(self.notification_history, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving notification history: {str(e)}")
    
    def send_price_alert(self, user_email, ticker, current_price, target_price, alert_type='above'):
        """Send price alert notification"""
        try:
            # Prepare notification data
            notification_data = {
                'type': 'price_alert',
                'ticker': ticker,
                'current_price': current_price,
                'target_price': target_price,
                'alert_type': alert_type,
                'timestamp': datetime.now().isoformat(),
                'user_email': user_email
            }
            
            # Generate email content
            subject = self.email_templates['price_alert']['subject'].format(ticker=ticker)
            
            html_content = self._generate_price_alert_html(notification_data)
            text_content = self._generate_price_alert_text(notification_data)
            
            # Send email
            success = self._send_email(user_email, subject, text_content, html_content)
            
            # Log notification
            notification_data['success'] = success
            self._log_notification(notification_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending price alert: {str(e)}")
            return False
    
    def send_portfolio_update(self, user_email, portfolio_data):
        """Send portfolio update notification"""
        try:
            notification_data = {
                'type': 'portfolio_update',
                'portfolio_data': portfolio_data,
                'timestamp': datetime.now().isoformat(),
                'user_email': user_email
            }
            
            subject = self.email_templates['portfolio_update']['subject']
            
            html_content = self._generate_portfolio_update_html(notification_data)
            text_content = self._generate_portfolio_update_text(notification_data)
            
            success = self._send_email(user_email, subject, text_content, html_content)
            
            notification_data['success'] = success
            self._log_notification(notification_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending portfolio update: {str(e)}")
            return False
    
    def send_oracle_insight(self, user_email, ticker, oracle_vision):
        """Send Oracle insight notification"""
        try:
            notification_data = {
                'type': 'oracle_insight',
                'ticker': ticker,
                'oracle_vision': oracle_vision,
                'timestamp': datetime.now().isoformat(),
                'user_email': user_email
            }
            
            subject = self.email_templates['oracle_insight']['subject'].format(ticker=ticker)
            
            html_content = self._generate_oracle_insight_html(notification_data)
            text_content = self._generate_oracle_insight_text(notification_data)
            
            success = self._send_email(user_email, subject, text_content, html_content)
            
            notification_data['success'] = success
            self._log_notification(notification_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending Oracle insight: {str(e)}")
            return False
    
    def send_market_summary(self, user_email, market_data):
        """Send daily market summary"""
        try:
            notification_data = {
                'type': 'market_summary',
                'market_data': market_data,
                'timestamp': datetime.now().isoformat(),
                'user_email': user_email
            }
            
            subject = self.email_templates['market_summary']['subject']
            
            html_content = self._generate_market_summary_html(notification_data)
            text_content = self._generate_market_summary_text(notification_data)
            
            success = self._send_email(user_email, subject, text_content, html_content)
            
            notification_data['success'] = success
            self._log_notification(notification_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending market summary: {str(e)}")
            return False
    
    def send_system_alert(self, admin_email, alert_type, alert_message, severity='medium'):
        """Send system alert to administrators"""
        try:
            notification_data = {
                'type': 'system_alert',
                'alert_type': alert_type,
                'alert_message': alert_message,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'admin_email': admin_email
            }
            
            subject = f"[{severity.upper()}] " + self.email_templates['system_alert']['subject']
            
            html_content = self._generate_system_alert_html(notification_data)
            text_content = self._generate_system_alert_text(notification_data)
            
            success = self._send_email(admin_email, subject, text_content, html_content)
            
            notification_data['success'] = success
            self._log_notification(notification_data)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending system alert: {str(e)}")
            return False
    
    def _send_email(self, recipient, subject, text_content, html_content=None):
        """Send email using Flask-Mail"""
        try:
            with app.app_context():
                msg = Message(
                    subject=subject,
                    recipients=[recipient],
                    body=text_content,
                    html=html_content,
                    sender=app.config.get('MAIL_USERNAME', 'noreply@fullstockai.com')
                )
                
                mail.send(msg)
                logging.info(f"Email sent successfully to {recipient}")
                return True
                
        except Exception as e:
            logging.error(f"Error sending email to {recipient}: {str(e)}")
            return False
    
    def _generate_price_alert_html(self, data):
        """Generate HTML content for price alert"""
        ticker = data['ticker']
        current_price = data['current_price']
        target_price = data['target_price']
        alert_type = data['alert_type']
        
        direction = "above" if alert_type == "above" else "below"
        color = "#28a745" if alert_type == "above" else "#dc3545"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .alert-box {{ background-color: {color}; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
                .price {{ font-size: 28px; font-weight: bold; }}
                .ticker {{ font-size: 20px; font-weight: bold; color: #333; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FullStock AI</div>
                    <h2>Price Alert Triggered</h2>
                </div>
                
                <div class="ticker">{ticker}</div>
                
                <div class="alert-box">
                    <div>Current Price: <span class="price">${current_price:.2f}</span></div>
                    <div style="margin-top: 10px;">
                        Price moved {direction} your target of ${target_price:.2f}
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p>Your FullStock AI price alert has been triggered. Consider reviewing your position and market conditions.</p>
                    <a href="https://fullstockai.com" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Dashboard</a>
                </div>
                
                <div class="footer">
                    <p>This alert was generated by FullStock AI on {data['timestamp']}</p>
                    <p>© 2025 FullStock AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_price_alert_text(self, data):
        """Generate text content for price alert"""
        ticker = data['ticker']
        current_price = data['current_price']
        target_price = data['target_price']
        alert_type = data['alert_type']
        
        direction = "above" if alert_type == "above" else "below"
        
        text = f"""
FullStock AI - Price Alert

{ticker} Price Alert Triggered!

Current Price: ${current_price:.2f}
Target Price: ${target_price:.2f}

Your price alert has been triggered as {ticker} moved {direction} your target price of ${target_price:.2f}.

Current market conditions suggest reviewing your position and considering your next steps.

Visit your FullStock AI dashboard to view detailed analysis and recommendations.

Alert generated on: {data['timestamp']}

Best regards,
FullStock AI Team
        """
        
        return text.strip()
    
    def _generate_portfolio_update_html(self, data):
        """Generate HTML for portfolio update"""
        portfolio_data = data.get('portfolio_data', {})
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .metric {{ display: flex; justify-content: space-between; padding: 15px; border-bottom: 1px solid #eee; }}
                .metric-label {{ font-weight: bold; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FullStock AI</div>
                    <h2>Portfolio Update</h2>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Portfolio Performance Summary</h3>
                    <div class="metric">
                        <span class="metric-label">Total Value:</span>
                        <span>${portfolio_data.get('total_value', 0):,.2f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Daily Change:</span>
                        <span class="{'positive' if portfolio_data.get('daily_change', 0) >= 0 else 'negative'}">
                            ${portfolio_data.get('daily_change', 0):,.2f} ({portfolio_data.get('daily_change_pct', 0):.2f}%)
                        </span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Return:</span>
                        <span class="{'positive' if portfolio_data.get('total_return', 0) >= 0 else 'negative'}">
                            {portfolio_data.get('total_return', 0):.2f}%
                        </span>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fullstockai.com" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Full Portfolio</a>
                </div>
                
                <div class="footer">
                    <p>Portfolio update generated on {data['timestamp']}</p>
                    <p>© 2025 FullStock AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_portfolio_update_text(self, data):
        """Generate text content for portfolio update"""
        portfolio_data = data.get('portfolio_data', {})
        
        text = f"""
FullStock AI - Portfolio Update

Portfolio Performance Summary:

Total Value: ${portfolio_data.get('total_value', 0):,.2f}
Daily Change: ${portfolio_data.get('daily_change', 0):,.2f} ({portfolio_data.get('daily_change_pct', 0):.2f}%)
Total Return: {portfolio_data.get('total_return', 0):.2f}%

Visit your FullStock AI dashboard for detailed analysis and recommendations.

Update generated on: {data['timestamp']}

Best regards,
FullStock AI Team
        """
        
        return text.strip()
    
    def _generate_oracle_insight_html(self, data):
        """Generate HTML for Oracle insight"""
        ticker = data['ticker']
        oracle_vision = data.get('oracle_vision', {})
        
        archetype = oracle_vision.get('archetype', 'Oracle')
        symbol = oracle_vision.get('archetype_symbol', '🔮')
        vision = oracle_vision.get('vision', 'The cosmic patterns reveal themselves to patient observers.')
        emotional_state = oracle_vision.get('emotional_state', 'CONTEMPLATION')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #1a1a2e; color: #eee; }}
                .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); padding: 30px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.3); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #ffd700; }}
                .archetype {{ font-size: 48px; text-align: center; margin: 20px 0; }}
                .vision-box {{ background: rgba(255,215,0,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffd700; }}
                .emotional-state {{ text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FullStock AI Oracle</div>
                    <h2>Mystical Vision for {ticker}</h2>
                </div>
                
                <div class="archetype">{symbol}</div>
                <h3 style="text-align: center; color: #ffd700;">The {archetype} Speaks</h3>
                
                <div class="vision-box">
                    <p style="font-style: italic; line-height: 1.6;">{vision}</p>
                </div>
                
                <div class="emotional-state">
                    <strong>Emotional State:</strong> {emotional_state}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fullstockai.com" style="display: inline-block; background-color: #ffd700; color: #1a1a2e; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Explore Oracle Visions</a>
                </div>
                
                <div class="footer">
                    <p>Oracle vision channeled on {data['timestamp']}</p>
                    <p>© 2025 FullStock AI. The Oracle sees all.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_oracle_insight_text(self, data):
        """Generate text content for Oracle insight"""
        ticker = data['ticker']
        oracle_vision = data.get('oracle_vision', {})
        
        archetype = oracle_vision.get('archetype', 'Oracle')
        vision = oracle_vision.get('vision', 'The cosmic patterns reveal themselves to patient observers.')
        emotional_state = oracle_vision.get('emotional_state', 'CONTEMPLATION')
        
        text = f"""
FullStock AI Oracle - Mystical Vision

{ticker} Oracle Vision

The {archetype} Speaks:

{vision}

Emotional State: {emotional_state}

The Oracle's vision has been cast for {ticker}. Consider these mystical insights as you navigate the cosmic currents of the market.

Vision channeled on: {data['timestamp']}

May the Oracle guide your path,
FullStock AI Oracle System
        """
        
        return text.strip()
    
    def _generate_market_summary_html(self, data):
        """Generate HTML for market summary"""
        market_data = data.get('market_data', {})
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .summary-item {{ padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FullStock AI</div>
                    <h2>Daily Market Summary</h2>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3>Market Overview</h3>
                    <div class="summary-item">
                        <span><strong>Market Sentiment:</strong></span>
                        <span>{market_data.get('sentiment', 'NEUTRAL')}</span>
                    </div>
                    <div class="summary-item">
                        <span><strong>Top Performer:</strong></span>
                        <span>{market_data.get('top_performer', 'N/A')}</span>
                    </div>
                    <div class="summary-item">
                        <span><strong>Market Volatility:</strong></span>
                        <span>{market_data.get('volatility', 'MODERATE')}</span>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://fullstockai.com" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Market Analysis</a>
                </div>
                
                <div class="footer">
                    <p>Market summary for {data['timestamp']}</p>
                    <p>© 2025 FullStock AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_market_summary_text(self, data):
        """Generate text content for market summary"""
        market_data = data.get('market_data', {})
        
        text = f"""
FullStock AI - Daily Market Summary

Market Overview:

Market Sentiment: {market_data.get('sentiment', 'NEUTRAL')}
Top Performer: {market_data.get('top_performer', 'N/A')}
Market Volatility: {market_data.get('volatility', 'MODERATE')}

For detailed market analysis and personalized recommendations, visit your FullStock AI dashboard.

Summary generated on: {data['timestamp']}

Best regards,
FullStock AI Team
        """
        
        return text.strip()
    
    def _generate_system_alert_html(self, data):
        """Generate HTML for system alert"""
        alert_type = data['alert_type']
        alert_message = data['alert_message']
        severity = data['severity']
        
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545',
            'critical': '#6f42c1'
        }
        
        color = severity_colors.get(severity, '#ffc107')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .alert-box {{ background-color: {color}; color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .severity {{ font-size: 18px; font-weight: bold; text-transform: uppercase; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">FullStock AI</div>
                    <h2>System Alert</h2>
                </div>
                
                <div class="alert-box">
                    <div class="severity">{severity} Priority</div>
                    <h3>{alert_type}</h3>
                    <p>{alert_message}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <p><strong>Alert Time:</strong> {data['timestamp']}</p>
                    <p>Please review system status and take appropriate action if necessary.</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 FullStock AI. System Monitoring.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_system_alert_text(self, data):
        """Generate text content for system alert"""
        alert_type = data['alert_type']
        alert_message = data['alert_message']
        severity = data['severity']
        
        text = f"""
FullStock AI - System Alert

PRIORITY: {severity.upper()}

Alert Type: {alert_type}

Message: {alert_message}

Alert Time: {data['timestamp']}

Please review system status and take appropriate action if necessary.

FullStock AI System Monitoring
        """
        
        return text.strip()
    
    def _log_notification(self, notification_data):
        """Log notification to history"""
        try:
            self.notification_history.append(notification_data)
            self._save_notification_history()
        except Exception as e:
            logging.error(f"Error logging notification: {str(e)}")
    
    def get_notification_history(self, limit=50, notification_type=None):
        """Get notification history"""
        try:
            history = self.notification_history.copy()
            
            # Filter by type if specified
            if notification_type:
                history = [n for n in history if n.get('type') == notification_type]
            
            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logging.error(f"Error getting notification history: {str(e)}")
            return []
    
    def get_notification_stats(self):
        """Get notification statistics"""
        try:
            total_notifications = len(self.notification_history)
            
            # Count by type
            type_counts = {}
            success_count = 0
            
            for notification in self.notification_history:
                notif_type = notification.get('type', 'unknown')
                type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
                
                if notification.get('success', False):
                    success_count += 1
            
            success_rate = (success_count / total_notifications * 100) if total_notifications > 0 else 0
            
            return {
                'total_notifications': total_notifications,
                'success_count': success_count,
                'failed_count': total_notifications - success_count,
                'success_rate': success_rate,
                'type_distribution': type_counts,
                'last_notification': self.notification_history[-1].get('timestamp') if self.notification_history else None
            }
            
        except Exception as e:
            logging.error(f"Error getting notification stats: {str(e)}")
            return {}
