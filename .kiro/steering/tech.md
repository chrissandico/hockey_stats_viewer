# Technology Stack & Build System

## Core Technologies

### Backend Framework
- **Python 3.7+**: Primary programming language
- **Dash**: Web framework for building interactive web applications
- **Flask**: Underlying web server (Dash is built on Flask)
- **Gunicorn**: WSGI HTTP server for production deployment

### Frontend Technologies
- **Dash Bootstrap Components (DBC)**: UI component library
- **Bootstrap**: CSS framework for responsive design
- **Font Awesome**: Icon library
- **Custom CSS**: Mobile-first responsive styling

### Data & Authentication
- **Google Sheets API**: Primary data storage backend
- **gspread**: Python library for Google Sheets integration
- **google-auth**: Google OAuth2 authentication
- **pandas**: Data manipulation and analysis
- **python-dotenv**: Environment variable management

### Key Dependencies
```
dash>=2.0.0,<2.14.0
dash-bootstrap-components>=1.0.0
gspread>=5.0.0
pandas
google-auth>=2.0.0
flask<2.3.0
gunicorn>=20.0.0
python-dotenv>=0.19.0
```

## Build & Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
# or
python hockey_stats_webapp/app.py

# Application runs on http://localhost:8050
```

### Testing
```bash
# Run individual test files
python test_[specific_test].py

# Common test patterns
python test_comprehensive_game_type_filtering.py
python test_centralized_stats.py
python test_all_games_fix_comprehensive.py
```

### Production Deployment

#### Render.com (Recommended)
- Uses `render.yaml` configuration
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn hockey_stats_webapp.app:server`
- Environment variables: `GOOGLE_CREDENTIALS`, `GOOGLE_SHEET_ID`, `HOCKEY_STATS_PASSWORD`, `SECRET_KEY`

#### Heroku
- Uses `Procfile`: `web: gunicorn hockey_stats_webapp.app:server`
- Requires same environment variables as Render

#### Railway.app
- Auto-detects `Procfile`
- Same configuration as Heroku

### Environment Variables
- `GOOGLE_CREDENTIALS`: JSON string of service account credentials
- `GOOGLE_SHEET_ID`: Google Sheets document ID
- `HOCKEY_STATS_PASSWORD`: Team access password
- `SECRET_KEY`: Flask session secret key
- `PORT`: Server port (default: 8050)

## Development Patterns

### Module Structure
- Force module reloads on startup to avoid caching issues
- Service layer pattern with dependency injection
- Callback registration pattern for Dash components

### Error Handling
- Graceful degradation when services unavailable
- Comprehensive logging for debugging
- Session validation and cleanup

### Performance Optimizations
- Data caching with TTL (3600 seconds)
- Force refresh capabilities for real-time updates
- Lazy loading of components and data