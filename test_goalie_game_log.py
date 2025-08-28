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
    
    print("\n=== TESTING GET_PLAYER_GAME_LOG FOR GOALIE ===")
    # Get game log for the goalie
    game_log = data_service.get_player_game_log(goalie_id)
    print(f"Game log entries: {len(game_log)}")
    
    if game_log:
        print("\n=== SAMPLE GAME LOG ENTRY ===")
        sample_entry = game_log[0]
        print(f"Game ID: {sample_entry['game']['ID']}")
        print(f"Date: {sample_entry['game']['Date']}")
        print(f"Opponent: {sample_entry['game']['Opponent']}")
        print(f"Result: {sample_entry['result']}")
        print(f"Goals Against: {sample_entry['goals_against']}")
        print(f"Shots Against: {sample_entry['shots_against']}")
        print(f"Saves: {sample_entry['saves']}")
        print(f"Save Percentage: {sample_entry['save_percentage']:.3f}")
        print(f"Shutout: {sample_entry['shutout']}")
    else:
        print("ERROR: No game log entries found for goalie!")

if __name__ == "__main__":
    main()
