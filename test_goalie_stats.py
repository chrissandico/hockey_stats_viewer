from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService

def main():
    print("Initializing services...")
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    print("\n=== CHECKING PLAYERS DATA ===")
    # Get players and filter goalies
    players = data_service.get_players()
    print(f"Total players: {len(players)}")
    goalies = players[players['Position'] == 'G']
    print(f"Goalies found: {len(goalies)}")
    
    if goalies.empty:
        print("ERROR: No goalies found in player data!")
        return
    
    # Get the first goalie
    goalie = goalies.iloc[0]
    goalie_id = goalie['ID']
    print(f"Using goalie: ID={goalie_id}, Jersey={goalie.get('JerseyNumber', 'Unknown')}")
    
    print("\n=== CHECKING GAME ROSTER ===")
    # Get game roster data
    game_roster = data_service.get_game_roster()
    
    # Check if goalie is in game roster
    goalie_roster = game_roster[game_roster['PlayerID'] == goalie_id]
    print(f"Goalie roster entries: {len(goalie_roster)}")
    
    print("\n=== CHECKING GOALIE GAMES ===")
    # Get games for the goalie
    goalie_games = data_service.get_player_games(goalie_id)
    print(f"Goalie games count: {len(goalie_games)}")
    
    if not goalie_games.empty:
        print("Sample game data:")
        print(goalie_games.iloc[0].to_dict())
    else:
        print("WARNING: No games found for goalie!")
    
    print("\n=== CALCULATING GOALIE STATS ===")
    # Calculate goalie stats
    goalie_stats = data_service.calculate_goalie_stats(goalie_id)
    
    if goalie_stats:
        print("\n=== GOALIE STATISTICS ===")
        print(f"Games Played: {goalie_stats['games_played']}")
        print(f"Wins: {goalie_stats['wins']}")
        print(f"Shutouts: {goalie_stats['shutouts']}")
        print(f"Goals Against: {goalie_stats['goals_against']}")
        print(f"Shots Against: {goalie_stats['shots_against']}")
        print(f"Saves: {goalie_stats['saves']}")
        print(f"Save Percentage: {goalie_stats['save_percentage']:.3f}")
        print(f"Goals Against Average: {goalie_stats['gaa']:.2f}")
    else:
        print("ERROR: Failed to calculate goalie statistics!")

if __name__ == "__main__":
    main()
