# Testing Guide for Hockey Stats Application

## Running Tests with Authentication

The test files require authentication to access the hockey stats application. You can provide the password in several ways:

### Method 1: Environment Variable (Recommended)
```bash
export HOCKEY_STATS_PASSWORD="your_password_here"
python test_web_api_score_fix.py
python test_web_interface_score_fix.py
```

### Method 2: Command Line Argument
```bash
python test_web_api_score_fix.py http://localhost:8050 your_password_here
python test_web_interface_score_fix.py http://localhost:8050 your_password_here
```

### Method 3: Direct Testing (No Authentication Required)
```bash
python test_score_fix_direct.py
python test_error_handling_logging.py
```

## Test Files Overview

- `test_score_fix_direct.py` - Direct DataService testing (no auth required)
- `test_web_api_score_fix.py` - API endpoint testing (requires auth)
- `test_web_interface_score_fix.py` - Full browser testing (requires auth + ChromeDriver)
- `test_error_handling_logging.py` - Error handling validation (no auth required)

## Security Note

Never commit passwords or sensitive credentials to the repository. Always use environment variables or secure credential management systems in production.