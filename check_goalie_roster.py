from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService

def main():
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get game roster data
    game_roster = data_service.get_game_roster()
    
    # Get players and filter goalies
    players = data_service.get_players()
    goalies = players[players['Position'] == 'G']
    
    # Check if goalie is in game roster
    for _, goalie in goalies.iterrows():
        goalie_roster = game_roster[game_roster['PlayerID'] == goalie['ID']]
        print(f"Goalie {goalie['ID']} roster entries:", len(goalie_roster))
        print(goalie_roster)
    
    # Check all unique teams in events
    events = data_service.get_events()
    unique_teams = events['Team'].unique()
    print('\nUnique teams in events:', unique_teams)
    
    # Count events by team
    team_counts = events['Team'].value_counts()
    print('\nEvents by team:')
    print(team_counts)

if __name__ == "__main__":
    main()
