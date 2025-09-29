# Goalie GP (Games Played) Fix Summary

## Issue Description
Previously, goalies were counted as having played a game (GP) if they were present in the GameRoster, regardless of whether they faced any shots on goal (SOG). This led to inflated GP statistics for goalies who were present but didn't actually play (0 SOG).

## Solution Implemented
Modified the `get_player_games` method in `data_service.py` to add special handling for goalies:

### Key Changes
1. **Goalie Detection**: Check if the player is a goalie (`Position == 'G'`)
2. **Shot Filtering**: For goalies, only count games where they faced at least 1 shot on goal
3. **Event Analysis**: Use the existing `_filter_goalie_events` method to get accurate shot counts per game
4. **Centralized Impact**: Since all goalie stats use `get_player_games`, the fix affects all areas where goalie stats are displayed

### Implementation Details
- Added goalie-specific filtering logic after the standard roster filtering
- Calculate shots against for each game using event data
- Only include games in the result where `shots_against > 0`
- Maintain backward compatibility with existing non-goalie logic

## Test Results
The test script `test_goalie_gp_fix.py` confirmed the fix is working correctly:

### Example Results
- **Goalie #33 (player_11)**: 
  - Present in 7 games according to roster
  - **4 games with 0 SOG excluded from GP**
  - Final GP: 3 games (only games with shots faced)

- **Goalie #35 (player_12)**:
  - Present in 8 games according to roster  
  - **5 games with 0 SOG excluded from GP**
  - Final GP: 3 games (only games with shots faced)

- **Goalie #8 (player_64)**:
  - Present in 7 games according to roster
  - **All 7 games had 0 SOG - excluded from GP**
  - Final GP: 0 games (correctly shows no actual playing time)

### Verification
✅ Games with 0 SOG are properly excluded from GP calculation  
✅ Games with shots > 0 are correctly included  
✅ All goalie statistics now reflect only games where shots were faced  
✅ The fix is centralized and affects all areas where goalie stats are displayed  

## Impact Areas
Since the fix is implemented in the centralized `get_player_games` method, it automatically affects:

1. **Individual Goalie Stats** (`calculate_goalie_stats`)
2. **Team Leaderboards** (`get_team_leaderboard`)
3. **Game Logs** (`get_player_game_log`)
4. **All UI Components** that display goalie statistics

## Benefits
- **More Accurate Statistics**: GP now reflects actual playing time
- **Better Performance Metrics**: Save percentage, GAA, etc. are based on actual games played
- **Consistent Data**: All areas of the application show the same corrected GP values
- **Backward Compatible**: Non-goalies continue to work as before

## Technical Notes
- Uses the existing `_filter_goalie_events` method for accurate shot counting
- Leverages the `GoalieOnIceId` column when available for precise event filtering
- Falls back to all events when `GoalieOnIceId` is not available (backward compatibility)
- Maintains proper team identification for accurate opponent shot counting

The fix ensures that goalie statistics are now more accurate and meaningful, reflecting only the games where goalies actually faced shots and contributed to the team's performance.
