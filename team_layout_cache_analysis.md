# Team Layout Cache Behavior Analysis

## Current Implementation Analysis

### 1. Team Layout Callback Structure

**File:** `hockey_stats_webapp/layouts/team_layout.py`

**Main Callback:** `update_team_stats_by_game_type(game_type_data)`
- **Location:** Lines 350-706
- **Trigger:** Changes to `game-type-session-store` data
- **Outputs:** Updates three loading components (team stats, leaderboards, game log)

### 2. Current Cache Usage Patterns

#### Data Retrieval Methods Called:
1. `data_service.calculate_team_stats(team_id, game_type)` - Team statistics calculation
2. `data_service.get_games(team_id, game_type)` - Game data retrieval  
3. `data_service.get_team_leaderboard(...)` - Player leaderboards (3 calls for F/D/G positions)

#### Cache Dependencies:
- All these methods rely on the underlying `_games_calculated_cache` in data_service
- Cache keys follow pattern: `"games_{team_id}_{game_type}"`
- No explicit cache clearing when filters change

### 3. Current Cache Issues Identified

#### Problem Areas:
1. **No Cache Clearing on Filter Changes**
   - When game type filter changes, cached data from previous filter state may be used
   - This can result in stale data being displayed

2. **Missing State Tracking**
   - No tracking of previous game type to detect when clearing is needed
   - No session state management for cache invalidation

3. **No Error Handling for Cache Operations**
   - No try-catch blocks around data retrieval that could fail due to cache issues
   - No fallback mechanisms if cache becomes corrupted

### 4. Available Cache Management Methods

#### From data_service.py:
1. **`clear_games_cache(team_id=None, game_type=None)`**
   - Clears cached games data with selective parameters
   - Includes comprehensive error handling and logging
   - Supports clearing all cache or specific entries

2. **`get_cache_info()`**
   - Returns cache state information for debugging
   - Provides cache size, keys, and memory usage

### 5. Where Cache Clearing Should Be Added

#### Primary Location:
**Function:** `update_team_stats_by_game_type()` callback
**Line:** Around line 407 (after parameter processing, before data retrieval)

#### Specific Integration Points:
1. **After game type processing** (line ~407)
   - Add state tracking to detect filter changes
   - Clear cache for previous game type if changed

2. **Before data retrieval calls** (lines 410-425)
   - Ensure fresh data by clearing relevant cache entries
   - Add error handling around cache operations

3. **Error handling wrapper**
   - Wrap entire callback in try-catch for cache-related errors
   - Add logging for cache operations

### 6. Comparison with Game Layout

#### Current Status:
- **Game Layout:** No explicit cache clearing found in current implementation
- **Team Layout:** No explicit cache clearing (same issue)
- **Player Layout:** Not yet analyzed (next task)

#### Expected Pattern (from design document):
```python
def update_team_stats_by_game_type(game_type_data):
    # Track previous state
    previous_game_type = session.get('previous_game_type')
    current_game_type = get_current_game_type()
    
    # Clear cache if filter changed
    if previous_game_type != current_game_type:
        data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
        session['previous_game_type'] = current_game_type
    
    # Proceed with existing data retrieval...
```

### 7. Requirements Mapping

#### Requirement 1.1: Navigation refresh
- **Current:** No explicit cache refresh on navigation
- **Needed:** Add cache clearing when team layout is accessed

#### Requirement 1.2: Filter change refresh  
- **Current:** No cache clearing on game type filter changes
- **Needed:** Add cache clearing in `update_team_stats_by_game_type()` callback

#### Requirement 3.1: Consistent behavior
- **Current:** Inconsistent with game layout (neither has proper cache management)
- **Needed:** Implement same pattern across all layouts

### 8. Implementation Strategy

#### Phase 1: Add Basic Cache Clearing
1. Import cache methods at top of file
2. Add state tracking for game type changes
3. Add cache clearing logic before data retrieval
4. Add error handling around cache operations

#### Phase 2: Enhanced Error Handling
1. Wrap callback in comprehensive try-catch
2. Add logging for cache operations
3. Implement graceful degradation for cache failures

#### Phase 3: Testing and Validation
1. Test cache clearing with different filter combinations
2. Verify data freshness after filter changes
3. Test error scenarios and recovery

### 9. Next Steps

1. **Implement cache clearing in team layout callback**
2. **Add error handling and logging**
3. **Test implementation with various filter scenarios**
4. **Move to player layout analysis (Task 3)**
5. **Ensure consistency across all layouts (Task 5)**

## Conclusion

The team layout currently has no explicit cache management, which can lead to stale data being displayed when users change game type filters. The solution involves integrating the existing `clear_games_cache()` method into the `update_team_stats_by_game_type()` callback with proper state tracking and error handling.