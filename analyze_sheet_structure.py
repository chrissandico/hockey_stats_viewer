#!/usr/bin/env python3

"""
Script to analyze the actual Google Sheet structure and update the app accordingly.
This will help identify the correct column names and fix the KeyError issue definitively.
"""

import sys
import os
import json

# Add the hockey_stats_webapp directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'hockey_stats_webapp'))

def analyze_sheet_structure():
    """Analyze the actual Google Sheet structure to identify column names."""
    
    print("=== ANALYZING GOOGLE SHEET STRUCTURE ===")
    
    try:
        from services.sheets_service import SheetsService
        
        print("Connecting to Google Sheets...")
        sheets_service = SheetsService()
        
        # Analyze all sheets
        sheets_to_analyze = ['Players', 'Teams', 'Games', 'Events', 'GameRoster']
        
        analysis_results = {}
        
        for sheet_name in sheets_to_analyze:
            print(f"\n--- Analyzing {sheet_name} Sheet ---")
            
            try:
                if sheet_name == 'Players':
                    data = sheets_service.get_players()
                elif sheet_name == 'Teams':
                    data = sheets_service.get_teams()
                elif sheet_name == 'Games':
                    data = sheets_service.get_games()
                elif sheet_name == 'Events':
                    data = sheets_service.get_events()
                elif sheet_name == 'GameRoster':
                    data = sheets_service.get_game_roster()
                else:
                    continue
                
                if not data.empty:
                    columns = data.columns.tolist()
                    print(f"✅ {sheet_name} columns: {columns}")
                    print(f"   Rows: {len(data)}")
                    
                    # Show sample data for first row
                    if len(data) > 0:
                        sample_row = data.iloc[0]
                        print(f"   Sample row:")
                        for col in columns[:10]:  # Show first 10 columns
                            value = sample_row[col]
                            print(f"     {col}: {value}")
                        if len(columns) > 10:
                            print(f"     ... and {len(columns) - 10} more columns")
                    
                    analysis_results[sheet_name] = {
                        'columns': columns,
                        'row_count': len(data),
                        'sample_data': sample_row.to_dict() if len(data) > 0 else {}
                    }
                else:
                    print(f"❌ {sheet_name} sheet is empty")
                    analysis_results[sheet_name] = {
                        'columns': [],
                        'row_count': 0,
                        'sample_data': {}
                    }
                    
            except Exception as e:
                print(f"❌ Error analyzing {sheet_name}: {e}")
                analysis_results[sheet_name] = {
                    'error': str(e),
                    'columns': [],
                    'row_count': 0,
                    'sample_data': {}
                }
        
        # Special analysis for the KeyError issue
        print(f"\n=== ANALYZING KEYERROR ISSUE ===")
        
        if 'Players' in analysis_results and analysis_results['Players']['columns']:
            players_columns = analysis_results['Players']['columns']
            
            # Look for ID-like columns
            id_columns = [col for col in players_columns if 'id' in col.lower()]
            print(f"ID-like columns in Players: {id_columns}")
            
            # Check for goalies specifically
            try:
                players = sheets_service.get_players()
                if 'Position' in players.columns:
                    goalies = players[players['Position'] == 'G']
                    if not goalies.empty:
                        print(f"Found {len(goalies)} goalies")
                        goalie = goalies.iloc[0]
                        print(f"First goalie data structure:")
                        for col in goalie.index:
                            print(f"  {col}: {goalie[col]}")
                        
                        # Test which ID column works
                        possible_id_columns = ['ID', 'PlayerID', 'id', 'player_id', 'Id']
                        working_id_column = None
                        
                        for col_name in possible_id_columns:
                            if col_name in goalie.index:
                                try:
                                    goalie_id = goalie[col_name]
                                    print(f"✅ Column '{col_name}' works: {goalie_id}")
                                    working_id_column = col_name
                                    break
                                except Exception as e:
                                    print(f"❌ Column '{col_name}' failed: {e}")
                        
                        if working_id_column:
                            print(f"\n🎯 SOLUTION: Use column '{working_id_column}' for player IDs")
                            analysis_results['recommended_id_column'] = working_id_column
                        else:
                            print(f"\n⚠️  WARNING: No working ID column found!")
                            analysis_results['recommended_id_column'] = None
                    else:
                        print("No goalies found in Players sheet")
                else:
                    print("No 'Position' column found in Players sheet")
            except Exception as e:
                print(f"Error analyzing goalies: {e}")
        
        # Save analysis results
        with open('sheet_structure_analysis.json', 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n✅ Analysis complete! Results saved to 'sheet_structure_analysis.json'")
        
        return analysis_results
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_fix_recommendations(analysis_results):
    """Generate specific fix recommendations based on the analysis."""
    
    print(f"\n=== FIX RECOMMENDATIONS ===")
    
    if not analysis_results:
        print("❌ No analysis results available")
        return
    
    # Check if we found a working ID column
    if 'recommended_id_column' in analysis_results:
        id_column = analysis_results['recommended_id_column']
        if id_column:
            print(f"✅ RECOMMENDED FIX:")
            print(f"   Update app.py to use column '{id_column}' instead of 'ID'")
            print(f"   Change: goalie['ID'] -> goalie['{id_column}']")
            
            # Generate the exact code fix
            print(f"\n📝 EXACT CODE CHANGE NEEDED:")
            print(f"   In hockey_stats_webapp/app.py, line ~65:")
            print(f"   OLD: goalie_id = goalie['ID']")
            print(f"   NEW: goalie_id = goalie['{id_column}']")
        else:
            print(f"❌ PROBLEM: No working ID column found")
            print(f"   The Players sheet may be missing ID columns")
            print(f"   Available columns: {analysis_results.get('Players', {}).get('columns', [])}")
    
    # Check for other potential issues
    for sheet_name, sheet_data in analysis_results.items():
        if isinstance(sheet_data, dict) and 'error' in sheet_data:
            print(f"⚠️  {sheet_name} sheet has issues: {sheet_data['error']}")
    
    print(f"\n💡 GENERAL RECOMMENDATIONS:")
    print(f"   1. The current fix with multiple column attempts should work")
    print(f"   2. Enhanced error handling will prevent crashes")
    print(f"   3. Consider updating the exact column name if identified")

def main():
    """Main function to run the analysis."""
    
    print("Google Sheet Structure Analysis")
    print("=" * 50)
    
    analysis_results = analyze_sheet_structure()
    
    if analysis_results:
        generate_fix_recommendations(analysis_results)
        
        print(f"\n" + "=" * 50)
        print(f"SUMMARY")
        print(f"=" * 50)
        print(f"✅ Analysis completed successfully")
        print(f"📄 Results saved to 'sheet_structure_analysis.json'")
        print(f"🔧 Check recommendations above for specific fixes")
    else:
        print(f"\n❌ Analysis failed - check your credentials and connection")
    
    return analysis_results is not None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
