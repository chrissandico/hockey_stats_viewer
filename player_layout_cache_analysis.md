# Player Layout Cache Behavior Analysis

## Current Implementation Analysis

### Callback Function: `update_player_info()`

**Location:** `hockey_stats_webapp/layouts/player_layout.py` (lines ~120-400)

**Current Signature:**
```python
@app.callback(
    [dash.dependencies.Output('player-info-container', 'children'),
     dash.dependencies.Output('player-game-log-container', 'children')],
    [dash.dependencies.Input('player-dropdown', 'value'),
     dash.dependencies.Input('game-type-session-store', 'data')]
)
def update_player_info(jersey_number, game_type_data):
```

### Current Cache Usage Patterns

#### 1. **No Explicit Cache Management**
- The callback does NOT use any cache clearing methods
- No calls to `data_service.clear_games_cache()`
- No state tracking for previous selections
- No cache diagnostic logging

#### 2. **Data Retrieval Methods Used**
The callback uses these data service methods that may be cached:
- `data_service.get_players(team_id)` - Gets player roster
- `data_service.calculate_player_stats(player_id, team_id, game_type)` - Calculates player statistics
- `data_service.calculate_goalie_stats(player_id, team_id, game_type)` - Calculates goalie statistics  
- `data_service.get_player_game_log(player_id, team_id, game_type)` - Gets game-by-game log

#### 3. **Current State Tracking**
- Uses Flask session for: `team_id`, `is_coach`
- Processes `game_type_data` from callback input
- Handles "All Games" selection (converts "all" to None)
- **Missing:** No tracking of previous player selection or game type

### Cache Issues Identified

#### 1. **Game Type Filter Changes**
**Problem:** When users change game type filters, cached data from previous filter selections may be displayed.

**Current Behavior:**
```python
# Game type processing - no cache clearing
game_type = game_type_data if isinstance(game_type_data, str) else None
if game_type_data and isinstance(game_type_data, dict):
    game_type = game_type_data.get('game_type')

# Handle "All Games" selection
if game_type == "all":
    game_type = None
```

**Missing:** Cache clearing when `game_type` changes from previous selection.

#### 2. **Player Selection Changes**
**Problem:** When users select different players, cached statistics from previous player selections may be displayed.

**Current Behavior:**
```python
if jersey_number is None:
    return html.Div(), html.Div()

# Get player data - no cache clearing for player changes
team_players = data_service.get_players(team_id)
matching_players = team_players[team_players['JerseyNumber'] == jersey_number]
```

**Missing:** Cache clearing when `jersey_number` changes from previous selection.

#### 3. **No Error Handling for Cache Operations**
**Problem:** No graceful degradation if cache operations were to fail.

**Current Behavior:** No cache error handling implemented.

### Comparison with Fixed Team Layout

#### Team Layout Cache Implementation (Reference)
```python
# Cache management: Track previous game type to detect changes
previous_game_type = session.get('team_previous_game_type')

# Clear cache if game type has changed
if previous_game_type != game_type:
    try:
        # Clear cache for previous game type
        data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
        
        # Clear cache for current game type
        data_service.clear_games_cache(team_id=team_id, game_type=game_type)
        
        # Update session with new game type
        session['team_previous_game_type'] = game_type
        
    except Exception as cache_error:
        logger.error(f"Cache management error: {str(cache_error)}")
        # Continue execution despite cache errors
```

## Required Cache Management Implementation

### 1. **Game Type Filter Cache Clearing**

**Where to Add:** In `update_player_info()` callback after game type processing

**Implementation Needed:**
```python
# Track previous game type to detect changes
previous_game_type = session.get('player_previous_game_type')

# Clear cache if game type has changed
if previous_game_type != game_type:
    try:
        # Clear cache for previous and current game types
        data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
        data_service.clear_games_cache(team_id=team_id, game_type=game_type)
        
        # Update session
        session['player_previous_game_type'] = game_type
        
    except Exception as cache_error:
        # Log error but continue execution
        logger.error(f"Player layout cache error: {str(cache_error)}")
```

### 2. **Player Selection Cache Clearing**

**Where to Add:** In `update_player_info()` callback after player selection processing

**Implementation Needed:**
```python
# Track previous player selection to detect changes
previous_jersey_number = session.get('player_previous_jersey_number')

# Clear cache if player selection has changed
if previous_jersey_number != jersey_number:
    try:
        # Clear cache for the team to ensure fresh player data
        data_service.clear_games_cache(team_id=team_id)
        
        # Update session
        session['player_previous_jersey_number'] = jersey_number
        
    except Exception as cache_error:
        # Log error but continue execution
        logger.error(f"Player selection cache error: {str(cache_error)}")
```

### 3. **Error Handling and Logging**

**Implementation Needed:**
- Import logging module
- Add try-catch blocks around cache operations
- Log cache clearing operations for debugging
- Ensure graceful degradation if cache operations fail
- Use same logging patterns as team layout

### 4. **Session State Management**

**New Session Variables Needed:**
- `player_previous_game_type` - Track previous game type selection
- `player_previous_jersey_number` - Track previous player selection

## Cache Key Patterns (From data_service.py)

The cache uses keys in format: `"games_{team_id}_{game_type}"`

**Examples:**
- `"games_team1_R"` - Regular season games for team1
- `"games_team1_None"` - All games for team1  
- `"games_None_R"` - Regular season games for all teams

## Available Cache Management Methods

### 1. `data_service.clear_games_cache(team_id=None, game_type=None)`
- Clears cached games data
- Can clear all cache or specific team/game_type combinations
- Has comprehensive error handling and logging
- Returns gracefully if cache not initialized

### 2. `data_service.get_cache_info()`
- Returns cache diagnostic information
- Useful for debugging cache issues
- Provides cache size, keys, and memory usage

## Requirements Mapping

This analysis addresses the following requirements:

- **Requirement 2.1:** Player screen cache refresh on navigation ✓
- **Requirement 2.2:** Player screen cache clearing on filter changes ✓  
- **Requirement 2.3:** Player screen cache clearing on player selection changes ✓
- **Requirement 3.1:** Consistent cache behavior across screens ✓

## Next Steps

1. Implement cache clearing logic in `update_player_info()` callback
2. Add error handling and logging for cache operations  
3. Add session state tracking for previous selections
4. Test cache behavior with different player and filter combinations
5. Ensure consistent patterns with team layout implementation