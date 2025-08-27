# Hockey Stats Web Application

A modern, responsive web application for tracking and displaying youth hockey statistics. Built with Dash and integrated with Google Sheets for data storage.

## Overview

The Hockey Stats Web Application provides a comprehensive solution for coaches, players, and parents to monitor individual player performance, team statistics, and game-by-game analysis. It features a secure, password-protected environment for accessing team statistics with a responsive design that works seamlessly across desktop and mobile devices.

## Features

- **Player Statistics**: View detailed performance metrics for individual players, including game-specific stats and season totals.
- **Team Statistics**: Access team performance metrics, position-based leaderboards, and player rankings.
- **Game Statistics**: Analyze specific games with detailed breakdowns of player performance and game events.
- **Mobile Responsive**: Fully optimized for mobile devices with touch-friendly controls and collapsible sections.
- **Secure Access**: Team-based password authentication system.
- **Google Sheets Integration**: Data stored in Google Sheets for easy management and updates.

## Installation

### Prerequisites

- Python 3.7+
- Google Cloud project with Google Sheets API enabled
- Google service account with access to your Google Sheet

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd hockey_stats_webapp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Place your Google service account credentials file in the project directory as `credentials.json`.

4. Configure your Google Sheet ID in `services/sheets_service.py` if different from the default.

5. (Optional) Set environment variables:
   ```
   # For custom password
   export HOCKEY_STATS_PASSWORD=your_password
   
   # For custom secret key
   export SECRET_KEY=your_secret_key
   ```

## Running the Application

Start the application with:

```
python app.py
```

The application will be available at `http://localhost:8050`.

## Google Sheets Structure

The application expects your Google Sheet to have the following tabs:

1. **Players**: Contains player information
   - ID: Unique Player ID
   - JerseyNumber: Player's jersey number
   - FirstName: Player's first name
   - LastName: Player's last name
   - TeamID: Team identifier
   - Position: Player position (F for Forward, D for Defense, G for Goalie)

2. **Games**: Contains game information
   - ID: Unique Game ID
   - Date: Game date
   - Opponent: Name of opposing team
   - Location: Game venue
   - Result: Game outcome (W for Win, L for Loss, T for Tie)
   - GoalsFor: Goals scored by the team
   - GoalsAgainst: Goals scored by the opponent

3. **Events**: Contains game events
   - GameID: Reference to the Game ID
   - EventType: Type of event (Goal, Shot, Penalty, Hit, Faceoff)
   - Period: Game period when the event occurred
   - Time: Time within the period
   - PrimaryPlayerID: ID of the primary player involved
   - AssistPlayer1ID: ID of the first assist player (for goals)
   - AssistPlayer2ID: ID of the second assist player (for goals)
   - Team: Which team performed the event
   - IsGoal: Boolean indicating if the event was a goal
   - IsPowerPlay: Boolean indicating if the goal was on power play
   - IsShortHanded: Boolean indicating if the goal was short-handed
   - PenaltyType: Type of penalty (if applicable)
   - PenaltyDuration: Duration of penalty in minutes
   - YourTeamPlayersOnIce: List of player IDs on ice during the event

4. **GameRoster**: Contains player attendance for each game
   - GameID: Reference to the Game ID
   - PlayerID: Reference to the Player ID
   - Status: Player's status for the game (Present or Absent)

## Authentication

The application uses a simple password-based authentication system. The default password is "waxersu12aa", but you can change it by setting the `HOCKEY_STATS_PASSWORD` environment variable.

## Mobile Optimizations

The application includes several optimizations for mobile devices:

- Responsive layout that adapts to different screen sizes
- Touch-friendly controls with larger buttons
- Collapsible sections to manage screen space
- Horizontal scrolling for tables and stats displays

## Customization

### Visual Customization

The application's appearance can be customized by modifying the CSS in `assets/css/style.css`. Key customizable elements include:

- Color scheme
- Card styling
- Table appearance
- Font styles
- Mobile breakpoints

### Data Structure Customization

The application can be adapted to different data structures by modifying the data processing functions in `services/data_service.py`.

## Deployment

The application can be deployed to various platforms. Here are instructions for some recommended options:

### Render.com (Recommended for Free Tier)

1. Fork or clone this repository to your GitHub account
2. Sign up for a [Render.com](https://render.com/) account
3. Create a new Web Service and connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Set the following environment variables in the Render dashboard:
   - `GOOGLE_CREDENTIALS`: The entire contents of your `credentials.json` file as a JSON string
   - `GOOGLE_SHEET_ID`: Your Google Sheet ID (if different from the default)
   - `HOCKEY_STATS_PASSWORD`: Custom password for accessing the app
   - `SECRET_KEY`: A secure random string for Flask sessions

### Heroku

1. Create a [Heroku](https://www.heroku.com/) account
2. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. Login to Heroku: `heroku login`
4. Create a new app: `heroku create your-app-name`
5. Push to Heroku: `git push heroku main`
6. Set environment variables:
   ```
   heroku config:set GOOGLE_CREDENTIALS='{"type":"service_account",...}'
   heroku config:set GOOGLE_SHEET_ID=your_sheet_id
   heroku config:set HOCKEY_STATS_PASSWORD=your_password
   heroku config:set SECRET_KEY=your_secret_key
   ```

### Railway.app

1. Create a [Railway.app](https://railway.app/) account
2. Connect your GitHub repository
3. Railway will automatically detect the `Procfile`
4. Set the required environment variables in the Railway dashboard

## License

[MIT License](LICENSE)
