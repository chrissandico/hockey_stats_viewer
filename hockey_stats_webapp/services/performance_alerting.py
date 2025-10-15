"""
Performance Alerting System

Provides configurable performance thresholds, alerting mechanisms,
and automatic performance degradation detection.
"""

import time
import threading
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from collections import deque, defaultdict
@dataclass
class AlertThreshold:
    """Configuration for performance alert thresholds"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    time_window_minutes: int = 10
    min_samples: int = 5
    enabled: bool = True

@dataclass
class AlertRule:
    """Defines when and how to trigger alerts"""
    name: str
    condition: str  # 'greater_than', 'less_than', 'equals'
    threshold: AlertThreshold
    notification_channels: List[str] = field(default_factory=list)
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Represents a triggered alert"""
    rule_name: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # 'warning', 'critical'
    timestamp: datetime
    message: str
    additional_data: Dict[str, Any] = field(default_factory=dict)

class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
    
    def send_notification(self, alert: Alert) -> bool:
        """Send notification for the given alert"""
        raise NotImplementedError

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email')
        self.to_emails = config.get('to_emails', [])
        self.use_tls = config.get('use_tls', True)
    
    def send_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        if not self.enabled or not self.to_emails:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.upper()}] Hockey Stats Performance Alert: {alert.rule_name}"
            
            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            logging.info(f"Email alert sent successfully for {alert.rule_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
            return False
    
    def _format_email_body(self, alert: Alert) -> str:
        """Format alert as HTML email body"""
        severity_color = '#ff4444' if alert.severity == 'critical' else '#ff8800'
        
        return f"""
        <html>
        <body>
            <h2 style="color: {severity_color};">Performance Alert Triggered</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Alert Rule:</strong></td><td>{alert.rule_name}</td></tr>
                <tr><td><strong>Metric:</strong></td><td>{alert.metric_name}</td></tr>
                <tr><td><strong>Current Value:</strong></td><td>{alert.current_value:.2f}</td></tr>
                <tr><td><strong>Threshold:</strong></td><td>{alert.threshold_value:.2f}</td></tr>
                <tr><td><strong>Severity:</strong></td><td style="color: {severity_color};">{alert.severity.upper()}</td></tr>
                <tr><td><strong>Time:</strong></td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            </table>
            <p><strong>Message:</strong> {alert.message}</p>
            {self._format_additional_data(alert.additional_data)}
        </body>
        </html>
        """
    
    def _format_additional_data(self, data: Dict[str, Any]) -> str:
        """Format additional alert data as HTML"""
        if not data:
            return ""
        
        html = "<h3>Additional Information:</h3><ul>"
        for key, value in data.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html

class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.webhook_url = config.get('webhook_url')
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.timeout = config.get('timeout', 10)
    
    def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            payload = {
                'alert_rule': alert.rule_name,
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat(),
                'message': alert.message,
                'additional_data': alert.additional_data
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logging.info(f"Webhook alert sent successfully for {alert.rule_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")
            return False

class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.webhook_url = config.get('webhook_url')
        self.channel = config.get('channel', '#alerts')
        self.username = config.get('username', 'Hockey Stats Bot')
    
    def send_notification(self, alert: Alert) -> bool:
        """Send Slack notification"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            color = 'danger' if alert.severity == 'critical' else 'warning'
            
            payload = {
                'channel': self.channel,
                'username': self.username,
                'attachments': [{
                    'color': color,
                    'title': f"Performance Alert: {alert.rule_name}",
                    'fields': [
                        {'title': 'Metric', 'value': alert.metric_name, 'short': True},
                        {'title': 'Current Value', 'value': f"{alert.current_value:.2f}", 'short': True},
                        {'title': 'Threshold', 'value': f"{alert.threshold_value:.2f}", 'short': True},
                        {'title': 'Severity', 'value': alert.severity.upper(), 'short': True},
                    ],
                    'text': alert.message,
                    'ts': int(alert.timestamp.timestamp())
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logging.info(f"Slack alert sent successfully for {alert.rule_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send Slack alert: {e}")
            return False

class PerformanceDegradationDetector:
    """Detects performance degradation patterns"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_metrics: Dict[str, float] = {}
        self.degradation_threshold = 0.5  # 50% degradation threshold
    
    def add_metric(self, metric_name: str, value: float, timestamp: datetime):
        """Add a metric value to the history"""
        self.metric_history[metric_name].append((value, timestamp))
        
        # Update baseline if we have enough data
        if len(self.metric_history[metric_name]) >= 20:
            self._update_baseline(metric_name)
    
    def _update_baseline(self, metric_name: str):
        """Update baseline performance for a metric"""
        recent_values = [v for v, t in list(self.metric_history[metric_name])[-20:]]
        self.baseline_metrics[metric_name] = sum(recent_values) / len(recent_values)
    
    def detect_degradation(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Detect if performance has degraded significantly"""
        if metric_name not in self.baseline_metrics:
            return None
        
        history = self.metric_history[metric_name]
        if len(history) < 10:
            return None
        
        # Get recent average (last 10 values)
        recent_values = [v for v, t in list(history)[-10:]]
        recent_avg = sum(recent_values) / len(recent_values)
        
        baseline = self.baseline_metrics[metric_name]
        
        # Check for degradation (higher values are worse for response times)
        if recent_avg > baseline * (1 + self.degradation_threshold):
            degradation_pct = ((recent_avg - baseline) / baseline) * 100
            
            return {
                'metric_name': metric_name,
                'baseline_value': baseline,
                'current_value': recent_avg,
                'degradation_percentage': degradation_pct,
                'detection_time': datetime.now()
            }
        
        return None

class PerformanceAlertingSystem:
    """Main alerting system that monitors metrics and triggers alerts"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.metric_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.degradation_detector = PerformanceDegradationDetector()
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Load configuration
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        else:
            self._setup_default_config()
    
    def _setup_default_config(self):
        """Setup default alerting configuration"""
        # Default thresholds
        default_thresholds = {
            'response_time': AlertThreshold('response_time', 5.0, 10.0, 10, 5),
            'error_rate': AlertThreshold('error_rate', 0.05, 0.10, 10, 5),
            'cache_miss_rate': AlertThreshold('cache_miss_rate', 0.30, 0.50, 15, 10),
            'memory_usage': AlertThreshold('memory_usage', 0.80, 0.90, 5, 3),
            'api_quota_usage': AlertThreshold('api_quota_usage', 0.80, 0.95, 60, 1)
        }
        
        # Default alert rules
        for name, threshold in default_thresholds.items():
            self.alert_rules[f"{name}_warning"] = AlertRule(
                name=f"{name}_warning",
                condition='greater_than',
                threshold=threshold,
                notification_channels=['console']
            )
            
            self.alert_rules[f"{name}_critical"] = AlertRule(
                name=f"{name}_critical",
                condition='greater_than',
                threshold=AlertThreshold(
                    threshold.metric_name,
                    threshold.critical_threshold,
                    threshold.critical_threshold,
                    threshold.time_window_minutes,
                    threshold.min_samples
                ),
                notification_channels=['console']
            )
        
        # Setup console notification channel
        self.notification_channels['console'] = ConsoleNotificationChannel('console', {})
    
    def load_config(self, config_file: str):
        """Load alerting configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load thresholds and rules
            for rule_config in config.get('alert_rules', []):
                threshold = AlertThreshold(**rule_config['threshold'])
                rule = AlertRule(
                    name=rule_config['name'],
                    condition=rule_config['condition'],
                    threshold=threshold,
                    notification_channels=rule_config.get('notification_channels', []),
                    cooldown_minutes=rule_config.get('cooldown_minutes', 30)
                )
                self.alert_rules[rule.name] = rule
            
            # Load notification channels
            for channel_config in config.get('notification_channels', []):
                channel_type = channel_config['type']
                if channel_type == 'email':
                    channel = EmailNotificationChannel(channel_config['name'], channel_config['config'])
                elif channel_type == 'webhook':
                    channel = WebhookNotificationChannel(channel_config['name'], channel_config['config'])
                elif channel_type == 'slack':
                    channel = SlackNotificationChannel(channel_config['name'], channel_config['config'])
                else:
                    continue
                
                self.notification_channels[channel.name] = channel
            
            logging.info(f"Loaded alerting configuration from {config_file}")
            
        except Exception as e:
            logging.error(f"Failed to load alerting config: {e}")
            self._setup_default_config()
    
    def add_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Add a metric value for monitoring"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.metric_buffer[metric_name].append((value, timestamp))
            self.degradation_detector.add_metric(metric_name, value, timestamp)
    
    def check_thresholds(self):
        """Check all metrics against configured thresholds"""
        with self.lock:
            current_time = datetime.now()
            
            for rule_name, rule in self.alert_rules.items():
                if not rule.threshold.enabled:
                    continue
                
                # Check cooldown period
                if (rule.last_triggered and 
                    current_time - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)):
                    continue
                
                # Get recent metrics for this rule
                metric_values = self._get_recent_metrics(
                    rule.threshold.metric_name,
                    rule.threshold.time_window_minutes
                )
                
                if len(metric_values) < rule.threshold.min_samples:
                    continue
                
                # Calculate metric value based on rule
                if rule.threshold.metric_name == 'error_rate':
                    metric_value = self._calculate_error_rate(metric_values)
                elif rule.threshold.metric_name == 'cache_miss_rate':
                    metric_value = self._calculate_cache_miss_rate(metric_values)
                else:
                    metric_value = sum(metric_values) / len(metric_values)
                
                # Check threshold
                threshold_value = (rule.threshold.warning_threshold 
                                 if 'warning' in rule_name 
                                 else rule.threshold.critical_threshold)
                
                if self._should_trigger_alert(rule.condition, metric_value, threshold_value):
                    severity = 'warning' if 'warning' in rule_name else 'critical'
                    alert = Alert(
                        rule_name=rule_name,
                        metric_name=rule.threshold.metric_name,
                        current_value=metric_value,
                        threshold_value=threshold_value,
                        severity=severity,
                        timestamp=current_time,
                        message=f"{rule.threshold.metric_name} {rule.condition} {threshold_value:.2f}",
                        additional_data={
                            'sample_count': len(metric_values),
                            'time_window_minutes': rule.threshold.time_window_minutes
                        }
                    )
                    
                    self._trigger_alert(alert, rule)
    
    def check_performance_degradation(self):
        """Check for performance degradation patterns"""
        for metric_name in self.metric_buffer.keys():
            degradation = self.degradation_detector.detect_degradation(metric_name)
            if degradation:
                alert = Alert(
                    rule_name='performance_degradation',
                    metric_name=metric_name,
                    current_value=degradation['current_value'],
                    threshold_value=degradation['baseline_value'],
                    severity='warning',
                    timestamp=degradation['detection_time'],
                    message=f"Performance degraded by {degradation['degradation_percentage']:.1f}%",
                    additional_data=degradation
                )
                
                # Use default notification channels for degradation alerts
                self._send_notifications(alert, ['console'])
    
    def _get_recent_metrics(self, metric_name: str, window_minutes: int) -> List[float]:
        """Get metric values from the specified time window"""
        if metric_name not in self.metric_buffer:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_values = []
        
        for value, timestamp in self.metric_buffer[metric_name]:
            if timestamp >= cutoff_time:
                recent_values.append(value)
        
        return recent_values
    
    def _calculate_error_rate(self, values: List[float]) -> float:
        """Calculate error rate from binary success/failure values"""
        if not values:
            return 0.0
        return sum(1 for v in values if v > 0) / len(values)
    
    def _calculate_cache_miss_rate(self, values: List[float]) -> float:
        """Calculate cache miss rate from hit/miss values"""
        if not values:
            return 0.0
        return sum(1 for v in values if v == 0) / len(values)
    
    def _should_trigger_alert(self, condition: str, current_value: float, threshold: float) -> bool:
        """Check if alert should be triggered based on condition"""
        if condition == 'greater_than':
            return current_value > threshold
        elif condition == 'less_than':
            return current_value < threshold
        elif condition == 'equals':
            return abs(current_value - threshold) < 0.001
        return False
    
    def _trigger_alert(self, alert: Alert, rule: AlertRule):
        """Trigger an alert and send notifications"""
        logging.warning(f"Alert triggered: {alert.rule_name} - {alert.message}")
        
        # Update last triggered time
        rule.last_triggered = alert.timestamp
        
        # Send notifications
        self._send_notifications(alert, rule.notification_channels)
    
    def _send_notifications(self, alert: Alert, channel_names: List[str]):
        """Send alert notifications to specified channels"""
        for channel_name in channel_names:
            if channel_name in self.notification_channels:
                try:
                    self.notification_channels[channel_name].send_notification(alert)
                except Exception as e:
                    logging.error(f"Failed to send notification via {channel_name}: {e}")
    
    def start_monitoring(self, check_interval: int = 60):
        """Start the monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logging.info("Performance alerting system started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logging.info("Performance alerting system stopped")
    
    def _monitoring_loop(self, check_interval: int):
        """Main monitoring loop"""
        while self.running:
            try:
                self.check_thresholds()
                self.check_performance_degradation()
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
            
            time.sleep(check_interval)
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Get current alerting system status"""
        with self.lock:
            return {
                'running': self.running,
                'active_rules': len([r for r in self.alert_rules.values() if r.threshold.enabled]),
                'notification_channels': len(self.notification_channels),
                'metrics_tracked': len(self.metric_buffer),
                'total_metric_samples': sum(len(buffer) for buffer in self.metric_buffer.values())
            }

class ConsoleNotificationChannel(NotificationChannel):
    """Console/logging notification channel for development"""
    
    def send_notification(self, alert: Alert) -> bool:
        """Log alert to console"""
        log_level = logging.ERROR if alert.severity == 'critical' else logging.WARNING
        message = (f"ALERT [{alert.severity.upper()}] {alert.rule_name}: "
                  f"{alert.metric_name}={alert.current_value:.2f} "
                  f"(threshold: {alert.threshold_value:.2f}) - {alert.message}")
        
        logging.log(log_level, message)
        return True

# Global alerting system instance
_alerting_system = None

def get_alerting_system() -> PerformanceAlertingSystem:
    """Get the global alerting system instance"""
    global _alerting_system
    if _alerting_system is None:
        config_file = os.environ.get('ALERTING_CONFIG_FILE')
        _alerting_system = PerformanceAlertingSystem(config_file)
    return _alerting_system

def initialize_alerting_system(config_file: Optional[str] = None, start_monitoring: bool = True):
    """Initialize and optionally start the alerting system"""
    global _alerting_system
    _alerting_system = PerformanceAlertingSystem(config_file)
    
    if start_monitoring:
        _alerting_system.start_monitoring()
    
    return _alerting_system