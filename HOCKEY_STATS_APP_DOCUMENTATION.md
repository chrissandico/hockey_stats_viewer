Hockey Stats Web Application
Overview
The Hockey Stats Web Application is a modern, responsive web platform designed for tracking and displaying youth hockey statistics. It provides a comprehensive solution for coaches, players, and parents to monitor individual player performance, team statistics, and game-by-game analysis.

Built with Dash and integrated with Google Sheets for data storage, this application offers a secure, password-protected environment for accessing team statistics. The application features a responsive design that works seamlessly across desktop and mobile devices, ensuring that users can access statistics from anywhere.

System Architecture
Technology Stack
Frontend Framework: Dash

Data Storage: Google Sheets

Authentication: Custom password-based authentication

Styling: Custom CSS with responsive design

Mobile Optimization: JavaScript enhancements for mobile devices

Data Flow
Data Source: All statistics are stored in Google Sheets

Backend Processing: Python functions process and analyze the raw data

Frontend Display: Dash components and callbacks render the processed data in user-friendly views

User Authentication: Password-based system controls access to the application

Google Sheets Integration
The application connects to Google Sheets using the gspread library and Google OAuth2 authentication. The connection is established through a service account with appropriate permissions. The application caches data for performance optimization with a time-to-live (TTL) of 3600 seconds (1 hour).

Core Features
Authentication System
The application implements a team-based password authentication system:

Single Password Access: All team members use the same password

Secure Storage: Passwords are hashed using SHA-256 before storage

Session Management: Authentication state is maintained throughout the user session

Logout Functionality: Users can explicitly log out when finished

Player Statistics
The Player Statistics view provides detailed performance metrics for individual players:

Player Selection: Users can select players by jersey number

Game-Specific Stats: Detailed statistics for each game a player participated in

Season Totals: Aggregated statistics across all games

Game Log: Chronological listing of performance across games

Key metrics tracked for players include:

Goals

Assists

Points

Plus/Minus rating

Shots

Penalty minutes

Games played

Goals per game

Team Statistics & Leaderboards
The Team Statistics view provides team performance metrics and player rankings:

Season Summary: Overall team record, points, goals for/against, and win percentage

Position-Based Leaderboards: Separate leaderboards for forwards, defensemen, and goalies

Multiple Ranking Categories: Top players in goals, assists, points, and plus/minus

Goalie Statistics: Specialized statistics for goalies including GAA, save percentage, wins, and shutouts

Game Log: Chronological listing of all team games with results

Game Statistics
The Game Statistics view provides detailed information about specific games:

Game Selection: Users can select individual games to analyze

Game Summary: Score, result, shots, penalty minutes, and power play statistics

Player Performance: Detailed breakdown of each player's performance in the selected game

Position Filtering: Ability to filter player performance by position

Game Timeline: Chronological sequence of game events including goals, penalties, shots, and other key moments

Mobile Responsiveness
The application is fully optimized for mobile devices:

Responsive Layout: Adapts to different screen sizes

Touch-Friendly Controls: Larger buttons and controls for mobile users

Collapsible Sections: Expandable/collapsible content sections to manage screen space

Cross-Platform Compatibility: Optimized to work seamlessly across all major browsers and operating systems (Android, iOS, macOS, Windows)

Horizontal Scrolling: Optimized tables and stats displays for smaller screens

Data Model
The application uses a structured data model stored in Google Sheets:

Players Data
ID: Unique Player ID

JerseyNumber: Player's jersey number

FirstName: Player's first name

LastName: Player's last name

TeamID: Team identifier

Position: Player position (F for Forward, D for Defense, G for Goalie)

Games Data
ID: Unique Game ID

Date: Game date

Opponent: Name of opposing team

Location: Game venue

Result: Game outcome (W for Win, L for Loss, T for Tie)

GoalsFor: Goals scored by the team

GoalsAgainst: Goals scored by the opponent

Events Data
GameID: Reference to the Game ID

EventType: Type of event (Goal, Shot, Penalty, Hit, Faceoff)

Period: Game period when the event occurred

Time: Time within the period

PrimaryPlayerID: ID of the primary player involved

AssistPlayer1ID: ID of the first assist player (for goals)

AssistPlayer2ID: ID of the second assist player (for goals)

Team: Which team performed the event

IsGoal: Boolean indicating if the event was a goal

IsPowerPlay: Boolean indicating if the goal was on power play

