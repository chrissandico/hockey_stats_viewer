# Product Overview

## Hockey Stats Web Application

A modern, responsive web application for tracking and analyzing youth hockey statistics. The application provides comprehensive tools for coaches, players, and parents to monitor individual performance, team dynamics, and game-by-game analysis.

### Core Purpose
- Track individual player statistics (goals, assists, points, plus/minus, penalty minutes)
- Analyze team performance and generate leaderboards
- Provide detailed game-by-game breakdowns and event tracking
- Support multiple game types (Exhibition, Regular Season, Tournament)
- Offer secure, team-based access with role-based permissions

### Key Features
- **Player Statistics**: Individual performance tracking with season totals and game logs
- **Team Analytics**: Position-based leaderboards, team records, and performance metrics
- **Game Analysis**: Detailed game breakdowns with player performance and event timelines
- **Goalie Statistics**: Specialized tracking for goalies (GAA, save percentage, wins, shutouts)
- **Mobile-First Design**: Fully responsive interface optimized for mobile devices
- **Secure Access**: Team-based password authentication with coach/player role differentiation

### Target Users
- **Coaches**: Strategic decision making, performance tracking, roster management
- **Players**: Personal development tracking, goal setting, performance insights
- **Parents**: Stay connected with player and team progress

### Data Model
The application uses Google Sheets as the backend with four main data tables:
- **Players**: Player roster with positions and team assignments
- **Games**: Game schedule, results, and basic statistics
- **Events**: Detailed game events (goals, assists, penalties, shots, etc.)
- **GameRoster**: Player attendance and availability tracking