"""
Alerting System Setup

Provides utilities to set up and configure the performance alerting system
for the hockey stats application.
"""

import os
import logging
from typing import Optional
from .alerting_integration import initialize_alerting_integration, get_alerting_integration

def setup_alerting_for_hockey_stats(
    config_file: Optional[str] = None,
    enable_email_alerts: bool = False,
    enable_slack_alerts: bool = False,
    start_monitoring: bool = True
) -> bool:
    """
    Set up performance alerting for the hockey stats application
    
    Args:
        config_file: Path to alerting configuration file
        enable_email_alerts: Whether to enable email notifications
        enable_slack_alerts: Whether to enable Slack notifications  
        start_monitoring: Whether to start the monitoring thread
    
    Returns:
        bool: True if setup was successful
    """
    try:
        # Determine config file path
        if not config_file:
            config_file = os.path.join(
                os.path.dirname(__file__), '..', 'config', 'alerting_config.json'
            )
        
        # Initialize the alerting integration
        initialize_alerting_integration(config_file, start_monitoring)
        
        # Get the integration instance
        alerting = get_alerting_integration()
        
        # Configure notification channels based on environment variables
        if enable_email_alerts:
            _configure_email_alerts(alerting)
        
        if enable_slack_alerts:
            _configure_slack_alerts(alerting)
        
        logging.info("Performance alerting system initialized successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize alerting system: {e}")
        return False

def _configure_email_alerts(alerting):
    """Configure email alerts based on environment variables"""
    email_config = {
        'smtp_server': os.environ.get('ALERT_SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.environ.get('ALERT_SMTP_PORT', '587')),
        'username': os.environ.get('ALERT_EMAIL_USERNAME'),
        'password': os.environ.get('ALERT_EMAIL_PASSWORD'),
        'from_email': os.environ.get('ALERT_FROM_EMAIL'),
        'to_emails': os.environ.get('ALERT_TO_EMAILS', '').split(','),
        'use_tls': os.environ.get('ALERT_EMAIL_TLS', 'true').lower() == 'true',
        'enabled': True
    }
    
    # Only enable if required fields are present
    if email_config['username'] and email_config['password'] and email_config['from_email']:
        # Update the email channel configuration
        if hasattr(alerting.alerting_system, 'notification_channels'):
            email_channel = alerting.alerting_system.notification_channels.get('email')
            if email_channel:
                email_channel.config.update(email_config)
                email_channel.enabled = True
                logging.info("Email alerts configured successfully")
            else:
                logging.warning("Email notification channel not found")
    else:
        logging.warning("Email alerts not configured - missing required environment variables")

def _configure_slack_alerts(alerting):
    """Configure Slack alerts based on environment variables"""
    slack_webhook = os.environ.get('ALERT_SLACK_WEBHOOK_URL')
    slack_channel = os.environ.get('ALERT_SLACK_CHANNEL', '#hockey-stats-alerts')
    
    if slack_webhook:
        # Update the Slack channel configuration
        if hasattr(alerting.alerting_system, 'notification_channels'):
            slack_channel_obj = alerting.alerting_system.notification_channels.get('slack')
            if slack_channel_obj:
                slack_channel_obj.config.update({
                    'webhook_url': slack_webhook,
                    'channel': slack_channel,
                    'enabled': True
                })
                slack_channel_obj.enabled = True
                logging.info("Slack alerts configured successfully")
            else:
                logging.warning("Slack notification channel not found")
    else:
        logging.warning("Slack alerts not configured - missing webhook URL")

def get_alerting_status() -> dict:
    """Get the current status of the alerting system"""
    try:
        alerting = get_alerting_integration()
        return alerting.get_alert_status()
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

def trigger_test_alert():
    """Trigger a test alert to verify the system is working"""
    try:
        alerting = get_alerting_integration()
        
        # Record a high response time to trigger an alert
        alerting.record_custom_metric('response_time', 15.0)  # 15 seconds - should trigger critical alert
        
        # Manually check thresholds
        alerting.trigger_manual_check()
        
        logging.info("Test alert triggered")
        return True
        
    except Exception as e:
        logging.error(f"Failed to trigger test alert: {e}")
        return False

def add_performance_monitoring_to_service(service_class):
    """
    Decorator to add performance monitoring to a service class
    
    This will automatically monitor all public methods of the service
    """
    from .alerting_integration import monitor_performance
    
    # Get all public methods
    for attr_name in dir(service_class):
        if not attr_name.startswith('_'):
            attr = getattr(service_class, attr_name)
            if callable(attr):
                # Wrap the method with performance monitoring
                wrapped_method = monitor_performance(f"{service_class.__name__}.{attr_name}")(attr)
                setattr(service_class, attr_name, wrapped_method)
    
    return service_class

# Environment variable configuration helper
def get_alerting_config_from_env() -> dict:
    """Get alerting configuration from environment variables"""
    return {
        'enable_email_alerts': os.environ.get('ENABLE_EMAIL_ALERTS', 'false').lower() == 'true',
        'enable_slack_alerts': os.environ.get('ENABLE_SLACK_ALERTS', 'false').lower() == 'true',
        'start_monitoring': os.environ.get('START_ALERTING_MONITORING', 'true').lower() == 'true',
        'config_file': os.environ.get('ALERTING_CONFIG_FILE'),
        'check_interval': int(os.environ.get('ALERTING_CHECK_INTERVAL', '60'))
    }