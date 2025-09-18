#!/usr/bin/env python3
"""
Deep dive analysis of plus/minus calculation for any jersey number.
This script shows the detailed step-by-step calculation process.

Usage:
    python analyze_player_plus_minus.py [jersey_number]
    
Examples:
    python analyze_player_plus_minus.py 84
    python analyze_player_plus_minus.py 25
    python analyze_player_plus_minus.py     # defaults to 84
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.sheets_service import SheetsService
from services.data_service import DataService

def analyze_player_plus_minus(jersey_number=84):
    """Analyze plus/minus calculation for any jersey number in detail."""
    print(f"=== DEEP DIVE: PLUS/MINUS CALCULATION FOR JERSEY #{jersey_number} ===")
    
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Find player with specified jersey number
    print(f"\n1. FINDING PLAYER WITH JERSEY #{jersey_number}")
    print("-" * 50)
    
    players = data_service.get_players()
    target_player = players[players['JerseyNumber'] == jersey_number]
    
    if target_player.empty:
        print(f"❌ No player found with jersey number {jersey_number}")
        
        # Show all available jersey numbers for reference
        print("\nAvailable jersey numbers:")
        jersey_numbers = sorted(players['JerseyNumber'].unique())
        for i, jersey in enumerate(jersey_numbers):
            if i % 10 == 0 and i > 0:
                print()  # New line every 10 numbers
            print(f"{jersey:3d}", end=" ")
        print("\n")
        return
    
    target_player = target_player.iloc[0]
    player_id = target_player['ID']
    
    print(f"✅ Found player: #{target_player['JerseyNumber']} (ID: {player_id})")
    print(f"   Position: {target_player['Position']}")
    
    # Get team information
    print("\n2. TEAM IDENTIFICATION")
    print("-" * 50)
    
    teams = sheets_service.get_teams()
    if not teams.empty:
        team_id = teams.iloc[0]['TeamID']
        team_name = teams.iloc[0]['TeamName']
        print(f"Team ID: {team_id}")
        print(f"Team Name: {team_name}")
    else:
        team_id = 'your_team'
        team_name = 'Unknown Team'
        print(f"Using fallback team ID: {team_id}")
    
    # Get team identifier for events
    team_identifier = data_service._get_team_identifier_for_events(team_id)
    print(f"Team identifier in events: {team_identifier}")
    
    # Get all events and filter for goals where player was on ice
    print(f"\n3. RETRIEVING GOAL EVENTS WHERE PLAYER #{jersey_number} WAS ON ICE")
    print("-" * 50)
    
    events = data_service.get_events()
    print(f"Total events in database: {len(events)}")
    
    # Helper function to check if player is on ice (same as in data_service.py)
    def is_player_on_ice(players_str, pid):
        if not players_str or pd.isna(players_str):
            return False
        if isinstance(players_str, str):
            try:
                players_list = players_str.strip('[]').replace(' ', '').split(',')
                return pid in players_list
            except:
                return pid in players_str
        return False
    
    # Import pandas for the helper function
    import pandas as pd
    
    # Filter to only goal events where target player was on ice
    goal_events_with_player = events[
        (events['IsGoal'] == True) & 
        (events['YourTeamPlayersOnIce'].apply(lambda x: is_player_on_ice(x, player_id)))
    ]
    
    print(f"Goal events where player #{target_player['JerseyNumber']} was on ice: {len(goal_events_with_player)}")
    
    if goal_events_with_player.empty:
        print(f"❌ No goal events found where player #{jersey_number} was on ice")
        
        # Check if player appears in any events at all
        all_player_events = events[events['PrimaryPlayerID'] == player_id]
        print(f"Total events involving player #{jersey_number}: {len(all_player_events)}")
        
        # Check if YourTeamPlayersOnIce field has any data
        non_empty_on_ice = events[events['YourTeamPlayersOnIce'].notna() & (events['YourTeamPlayersOnIce'] != '')]
        print(f"Events with YourTeamPlayersOnIce data: {len(non_empty_on_ice)}")
        
        if not non_empty_on_ice.empty:
            print("Sample YourTeamPlayersOnIce values:")
            for i, sample in enumerate(non_empty_on_ice['YourTeamPlayersOnIce'].head(3)):
                print(f"  {i+1}. {sample}")
        
        return
    
    # Analyze each goal event in detail
    print("\n4. DETAILED PLUS/MINUS CALCULATION")
    print("-" * 50)
    print("📊 STEP-BY-STEP CALCULATION:")
    
    plus_minus_total = 0
    
    for i, (_, goal_event) in enumerate(goal_events_with_player.iterrows(), 1):
        print(f"\n🏒 Goal Event #{i}:")
        print(f"  Game ID: {goal_event['GameID']}")
        print(f"  Period: {goal_event.get('Period', 'Unknown')}")
        print(f"  Time: {goal_event.get('Time', 'Unknown')}")
        print(f"  Scoring Team: {goal_event['Team']}")
        print(f"  Goal Situation: {goal_event.get('GoalSituation', 'Not specified')}")
        print(f"  Is Power Play: {goal_event.get('IsPowerPlay', 'Not specified')}")
        print(f"  Is Short Handed: {goal_event.get('IsShortHanded', 'Not specified')}")
        print(f"  Is Penalty Shot: {goal_event.get('IsPenaltyShot', 'Not specified')}")
        print(f"  Players on ice: {goal_event.get('YourTeamPlayersOnIce', 'Not specified')}")
        
        # Apply the decision tree logic
        print(f"\n  🔍 Decision Tree Analysis:")
        
        # Check for penalty shot goals first
        if goal_event.get('IsPenaltyShot', False):
            print(f"    ➤ RULE: Penalty Shot Goal → No +/- awarded")
            plus_minus_change = 0
        else:
            scoring_team = goal_event['Team']
            goal_situation = goal_event.get('GoalSituation', '')
            
            # Apply decision tree
            if 'Power Play' in goal_situation or goal_event.get('IsPowerPlay', False):
                print(f"    ➤ RULE 1: Power Play Goal → No +/- awarded")
                plus_minus_change = 0
            elif 'Even Strength' in goal_situation or goal_situation == '':
                if scoring_team == team_identifier:
                    print(f"    ➤ RULE 2: Even Strength Goal FOR team ({scoring_team}) → Player gets +1")
                    plus_minus_change = +1
                else:
                    print(f"    ➤ RULE 2: Even Strength Goal AGAINST team (by {scoring_team}) → Player gets -1")
                    plus_minus_change = -1
            elif 'Short Handed' in goal_situation or goal_event.get('IsShortHanded', False):
                if scoring_team == team_identifier:
                    print(f"    ➤ RULE 3: Short-Handed Goal FOR team → Player gets +1")
                    plus_minus_change = +1
                else:
                    print(f"    ➤ RULE 3: Short-Handed Goal AGAINST team → Player gets -1")
                    plus_minus_change = -1
            else:
                # Default case
                if scoring_team == team_identifier:
                    print(f"    ➤ DEFAULT: Unknown situation, treating as even strength FOR team → Player gets +1")
                    plus_minus_change = +1
                else:
                    print(f"    ➤ DEFAULT: Unknown situation, treating as even strength AGAINST team → Player gets -1")
                    plus_minus_change = -1
        
        # Update running total
        previous_total = plus_minus_total
        plus_minus_total += plus_minus_change
        
        print(f"  📈 Plus/Minus Change: {plus_minus_change:+d}")
        print(f"  📊 Previous Total: {previous_total:+d}")
        print(f"  🎯 NEW RUNNING TOTAL: {plus_minus_total:+d}")
        print(f"  {'='*40}")
    
    # Final calculation summary
    print("\n5. FINAL CALCULATION SUMMARY")
    print("-" * 50)
    print(f"Player: #{target_player['JerseyNumber']} ({target_player['Position']})")
    print(f"Total goal events analyzed: {len(goal_events_with_player)}")
    print(f"Final Plus/Minus: {plus_minus_total:+d}")
    
    # Verify with the actual calculation from data service
    print("\n6. VERIFICATION WITH DATA SERVICE")
    print("-" * 50)
    
    # Get season stats
    season_stats = data_service.calculate_player_stats(player_id, team_id)
    if season_stats:
        calculated_plus_minus = season_stats['plus_minus']
        print(f"Data Service Season Plus/Minus: {calculated_plus_minus:+d}")
        
        if calculated_plus_minus == plus_minus_total:
            print("✅ VERIFICATION PASSED: Manual calculation matches data service")
        else:
            print("❌ VERIFICATION FAILED: Manual calculation does not match data service")
            print(f"   Manual: {plus_minus_total:+d}")
            print(f"   Data Service: {calculated_plus_minus:+d}")
    else:
        print("❌ Could not retrieve season stats from data service")
    
    # Show game-by-game breakdown
    print("\n7. GAME-BY-GAME BREAKDOWN")
    print("-" * 50)
    
    games = data_service.get_player_games(player_id, team_id)
    print(f"Games played: {len(games)}")
    
    for _, game in games.iterrows():
        game_stats = data_service.calculate_player_game_stats(player_id, game['ID'])
        if game_stats:
            game_plus_minus = game_stats['plus_minus']
            print(f"  Game {game['ID']} ({game['Date']} vs {game['Opponent']}): {game_plus_minus:+d}")
    
    print("\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    # Parse command line arguments
    jersey_number = 84  # Default
    
    if len(sys.argv) > 1:
        try:
            jersey_number = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid jersey number")
            print("Usage: python analyze_player_plus_minus.py [jersey_number]")
            print("Example: python analyze_player_plus_minus.py 25")
            sys.exit(1)
    
    analyze_player_plus_minus(jersey_number)
