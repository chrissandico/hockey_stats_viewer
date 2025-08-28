from hockey_stats_webapp.services.sheets_service import SheetsService
from hockey_stats_webapp.services.data_service import DataService

def main():
    # Initialize services
    sheets_service = SheetsService()
    data_service = DataService(sheets_service)
    
    # Get game roster data
    game_roster = data_service.get_game_roster()
    print('Game Roster columns:', game_roster.columns.tolist())
    print('Game Roster sample:')
    print(game_roster.head())
    
    # Get players and filter goalies
    players = data_service.get_players()
    goalies = players[players['Position'] == 'G']
    print('\nGoalies:')
    print(goalies)
    
    # Check games for each goalie
    for _, goalie in goalies.iterrows():
        player_games = data_service.get_player_games(goalie['ID'])
        print(f"\nGoalie {goalie['ID']} games:", len(player_games))
        if len(player_games) > 0:
            print("Sample game:", player_games.iloc[0].to_dict())
    
    # Check events data
    events = data_service.get_events()
    print('\nEvents columns:', events.columns.tolist())
    print('Events sample:')
    print(events.head())
    
    # Check team detection
    unique_teams = events['Team'].unique()
    print('\nUnique teams in events:', unique_teams)
    
    # Check if there are any events with IsGoal=True
    goal_events = events[events['IsGoal'] == True]
    print('\nNumber of goal events:', len(goal_events))
    if len(goal_events) > 0:
        print('Sample goal event:', goal_events.iloc[0].to_dict())
    
    # Check if there are any events with EventType=Shot
    shot_events = events[events['EventType'] == 'Shot']
    print('\nNumber of shot events:', len(shot_events))
    if len(shot_events) > 0:
        print('Sample shot event:', shot_events.iloc[0].to_dict())

if __name__ == "__main__":
    main()
