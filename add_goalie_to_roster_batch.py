from hockey_stats_webapp.services.sheets_service import SheetsService
import pandas as pd
import time

def main():
    # Initialize services
    sheets_service = SheetsService()
    
    # Get game roster data
    game_roster = sheets_service.get_game_roster()
    print('Original Game Roster size:', len(game_roster))
    
    # Get players and filter goalies
    players = sheets_service.get_players()
    goalies = players[players['Position'] == 'G']
    print('\nGoalies:')
    print(goalies[['ID', 'JerseyNumber', 'TeamID', 'Position']])
    
    # Get games
    games = sheets_service.get_games()
    print(f'\nTotal games: {len(games)}')
    
    # Add goalie to game roster for all games
    if not goalies.empty:
        goalie_id = goalies.iloc[0]['ID']
        print(f"\nAdding goalie {goalie_id} to all games")
        
        # Check if goalie is already in any games
        existing_goalie_entries = game_roster[game_roster['PlayerID'] == goalie_id]
        print(f"Goalie already in {len(existing_goalie_entries)} games")
        
        # Create new entries for the goalie in games where they're not already present
        new_entries = []
        existing_game_ids = existing_goalie_entries['GameID'].tolist()
        
        for _, game in games.iterrows():
            if game['ID'] not in existing_game_ids:
                new_entry = {
                    'GameID': game['ID'],
                    'PlayerID': goalie_id,
                    'Status': 'Present'
                }
                new_entries.append(new_entry)
        
        if new_entries:
            # Create DataFrame from new entries
            new_entries_df = pd.DataFrame(new_entries)
            print(f'\nAdding {len(new_entries)} new entries for goalie')
            
            # Combine with existing game roster
            updated_game_roster = pd.concat([game_roster, new_entries_df], ignore_index=True)
            print(f'Updated Game Roster size: {len(updated_game_roster)}')
            
            # Update the Google Sheet using batch update
            worksheet = sheets_service._get_worksheet('GameRoster')
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare all data as a list of lists
            all_data = [['GameID', 'PlayerID', 'Status']]  # Header
            for _, row in updated_game_roster.iterrows():
                all_data.append([row['GameID'], row['PlayerID'], row['Status']])
            
            # Update in one batch operation
            worksheet.update('A1', all_data)
            
            print("\nGame roster updated successfully!")
        else:
            print("\nGoalie is already in all games. No updates needed.")
    else:
        print("\nNo goalies found in the players data.")

if __name__ == "__main__":
    main()
