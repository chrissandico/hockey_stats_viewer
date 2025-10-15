# Project Structure & Organization

## Root Directory Layout

```
├── hockey_stats_webapp/          # Main application package
├── test_*.py                     # Test files (root level)
├── debug_*.py                    # Debug/analysis scripts
├── fix_*.py                      # Data fix scripts
├── *.md                          # Documentation files
├── Procfile                      # Heroku deployment config
├── render.yaml                   # Render.com deployment config
├── requirements.txt              # Python dependencies (root level)
└── credentials.json.sample       # Sample credentials file
```

## Main Application Structure

```
hockey_stats_webapp/
├── app.py                        # Main application entry point
├── config.py                     # Global configuration settings
├── requirements.txt              # Application dependencies
├── credentials.json              # Google service account credentials
├── assets/                       # Static assets
│   ├── css/                      # Custom stylesheets
│   ├── js/                       # JavaScript files
│   └── theshift.jpg              # Background image
├── components/                   # Reusable UI components
│   ├── game_type_filter.py       # Game type filtering component
│   └── period_breakdown.py       # Period breakdown component
├── layouts/                      # Page layouts and views
│   ├── main_layout.py            # Home page layout
│   ├── navigation.py             # Navigation components
│   ├── player_layout.py          # Player statistics view
│   ├── team_layout.py            # Team statistics view
│   └── game_layout.py            # Game analysis view
├── services/                     # Business logic layer
│   ├── auth_service.py           # Authentication logic
│   ├── data_service.py           # Data processing and calculations
│   └── sheets_service.py         # Google Sheets integration
└── utils/                        # Utility functions
```

## Architecture Patterns

### Service Layer Pattern
- **services/**: Contains all business logic and data access
- **sheets_service.py**: Google Sheets API integration and caching
- **data_service.py**: Statistical calculations and data processing
- **auth_service.py**: Authentication and session management

### Layout Component Pattern
- **layouts/**: Page-specific layouts and Dash callbacks
- Each layout file contains both UI components and callback registrations
- Separation of concerns between presentation and business logic

### Configuration Management
- **config.py**: Centralized configuration for game types, coach-only stats
- Environment variables for sensitive data (credentials, passwords)
- Constants for UI styling and business rules

## File Naming Conventions

### Test Files
- `test_*.py`: Comprehensive test files
- `debug_*.py`: Debug and analysis scripts
- `fix_*.py`: Data correction scripts
- `verify_*.py`: Verification scripts

### Documentation
- `*_summary.md`: Implementation summaries
- `*_results.md`: Test results documentation
- `HOCKEY_STATS_APP_DOCUMENTATION.md`: Main technical documentation
- `Hockey_Stats_App_Guide.md`: User guide

### Component Organization
- **Layouts**: One file per major view (player, team, game)
- **Components**: Reusable UI components with their own callbacks
- **Services**: Business logic separated by concern (auth, data, sheets)

## Key Architectural Principles

### Separation of Concerns
- UI components in `layouts/` and `components/`
- Business logic in `services/`
- Configuration in `config.py`
- Static assets in `assets/`

### Dependency Injection
- Services passed to layouts and components
- Enables testing and modularity
- Clear dependency relationships

### Session Management
- Team-based authentication with role differentiation
- Session validation throughout the application
- Secure logout and session cleanup

### Error Handling
- Graceful degradation when services unavailable
- Comprehensive logging for debugging
- User-friendly error messages

### Mobile-First Design
- Responsive layouts in all components
- Touch-friendly UI elements
- Collapsible sections for mobile optimization

## Development Workflow

### Adding New Features
1. Create/modify service layer logic in `services/`
2. Add UI components in `layouts/` or `components/`
3. Register callbacks for interactivity
4. Add tests in root-level `test_*.py` files
5. Update configuration if needed

### Debugging Issues
1. Use `debug_*.py` scripts for analysis
2. Check service initialization in `app.py`
3. Verify data consistency with test scripts
4. Review session management and authentication

### Data Fixes
1. Create `fix_*.py` scripts for data corrections
2. Test fixes with verification scripts
3. Document changes in `*_summary.md` files
4. Deploy fixes through service layer updates