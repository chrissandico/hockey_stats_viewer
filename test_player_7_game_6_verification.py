#!/usr/bin/env python3
"""
Test to verify that player_7 should have 1 regular season game showing (id=6 in the games sheet).
This test uses mock data to simulate the expected state and verify the logic.
"""

import sys
import os
sys.path.append('hockey_stats_webapp')

from services.data_service import DataService
import pandas as pd

class MockSheetsService:
    """Mock sheets service with test data including game id=6 as regular season."""
    
    def __init__(self):
        self.force_refresh = True
        
    def refresh_all_data(self):
        """Mock refresh method - does nothing since we use static data."""
        pass
        
    def get_players(self, force_refresh=False):
        """Return mock players data."""
        return pd.DataFrame([
            {'ID': 'player_7', 'Name': 'Test Player 7', 'JerseyNumber': 7, 'Position': 'F', 'TeamID': 'cwaxersu12aa'},
            {'ID': 'player_1', 'Name': 'Test Player 1', 'JerseyNumber': 1, 'Position': 'G', 'TeamID': 'cwaxersu12aa'},
        ])
        
    def get_games(self, force_refresh=False):
        """Return mock games data with game id=6 as regular season."""
        return pd.DataFrame([
            {'ID': 1, 'Date': '2024-01-10', 'Opponent': 'Team B', 'GameType': 'E', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
            {'ID': 2, 'Date': '2024-02-01', 'Opponent': 'Team C', 'GameType': 'T', 'HomeAway': 'A', 'TeamID': 'cwaxersu12aa'},
            {'ID': 3, 'Date': '2024-02-02', 'Opponent': 'Team D', 'GameType': 'T', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
            {'ID': 4, 'Date': '2024-02-03', 'Opponent': 'Team E', 'GameType': 'T', 'HomeAway': 'A', 'TeamID': 'cwaxersu12aa'},
            {'ID': 5, 'Date': '2024-02-04', 'Opponent': 'Team F', 'GameType': 'T', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
            {'ID': 6, 'Date': '2024-01-15', 'Opponent': 'Team A', 'GameType': 'R', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},  # This is the regular season game
        ])
        
    def get_events(self, force_refresh=False):
        """Return mock events data."""
        return pd.DataFrame([
            {'GameID': 6, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': '', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Goal', 'Period': 1, 'Time': '5:30', 'IsGoal': True, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 6, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': 'player_7', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Assist', 'Period': 2, 'Time': '12:15', 'IsGoal': False, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 1, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': 'player_7', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Assist', 'Period': 1, 'Time': '8:45', 'IsGoal': False, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 2, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': '', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Goal', 'Period': 1, 'Time': '10:00', 'IsGoal': True, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 3, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': '', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Goal', 'Period': 2, 'Time': '15:30', 'IsGoal': True, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 3, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': 'player_7', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Assist', 'Period': 3, 'Time': '18:45', 'IsGoal': False, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 4, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': '', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Goal', 'Period': 1, 'Time': '7:20', 'IsGoal': True, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 4, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': 'player_7', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Assist', 'Period': 2, 'Time': '14:10', 'IsGoal': False, 'IsPowerPlay': False, 'IsShortHanded': False},
            {'GameID': 5, 'PlayerID': 'player_7', 'PrimaryPlayerID': 'player_7', 'AssistPlayer1ID': '', 'AssistPlayer2ID': '', 'YourTeamPlayersOnIce': 'player_7,player_1', 'OpponentPlayersOnIce': 'opp1,opp2', 'Team': 'cwaxersu12aa', 'EventType': 'Goal', 'Period': 3, 'Time': '19:55', 'IsGoal': True, 'IsPowerPlay': False, 'IsShortHanded': False},
        ])
        
    def get_game_roster(self, force_refresh=False):
        """Return mock roster data - player_7 should be Present for game 6."""
        return pd.DataFrame([
            {'GameID': 1, 'PlayerID': 'player_7', 'Status': 'Present'},
            {'GameID': 2, 'PlayerID': 'player_7', 'Status': 'Present'},
            {'GameID': 3, 'PlayerID': 'player_7', 'Status': 'Present'},
            {'GameID': 4, 'PlayerID': 'player_7', 'Status': 'Present'},
            {'GameID': 5, 'PlayerID': 'player_7', 'Status': 'Present'},
            {'GameID': 6, 'PlayerID': 'player_7', 'Status': 'Present'},  # player_7 is Present for game 6
            # Add other players for completeness
            {'GameID': 1, 'PlayerID': 'player_1', 'Status': 'Present'},
            {'GameID': 6, 'PlayerID': 'player_1', 'Status': 'Present'},
        ])
        
    def get_teams(self, force_refresh=False):
        """Return mock teams data."""
        return pd.DataFrame([
            {'TeamID': 'cwaxersu12aa', 'TeamName': 'Test Team', 'Password': 'cwaxersu12aa'}
        ])
        
    def get_sheet_data(self, sheet_name):
        """Return mock data for different sheets."""
        
        if sheet_name == 'Games':
            # Mock games data with game id=6 as regular season
            return pd.DataFrame([
                {'ID': 1, 'Date': '2024-01-10', 'Opponent': 'Team B', 'GameType': 'E', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
                {'ID': 2, 'Date': '2024-02-01', 'Opponent': 'Team C', 'GameType': 'T', 'HomeAway': 'A', 'TeamID': 'cwaxersu12aa'},
                {'ID': 3, 'Date': '2024-02-02', 'Opponent': 'Team D', 'GameType': 'T', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
                {'ID': 4, 'Date': '2024-02-03', 'Opponent': 'Team E', 'GameType': 'T', 'HomeAway': 'A', 'TeamID': 'cwaxersu12aa'},
                {'ID': 5, 'Date': '2024-02-04', 'Opponent': 'Team F', 'GameType': 'T', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},
                {'ID': 6, 'Date': '2024-01-15', 'Opponent': 'Team A', 'GameType': 'R', 'HomeAway': 'H', 'TeamID': 'cwaxersu12aa'},  # This is the regular season game
            ])
            
        elif sheet_name == 'GameRoster':
            # Mock roster data - player_7 should be Present for game 6
            return pd.DataFrame([
                {'GameID': 1, 'PlayerID': 'player_7', 'Status': 'Present'},
                {'GameID': 2, 'PlayerID': 'player_7', 'Status': 'Present'},
                {'GameID': 3, 'PlayerID': 'player_7', 'Status': 'Present'},
                {'GameID': 4, 'PlayerID': 'player_7', 'Status': 'Present'},
                {'GameID': 5, 'PlayerID': 'player_7', 'Status': 'Present'},
                {'GameID': 6, 'PlayerID': 'player_7', 'Status': 'Present'},  # player_7 is Present for game 6
                # Add other players for completeness
                {'GameID': 1, 'PlayerID': 'player_1', 'Status': 'Present'},
                {'GameID': 6, 'PlayerID': 'player_1', 'Status': 'Present'},
            ])
            
        elif sheet_name == 'Players':
            return pd.DataFrame([
                {'ID': 'player_7', 'Name': 'Test Player 7', 'JerseyNumber': 7, 'Position': 'F', 'TeamID': 'cwaxersu12aa'},
                {'ID': 'player_1', 'Name': 'Test Player 1', 'JerseyNumber': 1, 'Position': 'G', 'TeamID': 'cwaxersu12aa'},
            ])
            
        elif sheet_name == 'GameStats':
            # Mock game stats for player_7 in game 6
            return pd.DataFrame([
                {'GameID': 6, 'PlayerID': 'player_7', 'Goals': 1, 'Assists': 1, 'PlusMinus': 1, 'PIM': 0, 'SOG': 3},
                {'GameID': 1, 'PlayerID': 'player_7', 'Goals': 0, 'Assists': 1, 'PlusMinus': -2, 'PIM': 0, 'SOG': 2},
                {'GameID': 2, 'PlayerID': 'player_7', 'Goals': 1, 'Assists': 0, 'PlusMinus': 1, 'PIM': 2, 'SOG': 4},
                {'GameID': 3, 'PlayerID': 'player_7', 'Goals': 1, 'Assists': 1, 'PlusMinus': 1, 'PIM': 0, 'SOG': 2},
                {'GameID': 4, 'PlayerID': 'player_7', 'Goals': 1, 'Assists': 1, 'PlusMinus': 1, 'PIM': 0, 'SOG': 3},
                {'GameID': 5, 'PlayerID': 'player_7', 'Goals': 1, 'Assists': 0, 'PlusMinus': 1, 'PIM': 0, 'SOG': 1},
            ])
            
        elif sheet_name == 'Teams':
            return pd.DataFrame([
                {'ID': 'cwaxersu12aa', 'Name': 'Test Team', 'Password': 'cwaxersu12aa'}
            ])
            
        else:
            return pd.DataFrame()

def test_player_7_game_6_verification():
    """Test that player_7 has 1 regular season game showing (game id=6)."""
    
    print("=== PLAYER_7 GAME ID=6 VERIFICATION TEST ===")
    
    # Initialize with mock data
    mock_sheets = MockSheetsService()
    data_service = DataService(mock_sheets, force_refresh=True)
    
    team_id = 'cwaxersu12aa'
    player_id = 'player_7'
    
    print(f"\nTesting player {player_id} for team {team_id}")
    
    # Step 1: Verify game 6 exists and is regular season
    print("\n1. VERIFYING GAME 6 DATA")
    all_games = data_service.get_games(team_id)
    game_6 = all_games[all_games['ID'] == 6]
    
    if game_6.empty:
        print("❌ ERROR: Game 6 not found in games data")
        return False
    
    game_6_data = game_6.iloc[0]
    print(f"Game 6 found:")
    print(f"  ID: {game_6_data['ID']}")
    print(f"  Date: {game_6_data['Date']}")
    print(f"  Opponent: {game_6_data['Opponent']}")
    print(f"  GameType: {game_6_data['GameType']}")
    print(f"  HomeAway: {game_6_data['HomeAway']}")
    
    if game_6_data['GameType'] != 'R':
        print(f"❌ ERROR: Game 6 is not Regular Season. GameType = {game_6_data['GameType']}")
        return False
    
    print("✓ Game 6 is correctly marked as Regular Season")
    
    # Step 2: Verify player_7 is in roster for game 6
    print("\n2. VERIFYING PLAYER_7 ROSTER FOR GAME 6")
    game_roster = data_service.get_game_roster()
    player_7_game_6_roster = game_roster[
        (game_roster['GameID'] == 6) & 
        (game_roster['PlayerID'] == player_id)
    ]
    
    if player_7_game_6_roster.empty:
        print("❌ ERROR: player_7 not found in roster for game 6")
        return False
    
    roster_entry = player_7_game_6_roster.iloc[0]
    print(f"player_7 roster entry for game 6:")
    print(f"  GameID: {roster_entry['GameID']}")
    print(f"  PlayerID: {roster_entry['PlayerID']}")
    print(f"  Status: {roster_entry['Status']}")
    
    if roster_entry['Status'] != 'Present':
        print(f"❌ ERROR: player_7 is not marked as Present for game 6. Status = {roster_entry['Status']}")
        return False
    
    print("✓ player_7 is correctly marked as Present for game 6")
    
    # Step 3: Test regular season filtering
    print("\n3. TESTING REGULAR SEASON FILTERING")
    
    # Get regular season games only
    regular_games = data_service.get_games(team_id, game_type='R')
    print(f"Regular season games found: {len(regular_games)}")
    
    if len(regular_games) != 1:
        print(f"❌ ERROR: Expected 1 regular season game, found {len(regular_games)}")
        return False
    
    regular_game = regular_games.iloc[0]
    if regular_game['ID'] != 6:
        print(f"❌ ERROR: Regular season game ID is {regular_game['ID']}, expected 6")
        return False
    
    print("✓ Regular season filtering correctly returns only game 6")
    
    # Step 4: Test player games filtering
    print("\n4. TESTING PLAYER GAMES FILTERING")
    
    # Get player games for regular season only
    player_regular_games = data_service.get_player_games(player_id, team_id, game_type='R')
    print(f"player_7 regular season games: {len(player_regular_games)}")
    
    if len(player_regular_games) != 1:
        print(f"❌ ERROR: Expected 1 regular season game for player_7, found {len(player_regular_games)}")
        return False
    
    player_regular_game = player_regular_games.iloc[0]
    if player_regular_game['ID'] != 6:
        print(f"❌ ERROR: player_7 regular season game ID is {player_regular_game['ID']}, expected 6")
        return False
    
    print("✓ Player games filtering correctly returns only game 6 for player_7")
    
    # Step 5: Test player stats calculation
    print("\n5. TESTING PLAYER STATS CALCULATION")
    
    # Calculate player stats for regular season only
    player_regular_stats = data_service.calculate_player_stats(player_id, team_id, game_type='R')
    
    if not player_regular_stats:
        print("❌ ERROR: No regular season stats calculated for player_7")
        return False
    
    print(f"player_7 regular season stats:")
    print(f"  Games Played: {player_regular_stats['games_played']}")
    print(f"  Goals: {player_regular_stats['goals']}")
    print(f"  Assists: {player_regular_stats['assists']}")
    print(f"  Points: {player_regular_stats['points']}")
    print(f"  Plus/Minus: {player_regular_stats['plus_minus']}")
    
    if player_regular_stats['games_played'] != 1:
        print(f"❌ ERROR: Expected 1 game played, got {player_regular_stats['games_played']}")
        return False
    
    # Verify stats match game 6 data (1 goal, 1 assist from mock data)
    if player_regular_stats['goals'] != 1:
        print(f"❌ ERROR: Expected 1 goal, got {player_regular_stats['goals']}")
        return False
    
    if player_regular_stats['assists'] != 1:
        print(f"❌ ERROR: Expected 1 assist, got {player_regular_stats['assists']}")
        return False
    
    if player_regular_stats['points'] != 2:
        print(f"❌ ERROR: Expected 2 points, got {player_regular_stats['points']}")
        return False
    
    print("✓ Player stats calculation correctly shows 1 regular season game with proper stats")
    
    # Step 6: Test game log generation
    print("\n6. TESTING GAME LOG GENERATION")
    
    # Get game log for regular season only
    player_game_log = data_service.get_player_game_log(player_id, team_id, game_type='R')
    
    if len(player_game_log) != 1:
        print(f"❌ ERROR: Expected 1 game log entry, got {len(player_game_log)}")
        return False
    
    game_log_entry = player_game_log[0]
    print(f"player_7 regular season game log entry:")
    print(f"  Game ID: {game_log_entry['game']['ID']}")
    print(f"  Date: {game_log_entry['game']['Date']}")
    print(f"  Opponent: {game_log_entry['game']['Opponent']}")
    
    # Check if stats are available in the expected format
    if 'stats' in game_log_entry:
        print(f"  Goals: {game_log_entry['stats']['goals']}")
        print(f"  Assists: {game_log_entry['stats']['assists']}")
        print(f"  Points: {game_log_entry['stats']['points']}")
    else:
        # Stats might be directly in the entry or in a different format
        print(f"  Goals: {game_log_entry.get('goals', 'N/A')}")
        print(f"  Assists: {game_log_entry.get('assists', 'N/A')}")
        print(f"  Points: {game_log_entry.get('points', 'N/A')}")
    
    if game_log_entry['game']['ID'] != 6:
        print(f"❌ ERROR: Game log entry ID is {game_log_entry['game']['ID']}, expected 6")
        return False
    
    print("✓ Game log generation correctly shows 1 regular season game (game 6)")
    
    print("\n=== ALL TESTS PASSED ===")
    print("✅ player_7 correctly has 1 regular season game showing (id=6)")
    print("✅ Game 6 is properly marked as Regular Season")
    print("✅ player_7 is properly marked as Present for game 6")
    print("✅ Regular season filtering works correctly")
    print("✅ Player stats and game log show the correct data")
    
    return True

def test_current_issue_diagnosis():
    """Diagnose what might be wrong in the current system."""
    
    print("\n=== CURRENT ISSUE DIAGNOSIS ===")
    
    print("\nPossible issues that could prevent player_7 from showing 1 regular season game:")
    
    print("\n1. GAME DATA ISSUES:")
    print("   - Game 6 might not exist in the Games sheet")
    print("   - Game 6 might not be marked as GameType='R' (Regular Season)")
    print("   - Game 6 might be assigned to wrong TeamID")
    print("   - Game 6 might have a future date (filtered out)")
    
    print("\n2. ROSTER DATA ISSUES:")
    print("   - player_7 might not be in GameRoster for game 6")
    print("   - player_7 might be marked as 'Absent' or other status for game 6")
    print("   - GameRoster entry might have wrong GameID or PlayerID")
    
    print("\n3. FILTERING LOGIC ISSUES:")
    print("   - Game type filtering might not be working correctly")
    print("   - Date filtering might be excluding the game")
    print("   - Player games filtering might have bugs")
    
    print("\n4. DATA SERVICE ISSUES:")
    print("   - calculate_player_stats might have bugs")
    print("   - get_player_game_log might have bugs")
    print("   - Sheet data caching might be stale")
    
    print("\nTO FIX THE ISSUE:")
    print("1. Verify game 6 exists and has GameType='R'")
    print("2. Verify player_7 has Status='Present' for GameID=6 in GameRoster")
    print("3. Test the filtering logic with known good data")
    print("4. Check for any date-related filtering issues")
    
    return True

if __name__ == "__main__":
    try:
        # Run the verification test with mock data
        success1 = test_player_7_game_6_verification()
        
        # Run the diagnosis
        success2 = test_current_issue_diagnosis()
        
        if success1 and success2:
            print("\n🎉 VERIFICATION TEST PASSED WITH MOCK DATA! 🎉")
            print("\nThe logic is working correctly. If player_7 is not showing")
            print("1 regular season game in the actual webapp, the issue is likely")
            print("in the Google Sheets data itself, not the filtering logic.")
            print("\nNext steps:")
            print("1. Check that game 6 exists in Games sheet with GameType='R'")
            print("2. Check that player_7 has Status='Present' for GameID=6 in GameRoster")
        else:
            print("\n❌ SOME TESTS FAILED")
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
