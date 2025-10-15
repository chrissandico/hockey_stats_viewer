# Design Document

## Overview

The game statistics screen has a data consistency issue where game scores in the dropdown list don't update when the game type filter changes, even though the detailed game view shows correct scores. This is caused by a caching mechanism in the data service that doesn't properly account for filter-dependent calculations.

The root cause is in the `DataService.get_games()` method, which caches calculated game data (including GoalsFor/GoalsAgainst) based on team_id and game_type, but the score calculations are performed on the full event dataset regardless of the current game type filter context.

## Architecture

### Current Flow (Problematic)
1. User changes game type filter → `update_game_dropdown` callback triggered
2. Callback calls `data_service.get_games(team_id, game_type)` 
3. Data service checks cache with key `games_{team_id}_{game_type}`
4. If cache miss: retrieves games and events, calculates scores using ALL events
5. Caches the result with incorrect scores for the specific game type
6. Returns games with wrong scores for the filter context

### Proposed Flow (Fixed)
1. User changes game type filter → `update_game_dropdown` callback triggered
2. Callback calls `data_service.get_games(team_id, game_type)`
3. Data service checks cache with key `games_{team_id}_{game_type}`
4. If cache miss: retrieves games and events, calculates scores using FILTERED events based on game_type
5. Caches the result with correct scores for the specific game type context
6. Returns games with accurate scores for the filter context

## Components and Interfaces

### Modified Components

#### DataService.get_games()
- **Current Issue**: Calculates GoalsFor/GoalsAgainst using all events regardless of game_type filter
- **Fix**: Filter events by game type before calculating scores
- **Interface**: No changes to method signature
- **Behavior**: Score calculations will respect the game_type parameter

#### DataService._calculate_game_scores()
- **New Method**: Extract score calculation logic into separate method
- **Purpose**: Centralize score calculation with proper event filtering
- **Parameters**: `game_id`, `events_df`, `team_identifier`, `game_type_filter`
- **Returns**: `(goals_for, goals_against)` tuple

### Data Models

#### Game Score Calculation Context
```python
@dataclass
class GameScoreContext:
    game_id: str
    team_identifier: str
    game_type_filter: Optional[str]  # None for "All Games"
    events_df: pd.DataFrame
```

#### Cache Key Structure
- **Current**: `games_{team_id}_{game_type}`
- **Enhanced**: Same structure, but calculations will be context-aware

## Error Handling

### Event Filtering Edge Cases
- **Empty Events**: If no events exist for a game/filter combination, default to 0-0 score
- **Invalid Game Types**: Log warning and treat as "All Games" (no filter)
- **Missing Team Identifier**: Use fallback team identification logic

### Cache Consistency
- **Stale Data**: Existing cache entries remain valid as they represent correct calculations for their specific context
- **Memory Management**: No changes to current TTL-based cache expiration
- **Error Recovery**: If score calculation fails, fall back to 0-0 with warning log

## Testing Strategy

### Unit Tests
1. **Score Calculation Accuracy**
   - Test score calculation with different game type filters
   - Verify "All Games" includes all events
   - Verify specific game types only include relevant events

2. **Cache Behavior**
   - Test cache key generation with different parameters
   - Verify cache isolation between different game type filters
   - Test cache hit/miss scenarios

3. **Edge Cases**
   - Games with no events
   - Invalid game type values
   - Missing team identifiers

### Integration Tests
1. **UI Consistency**
   - Test game dropdown updates when filter changes
   - Verify scores match between dropdown and detail view
   - Test rapid filter switching

2. **Data Flow**
   - Test end-to-end data flow from filter change to UI update
   - Verify session context handling
   - Test with different team contexts

### Manual Testing Scenarios
1. **Filter Switching**
   - Change from "Regular Season" to "All Games" and verify scores update
   - Switch between different specific game types
   - Verify scores in dropdown match detail view

2. **Performance**
   - Test with large datasets to ensure acceptable response times
   - Verify cache effectiveness reduces redundant calculations

## Implementation Approach

### Phase 1: Core Fix
1. Modify `DataService.get_games()` to filter events by game type before score calculation
2. Extract score calculation logic into `_calculate_game_scores()` method
3. Add proper event filtering based on game type context

### Phase 2: Testing & Validation
1. Add comprehensive unit tests for score calculation logic
2. Add integration tests for UI consistency
3. Perform manual testing across different scenarios

### Phase 3: Performance Optimization (Optional)
1. Monitor cache hit rates and performance impact
2. Consider pre-calculating scores for common filter combinations
3. Optimize event filtering queries if needed

## Risk Assessment

### Low Risk
- **Backward Compatibility**: No API changes, existing functionality preserved
- **Performance**: Minimal impact as filtering is lightweight operation
- **Data Integrity**: Fix improves data accuracy without changing underlying data

### Medium Risk
- **Cache Invalidation**: Existing cached data may need to be cleared during deployment
- **Complex Game Types**: Edge cases with unusual game type values need proper handling

### Mitigation Strategies
- **Gradual Rollout**: Deploy to staging environment first
- **Monitoring**: Add logging to track score calculation accuracy
- **Rollback Plan**: Changes are isolated to single method, easy to revert