IsShortHanded: Boolean indicating if the goal was short-handed

PenaltyType: Type of penalty (if applicable)

PenaltyDuration: Duration of penalty in minutes

YourTeamPlayersOnIce: List of player IDs on ice during the event

Game Roster Data
GameID: Reference to the Game ID

PlayerID: Reference to the Player ID

Status: Player's status for the game (Present or Absent)

User Interface
Navigation
The application features a simple, intuitive navigation system:

Top Navigation Bar: Buttons for switching between main views

Logout Button: Positioned at the top right for easy access

Dropdown Selectors: For choosing players and games

Collapsible Sections: For organizing content on mobile devices

Design Elements
Color Scheme: Blue and white theme inspired by the Toronto Maple Leafs

Card-Based Layout: Information presented in clean, separated card components

Responsive Tables: Data tables that adapt to different screen sizes

Visual Indicators: Color coding for wins, losses, and ties

Mobile Optimizations
Collapsible Sections: Expandable/collapsible content to manage screen space

Touch-Friendly Controls: Larger tap targets for mobile users

Horizontal Scrolling: For tables and data displays that exceed screen width

Optimized Layout: Adjusted spacing and sizing for mobile screens

Mobile-First Design Principles
For an optimal experience on mobile devices, the application's design adheres to the following principles:

Focus on Essential Information: Key stats and summaries are presented first to ensure users can quickly find the most important information on a small screen.

Simple Visualizations: Data is displayed using clear, easy-to-read charts and tables that are optimized for mobile viewports, avoiding complex visualizations that are difficult to interpret on a phone.

Clear Visual Hierarchy: The use of bold headers, contrasting colors, and card-based layouts creates a clear visual hierarchy, guiding the user's eye to the most relevant data.

Touch-Friendly Controls: Buttons and interactive elements are generously sized with sufficient spacing to ensure they are easy to tap accurately with a finger.

Efficient Content Organization: Collapsible sections are used to organize large amounts of information, allowing users to expand only the content they want to see, which saves screen space and reduces visual clutter.

Security Features
Password Authentication
Hashed Storage: Passwords are never stored in plain text

SHA-256 Algorithm: Industry-standard hashing algorithm

Secure Configuration: Password hash stored in a secure config file or environment variable

Session Management: Authentication state maintained throughout user session

Data Protection
Google OAuth2: Secure connection to Google Sheets

Service Account: Limited permission access to data

No Client-Side Storage: Sensitive data not stored in browser

Setup and Configuration
Requirements
Python 3.7+

Dash

gspread

pandas

Google Cloud service account

Configuration Steps
Install Dependencies:

pip install -r requirements.txt

Google Sheets Setup:

Create a Google Cloud project

Enable Google Sheets API

Create a service account

Share your Google Sheet with the service account email

Authentication Setup:

Generate a password hash using the provided script

Store the hash in a secure config file or as an environment variable

Running the Application:

python app.py

Customization Options
Visual Customization
The application's appearance can be customized by modifying the CSS in hockey_stats/static/css/style.css. Key customizable elements include:

Color scheme

Card styling

Table appearance

Font styles

Mobile breakpoints

Data Structure Customization
The application can be adapted to different data structures by modifying the data processing functions in hockey_stats/sheets_service.py. This allows for flexibility in how statistics are stored and calculated.

Future Enhancement Possibilities
Potential Improvements
Advanced Analytics: Shot maps, heat maps, and advanced statistical analysis

Video Integration: Linking game events to video clips

Multi-Season Support: Tracking statistics across multiple seasons

Opponent Analysis: Detailed statistics about performance against specific opponents

Practice Tracking: Integration of practice attendance and performance metrics

User-Specific Views: Customized views for coaches, players, and parents

Expansion Possibilities
Multi-Team Support: Expanding to support multiple teams within the same organization

League Integration: Connecting with league-wide statistics

Tournament Mode: Special views for tournament play

Social Features: Sharing capabilities for achievements and milestones

Notification System: Alerts for new games, updated statistics, or team announcements

Conclusion
The Hockey Stats Web Application provides a comprehensive solution for tracking and analyzing youth hockey statistics. With its responsive design, secure authentication, and detailed statistical views, it offers valuable insights for coaches, players, and parents. The application's integration with Google Sheets ensures easy data management, while its customizable nature allows for adaptation to specific team needs.