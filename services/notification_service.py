import json
import os
import logging
from datetime import datetime, timedelta
from flask_mail import Message
from app import mail, socketio
import smtplib
from email.mime.text import MimeText
import yfinance as yf

class NotificationService:
    """Enhanced notification service with email/SMS alerts"""
    
    def __init__(self):
        self.alerts_file = 'data/price_alerts.json'
        self.notification_log = 'data/notification_log.json'
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        """Ensure notification data files exist"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.notification_log):
            with open(self.notification_log, 'w') as f:
                json.dump([], f)
    
    def create_alert(self, ticker, alert_type, target_value, user_id='anonymous', email=None):
        """Create a new price alert"""
        try:
            # Load existing alerts
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)
            
            alert_id = f"{user_id}_{ticker}_{alert_type}_{datetime.utcnow().timestamp()}"
            
            alert_data = {
                'id': alert_id,
                'user_id': user_id,
                'ticker': ticker,
                'alert_type': alert_type,  # 'price_above', 'price_below', 'prediction_change'
                'target_value': target_value,
                'email': email,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'triggered_at': None,
                'trigger_count': 0
            }
            
            alerts[alert_id] = alert_data
            
            # Save alerts
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            logging.info(f"Created alert {alert_id} for {ticker}")
            
            return {'status': 'success', 'alert_id': alert_id, 'message': 'Alert created successfully'}
            
        except Exception as e:
            logging.error(f"Error creating alert: {str(e)}")
            return {'status': 'error', 'message': 'Failed to create alert'}
    
    def get_user_alerts(self, user_id):
        """Get all alerts for a user"""
        try:
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)
            
            user_alerts = {
                alert_id: alert_data 
                for alert_id, alert_data in alerts.items() 
                if alert_data['user_id'] == user_id
            }
            
            return {'status': 'success', 'alerts': user_alerts}
            
        except Exception as e:
            logging.error(f"Error getting user alerts: {str(e)}")
            return {'status': 'error', 'message': 'Failed to retrieve alerts'}
    
    def delete_alert(self, alert_id):
        """Delete an alert"""
        try:
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)
            
            if alert_id in alerts:
                del alerts[alert_id]
                
                with open(self.alerts_file, 'w') as f:
                    json.dump(alerts, f, indent=2)
                
                return {'status': 'success', 'message': 'Alert deleted successfully'}
            else:
                return {'status': 'error', 'message': 'Alert not found'}
                
        except Exception as e:
            logging.error(f"Error deleting alert: {str(e)}")
            return {'status': 'error', 'message': 'Failed to delete alert'}
    
    def check_price_alerts(self):
        """Check all active alerts and trigger notifications"""
        try:
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)
            
            active_alerts = {
                alert_id: alert_data 
                for alert_id, alert_data in alerts.items() 
                if alert_data['is_active']
            }
            
            triggered_alerts = []
            
            for alert_id, alert_data in active_alerts.items():
                if self._check_alert_condition(alert_data):
                    self._trigger_alert(alert_id, alert_data)
                    triggered_alerts.append(alert_id)
            
            # Update alerts file
            if triggered_alerts:
                for alert_id in triggered_alerts:
                    alerts[alert_id]['triggered_at'] = datetime.utcnow().isoformat()
                    alerts[alert_id]['trigger_count'] += 1
                
                with open(self.alerts_file, 'w') as f:
                    json.dump(alerts, f, indent=2)
                
                logging.info(f"Triggered {len(triggered_alerts)} alerts")
            
        except Exception as e:
            logging.error(f"Error checking price alerts: {str(e)}")
    
    def _check_alert_condition(self, alert_data):
        """Check if alert condition is met"""
        try:
            ticker = alert_data['ticker']
            alert_type = alert_data['alert_type']
            target_value = alert_data['target_value']
            
            # Get current price
            if ticker.endswith('-USD'):  # Crypto
                stock = yf.Ticker(ticker)
            else:  # Stock
                stock = yf.Ticker(ticker)
            
            hist = stock.history(period='1d')
            if hist.empty:
                return False
            
            current_price = hist['Close'].iloc[-1]
            
            # Check condition based on alert type
            if alert_type == 'price_above':
                return current_price > target_value
            elif alert_type == 'price_below':
                return current_price < target_value
            elif alert_type == 'prediction_change':
                # This would require checking prediction changes
                # Simplified implementation
                return False
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking alert condition: {str(e)}")
            return False
    
    def _trigger_alert(self, alert_id, alert_data):
        """Trigger alert notification"""
        try:
            ticker = alert_data['ticker']
            alert_type = alert_data['alert_type']
            target_value = alert_data['target_value']
            email = alert_data.get('email')
            
            # Get current price for notification
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1d')
            current_price = hist['Close'].iloc[-1] if not hist.empty else target_value
            
            # Create notification message
            if alert_type == 'price_above':
                message = f"{ticker} price ${current_price:.2f} is above your alert level of ${target_value:.2f}"
            elif alert_type == 'price_below':
                message = f"{ticker} price ${current_price:.2f} is below your alert level of ${target_value:.2f}"
            else:
                message = f"{ticker} alert triggered: {alert_type}"
            
            # Send WebSocket notification
            socketio.emit('price_alert', {
                'alert_id': alert_id,
                'ticker': ticker,
                'message': message,
                'current_price': float(current_price),
                'target_value': target_value,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send email if provided
            if email:
                self._send_email_notification(email, ticker, message)
            
            # Log notification
            self._log_notification(alert_id, message)
            
            logging.info(f"Triggered alert {alert_id}: {message}")
            
        except Exception as e:
            logging.error(f"Error triggering alert {alert_id}: {str(e)}")
    
    def _send_email_notification(self, email, ticker, message):
        """Send email notification"""
        try:
            msg = Message(
                subject=f"FullStock AI Alert: {ticker}",
                sender=os.environ.get('MAIL_USERNAME', 'noreply@fullstock.ai'),
                recipients=[email],
                body=f"""
