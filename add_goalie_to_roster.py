from hockey_stats_webapp.services.sheets_service import SheetsService
import pandas as pd

def main():
    # Initialize services
    sheets_service = SheetsService()
    
    # Get game roster data
    game_roster = sheets_service.get_game_roster()
    print('Original Game Roster:')
    print(game_roster.head())
    
    # Get players and filter goalies
    players = sheets_service.get_players()
    goalies = players[players['Position'] == 'G']
    print('\nGoalies:')
    print(goalies)
    
    # Get games
    games = sheets_service.get_games()
    print('\nGames:')
    print(games.head())
    
    # Add goalie to game roster for all games
    if not goalies.empty:
        goalie_id = goalies.iloc[0]['ID']
        print(f"\nAdding goalie {goalie_id} to all games")
        
        # Create new entries for the goalie in all games
        new_entries = []
        for _, game in games.iterrows():
            new_entry = {
                'GameID': game['ID'],
                'PlayerID': goalie_id,
                'Status': 'Present'
            }
            new_entries.append(new_entry)
        
        # Create DataFrame from new entries
        new_entries_df = pd.DataFrame(new_entries)
        print('\nNew entries:')
        print(new_entries_df)
        
        # Combine with existing game roster
        updated_game_roster = pd.concat([game_roster, new_entries_df], ignore_index=True)
        print('\nUpdated Game Roster:')
        print(updated_game_roster.head())
        
        # Update the Google Sheet
        worksheet = sheets_service._get_worksheet('GameRoster')
        
        # Clear existing data
        worksheet.clear()
        
        # Add header row
        worksheet.append_row(['GameID', 'PlayerID', 'Status'])
        
        # Add data rows
        for _, row in updated_game_roster.iterrows():
            worksheet.append_row([row['GameID'], row['PlayerID'], row['Status']])
        
        print("\nGame roster updated successfully!")
    else:
        print("\nNo goalies found in the players data.")

if __name__ == "__main__":
    main()
