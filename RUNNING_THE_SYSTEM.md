# How to Run the Hockey Stats Application with Performance Monitoring

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to the application directory
cd hockey_stats_webapp

# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for performance monitoring
pip install psutil  # For memory monitoring
pip install requests  # For webhook notifications (if not already installed)
```

### 2. Basic Local Development (Without Google Sheets)

```bash
# Run the application locally
python app.py
```

The application will start on `http://localhost:8050`

**Note**: Without Google Sheets credentials, the app will run in "demo mode" with limited functionality, but you can still access the performance monitoring features.

### 3. Production Setup (With Google Sheets Integration)

#### Environment Variables

Create a `.env` file in the `hockey_stats_webapp` directory:

```bash
# Google Sheets Integration
GOOGLE_CREDENTIALS={"type": "service_account", "project_id": "your-project"...}
GOOGLE_SHEET_ID=your-google-sheet-id
HOCKEY_STATS_PASSWORD=your-team-password
SECRET_KEY=your-secret-key

# Performance Monitoring (Optional)
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_ALERTING=true

# Email Alerts (Optional)
ALERT_SMTP_SERVER=smtp.gmail.com
ALERT_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your-email@gmail.com
ALERT_EMAIL_PASSWORD=your-app-password
ALERT_FROM_EMAIL=alerts@yourapp.com
ALERT_TO_EMAILS=admin@yourapp.com,ops@yourapp.com

# Slack Alerts (Optional)
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_SLACK_CHANNEL=#hockey-stats-alerts
```

Then run:

```bash
python app.py
```

## Performance Monitoring Features

### Accessing the App Performance Dashboard

1. **Login as a Coach**: Only coaches have access to the app performance dashboard
2. **Navigate to App Performance**: Look for the "App Performance" tab in the navigation menu
3. **View Real-time Metrics**: The dashboard updates every 5 seconds automatically

### Dashboard Features

- **Response Time Monitoring**: Track average, max, and 95th percentile response times
- **Error Rate Tracking**: Monitor application errors and failure rates
- **Cache Performance**: View cache hit/miss ratios and efficiency
- **API Quota Usage**: Monitor Google Sheets API usage against quotas
- **Real-time Charts**: Interactive charts showing trends over time
- **Performance Alerts**: Live alerts when thresholds are exceeded

### Testing the Performance Monitoring

Run the example script to see the monitoring in action:

```bash
cd hockey_stats_webapp
python examples/alerting_integration_example.py
```

This will:
- Simulate normal operations
- Trigger slow operations (response time alerts)
- Generate errors (error rate alerts)
- Test cache performance monitoring
- Demonstrate memory and API quota monitoring

## Advanced Configuration

### Custom Alerting Configuration

Edit `hockey_stats_webapp/config/alerting_config.json` to customize:

- **Alert Thresholds**: Response time, error rate, cache performance limits
- **Time Windows**: How long to monitor before triggering alerts
- **Notification Channels**: Email, Slack, webhook configurations
- **Cooldown Periods**: Prevent alert spam

### Integration with Existing Services

The performance monitoring automatically integrates with existing services. To add monitoring to custom functions:

```python
from services.performance_decorators import track_performance

@track_performance("my_custom_operation")
def my_function():
    # Your code here
    pass
```

### Manual Performance Tracking

```python
from services.performance_integration import track_user_action

with track_user_action("user_clicked_button", session_id):
    # Handle user action
    process_user_request()
```

## Deployment Options

### Local Development

```bash
python app.py
```
- Runs on `http://localhost:8050`
- Debug mode disabled for performance
- Performance monitoring active

### Production with Gunicorn

```bash
gunicorn hockey_stats_webapp.app:server --bind 0.0.0.0:8050
```

### Docker (if you have a Dockerfile)

```bash
docker build -t hockey-stats .
docker run -p 8050:8050 --env-file .env hockey-stats
```

### Cloud Deployment (Render, Heroku, Railway)

The application is configured for cloud deployment with:
- `Procfile`: `web: gunicorn hockey_stats_webapp.app:server`
- Environment variable configuration
- Automatic performance monitoring initialization

## Monitoring and Maintenance

### Health Checks

Check application health at: `http://your-app/performance` (coach login required)

### Log Monitoring

Performance alerts and metrics are logged to the console. In production, configure log aggregation to capture:
- Performance threshold violations
- Error rate spikes
- Cache performance issues
- API quota warnings

### Troubleshooting

#### Common Issues

1. **App Performance Dashboard Not Loading**
   - Ensure you're logged in as a coach
   - Check browser console for JavaScript errors
   - Verify performance monitoring is enabled

2. **Alerts Not Triggering**
   - Check `alerting_config.json` configuration
   - Verify environment variables for notification channels
   - Check console logs for alerting system status

3. **High Memory Usage**
   - Performance metrics are stored in memory with automatic cleanup
   - Adjust retention periods in configuration if needed
   - Monitor memory usage in the performance dashboard

#### Debug Mode

For debugging, you can enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Impact

The monitoring system has minimal impact:
- **Memory**: ~1-5MB additional usage
- **CPU**: <1% overhead
- **Network**: Only for sending alerts
- **Storage**: Configuration files only

## Security Considerations

- **Access Control**: App Performance dashboard restricted to coaches
- **Credential Management**: Use environment variables for sensitive data
- **TLS Encryption**: Email and webhook notifications use secure connections
- **Session Security**: Proper session management and cleanup

## Getting Help

1. **Check Logs**: Console output shows detailed startup and error information
2. **Test Examples**: Run the example scripts to verify functionality
3. **Configuration**: Review `alerting_config.json` for customization options
4. **Performance Status**: Use the dashboard to check system health

The system is designed to be robust and continue working even if monitoring components fail, ensuring your core hockey stats functionality remains available.