#!/usr/bin/env python3
"""
Debug script to check team names in events data.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def debug_team_names():
    print("=== Debugging Team Names in Events ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get events and check team names
    events = sheets_service.get_events()
    print(f"\nTotal events: {len(events)}")
    
    # Check unique team names in events
    unique_teams = events['Team'].unique()
    print(f"Unique team names in events: {unique_teams}")
    
    # Check goal events specifically
    goal_events = events[events['IsGoal'] == True]
    print(f"\nGoal events: {len(goal_events)}")
    goal_teams = goal_events['Team'].unique()
    print(f"Team names in goal events: {goal_teams}")
    
    # Get teams from teams sheet
    teams = sheets_service.get_teams()
    print(f"\nTeams from Teams sheet:")
    for _, team in teams.iterrows():
        print(f"  TeamID: {team['TeamID']}, TeamName: {team['TeamName']}")
    
    # Check a few sample goal events
    print(f"\nSample goal events:")
    for i, (_, event) in enumerate(goal_events.head(10).iterrows()):
        print(f"  Event {i+1}: GameID={event['GameID']}, Team={event['Team']}, IsGoal={event['IsGoal']}")

if __name__ == "__main__":
    debug_team_names()
