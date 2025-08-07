import psutil
import os
import json
import logging
from datetime import datetime, timedelta
import requests
import yfinance as yf
from app import db
from models import SystemHealth
import numpy as np

class HealthMonitor:
    """System Health Monitoring and Self-Diagnostic Agent"""
    
    def __init__(self):
        self.health_log_file = 'data/health_log.json'
        self.ensure_files_exist()
        
        # Health thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0,
            'response_time_warning': 5.0,  # seconds
            'response_time_critical': 10.0,
            'data_freshness_warning': 15,  # minutes
            'data_freshness_critical': 30
        }
    
    def ensure_files_exist(self):
        """Ensure health monitoring files exist"""
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(self.health_log_file):
            with open(self.health_log_file, 'w') as f:
                json.dump([], f)
    
    def get_health_status(self):
        """Get comprehensive system health status"""
        try:
            # System resource metrics
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()
            disk_usage = self._get_disk_usage()
            
            # API connectivity checks
            api_status = self._check_api_connectivity()
            
            # Data freshness checks
            data_freshness = self._check_data_freshness()
            
            # Application health checks
            app_health = self._check_application_health()
            
            # Calculate overall health score
            overall_status, health_score = self._calculate_overall_health(
                cpu_usage, memory_usage, disk_usage, api_status, data_freshness, app_health
            )
            
            # Generate recommendations
            recommendations = self._generate_health_recommendations(
                cpu_usage, memory_usage, disk_usage, api_status, data_freshness
            )
            
            # Create health report
            health_report = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': overall_status,
                'health_score': health_score,
                'system_resources': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'disk_usage': disk_usage
                },
                'api_connectivity': api_status,
                'data_freshness': data_freshness,
                'application_health': app_health,
                'recommendations': recommendations,
                'uptime': self._get_system_uptime(),
                'python_version': self._get_python_info(),
                'environment_status': self._check_environment_variables()
            }
            
            # Store health status in database
            self._store_health_status(health_report)
            
            # Log health check
            self._log_health_check(health_report)
            
            return health_report
            
        except Exception as e:
            logging.error(f"Error getting health status: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'ERROR',
                'error': f'Health check failed: {str(e)}'
            }
    
    def _get_cpu_usage(self):
        """Get CPU usage metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            status = 'OK'
            if cpu_percent > self.thresholds['cpu_critical']:
                status = 'CRITICAL'
            elif cpu_percent > self.thresholds['cpu_warning']:
                status = 'WARNING'
            
            return {
                'percentage': float(cpu_percent),
                'cpu_count': cpu_count,
                'frequency_mhz': float(cpu_freq.current) if cpu_freq else None,
                'status': status
            }
            
        except Exception as e:
            logging.error(f"Error getting CPU usage: {str(e)}")
            return {'percentage': 0, 'status': 'ERROR', 'error': str(e)}
    
    def _get_memory_usage(self):
        """Get memory usage metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            status = 'OK'
            if memory.percent > self.thresholds['memory_critical']:
                status = 'CRITICAL'
            elif memory.percent > self.thresholds['memory_warning']:
                status = 'WARNING'
            
            return {
                'percentage': float(memory.percent),
                'total_gb': float(memory.total / (1024**3)),
                'available_gb': float(memory.available / (1024**3)),
                'used_gb': float(memory.used / (1024**3)),
                'swap_percentage': float(swap.percent),
                'status': status
            }
            
        except Exception as e:
            logging.error(f"Error getting memory usage: {str(e)}")
            return {'percentage': 0, 'status': 'ERROR', 'error': str(e)}
    
    def _get_disk_usage(self):
        """Get disk usage metrics"""
        try:
            disk = psutil.disk_usage('/')
            
            disk_percent = (disk.used / disk.total) * 100
            
            status = 'OK'
            if disk_percent > self.thresholds['disk_critical']:
                status = 'CRITICAL'
            elif disk_percent > self.thresholds['disk_warning']:
                status = 'WARNING'
            
            return {
                'percentage': float(disk_percent),
                'total_gb': float(disk.total / (1024**3)),
                'used_gb': float(disk.used / (1024**3)),
                'free_gb': float(disk.free / (1024**3)),
                'status': status
            }
            
        except Exception as e:
            logging.error(f"Error getting disk usage: {str(e)}")
            return {'percentage': 0, 'status': 'ERROR', 'error': str(e)}
    
    def _check_api_connectivity(self):
        """Check connectivity to external APIs"""
        api_tests = {
            'yahoo_finance': self._test_yahoo_finance,
            'internet_connectivity': self._test_internet_connectivity
        }
        
        results = {}
        overall_status = 'OK'
        
        for api_name, test_func in api_tests.items():
            try:
                start_time = datetime.utcnow()
                status, response_time, details = test_func()
                
                results[api_name] = {
                    'status': status,
                    'response_time_ms': response_time,
                    'details': details,
                    'last_checked': start_time.isoformat()
                }
                
                if status != 'OK':
                    overall_status = 'WARNING' if overall_status == 'OK' else 'CRITICAL'
                    
            except Exception as e:
                results[api_name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'last_checked': datetime.utcnow().isoformat()
                }
                overall_status = 'CRITICAL'
        
        return {
            'overall_status': overall_status,
            'individual_apis': results
        }
    
    def _test_yahoo_finance(self):
        """Test Yahoo Finance API connectivity"""
        try:
            start_time = datetime.utcnow()
            
            # Try to fetch a simple stock quote
            ticker = yf.Ticker("AAPL")
            info = ticker.history(period="1d")
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if info.empty:
                return 'ERROR', response_time, 'No data returned'
            
            if response_time > self.thresholds['response_time_critical'] * 1000:
                return 'CRITICAL', response_time, 'Response time too slow'
            elif response_time > self.thresholds['response_time_warning'] * 1000:
                return 'WARNING', response_time, 'Response time elevated'
            
            return 'OK', response_time, 'Yahoo Finance API responding normally'
            
        except Exception as e:
            return 'ERROR', 0, f'Yahoo Finance API error: {str(e)}'
    
    def _test_internet_connectivity(self):
        """Test basic internet connectivity"""
        try:
            start_time = datetime.utcnow()
            
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return 'OK', response_time, 'Internet connectivity normal'
            else:
                return 'WARNING', response_time, f'Unexpected status code: {response.status_code}'
                
        except requests.exceptions.Timeout:
            return 'WARNING', 10000, 'Internet connectivity timeout'
        except Exception as e:
            return 'ERROR', 0, f'Internet connectivity error: {str(e)}'
    
    def _check_data_freshness(self):
        """Check freshness of cached data"""
        try:
            freshness_results = {}
            overall_status = 'OK'
            
            # Check model files
            model_files = ['models/random_forest.joblib', 'models/xgboost.model', 'models/lstm.h5']
            for model_file in model_files:
                if os.path.exists(model_file):
                    mtime = os.path.getmtime(model_file)
                    age_hours = (datetime.utcnow().timestamp() - mtime) / 3600
                    
                    freshness_results[model_file] = {
                        'age_hours': float(age_hours),
                        'status': 'OLD' if age_hours > 168 else 'FRESH'  # 7 days
                    }
                else:
                    freshness_results[model_file] = {'status': 'MISSING'}
                    overall_status = 'WARNING'
            
            # Check Oracle logs
            oracle_files = ['oracle_logs/dreams.json', 'oracle_logs/archetypes.json']
            for oracle_file in oracle_files:
                if os.path.exists(oracle_file):
                    mtime = os.path.getmtime(oracle_file)
                    age_minutes = (datetime.utcnow().timestamp() - mtime) / 60
                    
                    status = 'FRESH'
                    if age_minutes > self.thresholds['data_freshness_critical']:
                        status = 'CRITICAL'
                        overall_status = 'CRITICAL' if overall_status != 'CRITICAL' else overall_status
                    elif age_minutes > self.thresholds['data_freshness_warning']:
                        status = 'WARNING'
                        overall_status = 'WARNING' if overall_status == 'OK' else overall_status
                    
                    freshness_results[oracle_file] = {
                        'age_minutes': float(age_minutes),
                        'status': status
                    }
                else:
                    freshness_results[oracle_file] = {'status': 'MISSING'}
                    overall_status = 'WARNING'
            
            return {
                'overall_status': overall_status,
                'file_freshness': freshness_results
            }
            
        except Exception as e:
            logging.error(f"Error checking data freshness: {str(e)}")
            return {'overall_status': 'ERROR', 'error': str(e)}
    
    def _check_application_health(self):
        """Check application-specific health metrics"""
        try:
            health_metrics = {}
            
            # Check database connectivity
            try:
                # Simple database query
                result = db.session.execute("SELECT 1").scalar()
                health_metrics['database'] = {
                    'status': 'OK' if result == 1 else 'ERROR',
                    'details': 'Database connection successful'
                }
            except Exception as e:
                health_metrics['database'] = {
                    'status': 'ERROR',
                    'details': f'Database error: {str(e)}'
                }
            
            # Check critical directories
            critical_dirs = ['data', 'models', 'oracle_logs', 'static']
            missing_dirs = [d for d in critical_dirs if not os.path.exists(d)]
            
            health_metrics['directories'] = {
                'status': 'OK' if not missing_dirs else 'WARNING',
                'missing_directories': missing_dirs
            }
            
            # Check environment variables
            required_env_vars = ['SESSION_SECRET']
            missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
            
            health_metrics['environment'] = {
                'status': 'OK' if not missing_env_vars else 'WARNING',
                'missing_variables': missing_env_vars
            }
            
            return health_metrics
            
        except Exception as e:
            logging.error(f"Error checking application health: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_overall_health(self, cpu, memory, disk, api, data_freshness, app_health):
        """Calculate overall system health score and status"""
        try:
            # Status priority: ERROR > CRITICAL > WARNING > OK
            status_priority = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'ERROR': 3}
            
            statuses = [
                cpu.get('status', 'ERROR'),
                memory.get('status', 'ERROR'),
                disk.get('status', 'ERROR'),
                api.get('overall_status', 'ERROR'),
                data_freshness.get('overall_status', 'ERROR')
            ]
            
            # Add application health statuses
            for metric in app_health.values():
                if isinstance(metric, dict) and 'status' in metric:
                    statuses.append(metric['status'])
            
            # Find highest priority status
            max_priority = max(status_priority.get(status, 3) for status in statuses)
            overall_status = [status for status, priority in status_priority.items() if priority == max_priority][0]
            
            # Calculate health score (0-100)
            score_components = []
            
            # CPU score (0-100, inverted so lower usage = higher score)
            cpu_score = max(0, 100 - cpu.get('percentage', 100))
            score_components.append(cpu_score)
            
            # Memory score
            memory_score = max(0, 100 - memory.get('percentage', 100))
            score_components.append(memory_score)
            
            # Disk score
            disk_score = max(0, 100 - disk.get('percentage', 100))
            score_components.append(disk_score)
            
            # API score
            api_score = 100 if api.get('overall_status') == 'OK' else 50 if api.get('overall_status') == 'WARNING' else 0
            score_components.append(api_score)
            
            # Data freshness score
            freshness_score = 100 if data_freshness.get('overall_status') == 'OK' else 50 if data_freshness.get('overall_status') == 'WARNING' else 0
            score_components.append(freshness_score)
            
            # Calculate weighted average
            health_score = np.mean(score_components)
            
            return overall_status, float(health_score)
            
        except Exception as e:
            logging.error(f"Error calculating overall health: {str(e)}")
            return 'ERROR', 0.0
    
    def _generate_health_recommendations(self, cpu, memory, disk, api, data_freshness):
        """Generate health improvement recommendations"""
        recommendations = []
        
        # CPU recommendations
        if cpu.get('percentage', 0) > self.thresholds['cpu_critical']:
            recommendations.append("CRITICAL: CPU usage extremely high. Consider optimizing algorithms or scaling resources.")
        elif cpu.get('percentage', 0) > self.thresholds['cpu_warning']:
            recommendations.append("WARNING: CPU usage elevated. Monitor for performance issues.")
        
        # Memory recommendations
        if memory.get('percentage', 0) > self.thresholds['memory_critical']:
            recommendations.append("CRITICAL: Memory usage critical. Restart application or increase memory allocation.")
        elif memory.get('percentage', 0) > self.thresholds['memory_warning']:
            recommendations.append("WARNING: High memory usage detected. Consider memory optimization.")
        
        # Disk recommendations
        if disk.get('percentage', 0) > self.thresholds['disk_critical']:
            recommendations.append("CRITICAL: Disk space critically low. Clean up old logs and temporary files.")
        elif disk.get('percentage', 0) > self.thresholds['disk_warning']:
            recommendations.append("WARNING: Disk space running low. Schedule cleanup maintenance.")
        
        # API recommendations
        if api.get('overall_status') != 'OK':
            recommendations.append("API connectivity issues detected. Check internet connection and API endpoints.")
        
        # Data freshness recommendations
        if data_freshness.get('overall_status') == 'CRITICAL':
            recommendations.append("CRITICAL: Data is severely outdated. Update models and refresh data sources.")
        elif data_freshness.get('overall_status') == 'WARNING':
            recommendations.append("WARNING: Some data files are getting old. Schedule data refresh.")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("System health is good. Continue regular monitoring.")
        else:
            recommendations.append("Regular system maintenance recommended to prevent issues.")
        
        return recommendations
    
    def _get_system_uptime(self):
        """Get system uptime information"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.utcnow().timestamp() - boot_time
            uptime_hours = uptime_seconds / 3600
            
            return {
                'uptime_hours': float(uptime_hours),
                'boot_time': datetime.fromtimestamp(boot_time).isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_python_info(self):
        """Get Python environment information"""
        try:
            import sys
            import platform
            
            return {
                'python_version': sys.version,
                'platform': platform.platform(),
                'architecture': platform.architecture()[0]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_environment_variables(self):
        """Check critical environment variables"""
        try:
            env_status = {}
            
            # Check required environment variables
            required_vars = {
                'SESSION_SECRET': 'Application session secret',
                'DATABASE_URL': 'Database connection URL (optional)',
                'MAIL_USERNAME': 'Email service username (optional)',
                'MAIL_PASSWORD': 'Email service password (optional)'
            }
            
            for var_name, description in required_vars.items():
                value = os.environ.get(var_name)
                env_status[var_name] = {
                    'present': value is not None,
                    'description': description,
                    'status': 'OK' if value else 'MISSING'
                }
            
            return env_status
            
        except Exception as e:
            return {'error': str(e)}
    
    def _store_health_status(self, health_report):
        """Store health status in database"""
        try:
            health_record = SystemHealth(
                cpu_usage=health_report['system_resources']['cpu_usage']['percentage'],
                memory_usage=health_report['system_resources']['memory_usage']['percentage'],
                disk_usage=health_report['system_resources']['disk_usage']['percentage'],
                api_status=health_report['api_connectivity']['overall_status'],
                data_freshness=0,  # Simplified for now
                overall_status=health_report['overall_status']
            )
            
            db.session.add(health_record)
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error storing health status in database: {str(e)}")
            db.session.rollback()
    
    def _log_health_check(self, health_report):
        """Log health check to file"""
        try:
            # Load existing logs
            logs = []
            if os.path.exists(self.health_log_file):
                with open(self.health_log_file, 'r') as f:
                    logs = json.load(f)
            
            # Add new log entry
            log_entry = {
                'timestamp': health_report['timestamp'],
                'overall_status': health_report['overall_status'],
                'health_score': health_report['health_score'],
                'cpu_usage': health_report['system_resources']['cpu_usage']['percentage'],
                'memory_usage': health_report['system_resources']['memory_usage']['percentage'],
                'disk_usage': health_report['system_resources']['disk_usage']['percentage'],
                'api_status': health_report['api_connectivity']['overall_status']
            }
            
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Save logs
            with open(self.health_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error logging health check: {str(e)}")
    
    def get_health_history(self, hours=24):
        """Get health check history"""
        try:
            if not os.path.exists(self.health_log_file):
                return []
            
            with open(self.health_log_file, 'r') as f:
                logs = json.load(f)
            
            # Filter logs by time period
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            filtered_logs = []
            for log in logs:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time > cutoff_time:
                    filtered_logs.append(log)
            
            return filtered_logs
            
        except Exception as e:
            logging.error(f"Error getting health history: {str(e)}")
            return []

# Background function to be called by scheduler
def run_health_check():
    """Background function to run health check"""
    health_monitor = HealthMonitor()
    health_status = health_monitor.get_health_status()
    
    # Log critical issues
    if health_status.get('overall_status') in ['CRITICAL', 'ERROR']:
        logging.critical(f"System health critical: {health_status.get('overall_status')}")
    
    return health_status
