# Design Document

## Overview

This design addresses the cache management inconsistencies between the game statistics screen (which has been fixed) and the team/player statistics screens (which still have cache issues). The solution involves applying the same cache management patterns that were successfully implemented for the game screen to the team and player screens.

## Architecture

### Current State Analysis

**Game Layout (Fixed):**
- Uses enhanced cache management methods
- Properly clears cache on filter changes
- Has error handling and logging
- Refreshes data appropriately

**Team Layout (Needs Fix):**
- Uses old caching approach
- No explicit cache clearing on filter changes
- Limited error handling for cache operations
- May display stale data

**Player Layout (Needs Fix):**
- Uses old caching approach
- No explicit cache clearing on filter changes
- Limited error handling for cache operations
- May display stale data

### Target Architecture

All three layouts (game, team, player) will use the same cache management approach:
1. **Consistent Cache Clearing**: Use `clear_games_cache()` method when filters change
2. **Error Handling**: Implement the same error handling patterns
3. **Logging**: Use consistent logging for cache operations
4. **Data Refresh**: Ensure fresh data on navigation and filter changes

## Components and Interfaces

### 1. Enhanced Team Layout Callbacks

**File:** `hockey_stats_webapp/layouts/team_layout.py`

**Changes Required:**
- Modify `update_team_stats_by_game_type()` callback to clear cache before data retrieval
- Add cache clearing logic similar to game layout
- Implement error handling for cache operations
- Add logging for cache operations

**Interface:**
```python
def update_team_stats_by_game_type(game_type_data):
    # Clear relevant cache entries
    data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
    
    # Proceed with existing logic
    # ... existing team stats calculation
```

### 2. Enhanced Player Layout Callbacks

**File:** `hockey_stats_webapp/layouts/player_layout.py`

**Changes Required:**
- Modify `update_player_info()` callback to clear cache before data retrieval
- Add cache clearing logic when player selection changes
- Add cache clearing logic when game type filter changes
- Implement error handling for cache operations
- Add logging for cache operations

**Interface:**
```python
def update_player_info(jersey_number, game_type_data):
    # Clear relevant cache entries when filters change
    if game_type_changed:
        data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
    
    # Proceed with existing logic
    # ... existing player stats calculation
```

### 3. Cache Management Integration

**Existing Methods to Leverage:**
- `data_service.clear_games_cache(team_id=None, game_type=None)` - Already implemented
- `data_service.get_cache_info()` - Already implemented for diagnostics
- Enhanced error handling patterns from game layout

**Cache Clearing Strategy:**
1. **On Filter Change**: Clear cache entries for the previous filter state
2. **On Navigation**: Optionally clear cache to ensure fresh data
3. **Selective Clearing**: Use team_id and game_type parameters to clear only relevant cache entries
4. **Error Recovery**: Continue operation even if cache clearing fails

## Data Models

### Cache Key Structure (Already Implemented)

The existing cache system uses keys in the format:
```
"games_{team_id}_{game_type}"
```

Examples:
- `"games_team1_R"` - Regular season games for team1
- `"games_team1_None"` - All games for team1
- `"games_None_R"` - Regular season games for all teams

### Cache State Tracking

Track cache state changes to determine when clearing is needed:
```python
# Track previous state to detect changes
previous_game_type = session.get('previous_game_type')
current_game_type = get_current_game_type()

if previous_game_type != current_game_type:
    # Clear cache for previous state
    data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
    # Update session with new state
    session['previous_game_type'] = current_game_type
```

## Error Handling

### Cache Operation Error Handling

Follow the same pattern established in the game layout:

1. **Graceful Degradation**: If cache clearing fails, continue with data retrieval
2. **Logging**: Log cache operations and any errors
3. **Fallback**: Use existing fallback mechanisms if cache operations fail
4. **User Experience**: Ensure cache issues don't break the user interface

### Error Scenarios

1. **Cache Clearing Failure**: Log error, continue with data retrieval
2. **Cache Info Retrieval Failure**: Log error, continue without diagnostics
3. **Memory Issues**: Handle cache size limits gracefully
4. **Concurrent Access**: Handle multiple users accessing cache simultaneously

## Testing Strategy

### Unit Testing

1. **Cache Clearing Logic**: Test that cache is cleared when filters change
2. **Error Handling**: Test behavior when cache operations fail
3. **State Tracking**: Test that previous state is tracked correctly
4. **Selective Clearing**: Test that only relevant cache entries are cleared

### Integration Testing

1. **Cross-Screen Consistency**: Test that all screens behave consistently
2. **Filter Changes**: Test cache behavior when changing between different game types
3. **Navigation**: Test cache behavior when navigating between screens
4. **Performance**: Ensure cache improvements don't degrade performance

### User Acceptance Testing

1. **Data Freshness**: Verify that users see current data after filter changes
2. **Performance**: Ensure application remains responsive
3. **Error Recovery**: Verify graceful handling of cache errors
4. **Consistency**: Verify consistent behavior across all screens

## Implementation Approach

### Phase 1: Team Layout Cache Fix
1. Analyze current team layout callback structure
2. Implement cache clearing logic in `update_team_stats_by_game_type()`
3. Add error handling and logging
4. Test team layout cache behavior

### Phase 2: Player Layout Cache Fix
1. Analyze current player layout callback structure
2. Implement cache clearing logic in `update_player_info()`
3. Add state tracking for player selection changes
4. Add error handling and logging
5. Test player layout cache behavior

### Phase 3: Integration and Testing
1. Test cross-screen cache consistency
2. Verify performance characteristics
3. Test error scenarios
4. Document cache behavior for future maintenance

### Rollback Strategy

If issues arise:
1. **Selective Rollback**: Can disable cache clearing for specific screens
2. **Feature Flags**: Use conditional logic to enable/disable new cache behavior
3. **Monitoring**: Use existing logging to monitor cache performance
4. **Fallback**: Existing cache behavior remains as fallback option