FullStock AI Price Alert

{message}

Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This is an automated alert from FullStock AI vNext Ultimate.

Best regards,
The FullStock AI Team
                """
            )
            
            mail.send(msg)
            logging.info(f"Email alert sent to {email}")
            
        except Exception as e:
            logging.error(f"Error sending email notification: {str(e)}")
    
    def _log_notification(self, alert_id, message):
        """Log notification for audit trail"""
        try:
            with open(self.notification_log, 'r') as f:
                log_entries = json.load(f)
            
            log_entry = {
                'alert_id': alert_id,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'price_alert'
            }
            
            log_entries.append(log_entry)
            
            # Keep only last 1000 entries
            if len(log_entries) > 1000:
                log_entries = log_entries[-1000:]
            
            with open(self.notification_log, 'w') as f:
                json.dump(log_entries, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error logging notification: {str(e)}")
    
    def send_system_notification(self, title, message, notification_type='info'):
        """Send system-wide notification"""
        try:
            # Send WebSocket notification
            socketio.emit('system_notification', {
                'title': title,
                'message': message,
                'type': notification_type,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Log system notification
            self._log_notification('system', f"{title}: {message}")
            
        except Exception as e:
            logging.error(f"Error sending system notification: {str(e)}")
    
    def get_notification_statistics(self):
        """Get notification statistics"""
        try:
            with open(self.notification_log, 'r') as f:
                log_entries = json.load(f)
            
            # Calculate statistics
            total_notifications = len(log_entries)
            
            # Last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_notifications = [
                entry for entry in log_entries 
                if datetime.fromisoformat(entry['timestamp']) > yesterday
            ]
            
            return {
                'total_notifications': total_notifications,
                'recent_notifications': len(recent_notifications),
                'notification_types': {
                    'price_alerts': len([e for e in log_entries if e['type'] == 'price_alert']),
                    'system_notifications': len([e for e in log_entries if e['type'] == 'system']),
                },
                'last_notification': log_entries[-1] if log_entries else None
            }
            
        except Exception as e:
            logging.error(f"Error getting notification statistics: {str(e)}")
            return {'error': 'Failed to get statistics'}

# Background function to be called by scheduler
def check_price_alerts():
    """Background function to check price alerts"""
    notification_service = NotificationService()
    notification_service.check_price_alerts()
