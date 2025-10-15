# Cache Management Analysis - Consistent Patterns Across Layouts

## Current State Analysis

### Game Layout Cache Implementation
**Status:** ❌ **NO CACHE MANAGEMENT**
- **File:** `hockey_stats_webapp/layouts/game_layout.py`
- **Cache Clearing:** None implemented
- **Error Handling:** Standard Dash error handling only
- **Logging:** Basic print statements for debugging
- **State Tracking:** None for cache management

**Key Findings:**
- Game layout does NOT have cache clearing logic
- Uses standard callback patterns without cache management
- Relies on data service caching without explicit clearing
- No state tracking for filter changes

### Team Layout Cache Implementation  
**Status:** ✅ **ENHANCED CACHE MANAGEMENT IMPLEMENTED**
- **File:** `hockey_stats_webapp/layouts/team_layout.py`
- **Cache Clearing:** `data_service.clear_games_cache()` on game type changes
- **Error Handling:** Comprehensive try-catch blocks with graceful degradation
- **Logging:** Both `logging` module and print statements
- **State Tracking:** `session['team_previous_game_type']` to detect changes

**Implementation Pattern:**
```python
# Cache management in update_team_stats_by_game_type callback
previous_game_type = session.get('team_previous_game_type')
logger = logging.getLogger(__name__)

if previous_game_type != game_type:
    try:
        logger.info(f"Team layout: Game type changed from {previous_game_type} to {game_type}")
        
        # Clear previous game type cache
        if previous_game_type is not None:
            try:
                data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
                logger.debug(f"Successfully cleared cache for previous game type {previous_game_type}")
            except Exception as prev_cache_error:
                logger.warning(f"Failed to clear cache for previous game type: {str(prev_cache_error)}")
        
        # Clear current game type cache
        try:
            data_service.clear_games_cache(team_id=team_id, game_type=game_type)
            logger.debug(f"Successfully cleared cache for current game type {game_type}")
        except Exception as curr_cache_error:
            logger.warning(f"Failed to clear cache for current game type: {str(curr_cache_error)}")
        
        # Update session state
        session['team_previous_game_type'] = game_type
        logger.info(f"Cache management completed successfully")
        
    except Exception as cache_error:
        logger.error(f"Unexpected error in cache management: {str(cache_error)}")
        # Ensure session is still updated
        session['team_previous_game_type'] = game_type
```

### Player Layout Cache Implementation
**Status:** ✅ **ENHANCED CACHE MANAGEMENT IMPLEMENTED**
- **File:** `hockey_stats_webapp/layouts/player_layout.py`
- **Cache Clearing:** `data_service.clear_games_cache()` on game type OR player selection changes
- **Error Handling:** Comprehensive try-catch blocks with graceful degradation
- **Logging:** Both `logging` module and print statements
- **State Tracking:** `session['player_previous_game_type']` and `session['player_previous_jersey_number']`

**Implementation Pattern:**
```python
# Cache management in update_player_info callback
previous_game_type = session.get('player_previous_game_type')
previous_jersey_number = session.get('player_previous_jersey_number')
logger = logging.getLogger(__name__)

if previous_game_type != game_type or previous_jersey_number != jersey_number:
    try:
        logger.info(f"Player layout: State changed - game type: {previous_game_type} -> {game_type}, player: {previous_jersey_number} -> {jersey_number}")
        
        # Clear previous game type cache
        if previous_game_type is not None:
            try:
                data_service.clear_games_cache(team_id=team_id, game_type=previous_game_type)
                logger.debug(f"Successfully cleared cache for previous game type {previous_game_type}")
            except Exception as prev_cache_error:
                logger.warning(f"Failed to clear cache for previous game type: {str(prev_cache_error)}")
        
        # Clear current game type cache
        try:
            data_service.clear_games_cache(team_id=team_id, game_type=game_type)
            logger.debug(f"Successfully cleared cache for current game type {game_type}")
        except Exception as curr_cache_error:
            logger.warning(f"Failed to clear cache for current game type: {str(curr_cache_error)}")
        
        # Update session state
        session['player_previous_game_type'] = game_type
        session['player_previous_jersey_number'] = jersey_number
        logger.info(f"Cache management completed successfully")
        
    except Exception as cache_error:
        logger.error(f"Unexpected error in cache management: {str(cache_error)}")
        # Ensure session is still updated
        session['player_previous_game_type'] = game_type
        session['player_previous_jersey_number'] = jersey_number
```

## Inconsistencies Identified

### 1. Game Layout Missing Cache Management
- **Issue:** Game layout has no cache clearing logic
- **Impact:** May display stale data when navigating from other screens
- **Required:** Implement same cache management pattern as team/player layouts

### 2. Different Logging Approaches
- **Team/Player:** Use both `logging` module and print statements
- **Game:** Uses only print statements for debugging
- **Required:** Standardize on `logging` module with consistent log levels

### 3. Inconsistent Error Handling Depth
- **Team/Player:** Multi-level try-catch with specific error handling for cache operations
- **Game:** Basic Dash error handling only
- **Required:** Implement same error handling patterns

## Recommended Consistent Cache Management Pattern

### Standard Implementation Template
```python
def layout_callback_with_cache_management(filter_params):
    """Standard pattern for layout callbacks with cache management"""
    from flask import session
    import logging
    
    # Get session context
    team_id = session.get('team_id')
    logger = logging.getLogger(__name__)
    
    # Extract current state
    current_state = extract_current_state(filter_params)
    
    # Get previous state for comparison
    previous_state = session.get('layout_previous_state')
    
    # Cache management: Clear cache if state changed
    if state_changed(previous_state, current_state):
        try:
            logger.info(f"Layout: State changed from {previous_state} to {current_state}, clearing cache")
            
            # Clear previous state cache
            if previous_state is not None:
                try:
                    data_service.clear_games_cache(team_id=team_id, game_type=previous_state.get('game_type'))
                    logger.debug(f"Successfully cleared cache for previous state")
                except Exception as prev_cache_error:
                    logger.warning(f"Failed to clear cache for previous state: {str(prev_cache_error)}")
            
            # Clear current state cache
            try:
                data_service.clear_games_cache(team_id=team_id, game_type=current_state.get('game_type'))
                logger.debug(f"Successfully cleared cache for current state")
            except Exception as curr_cache_error:
                logger.warning(f"Failed to clear cache for current state: {str(curr_cache_error)}")
            
            # Update session state
            session['layout_previous_state'] = current_state
            logger.info(f"Cache management completed successfully")
            
        except Exception as cache_error:
            logger.error(f"Unexpected error in cache management: {str(cache_error)}")
            # Ensure session is still updated to prevent repeated attempts
            try:
                session['layout_previous_state'] = current_state
                logger.debug(f"Session updated despite cache error")
            except Exception as session_error:
                logger.error(f"Failed to update session after cache error: {str(session_error)}")
    else:
        logger.debug(f"State unchanged, no cache clearing needed")
    
    # Continue with normal callback logic...
```

### Key Components of Consistent Pattern

1. **State Tracking**
   - Use session variables to track previous state
   - Compare current vs previous to detect changes
   - Update session state after cache operations

2. **Cache Clearing Strategy**
   - Clear cache for previous state (if exists)
   - Clear cache for current state to ensure consistency
   - Use selective clearing with team_id and game_type parameters

3. **Error Handling Hierarchy**
   - Outer try-catch for overall cache management
   - Inner try-catch for individual cache operations
   - Graceful degradation - continue execution if cache operations fail
   - Always update session state to prevent repeated failed attempts

4. **Logging Standards**
   - Use `logging` module with appropriate log levels
   - `logger.info()` for state changes and completion
   - `logger.debug()` for successful operations
   - `logger.warning()` for recoverable errors
   - `logger.error()` for unexpected errors
   - Include context (team_id, state changes) in log messages

5. **Cache Diagnostic Integration**
   - Use `data_service.get_cache_info()` for debugging when needed
   - Log cache performance metrics where appropriate
   - Monitor cache memory usage in error scenarios

## Next Steps for Consistency

1. **Implement Game Layout Cache Management**
   - Add cache clearing logic to game layout callbacks
   - Implement state tracking for game type filter changes
   - Add consistent error handling and logging

2. **Standardize Logging Across All Layouts**
   - Replace print statements with logging module calls
   - Use consistent log levels and message formats
   - Add cache diagnostic logging where needed

3. **Verify Cache Method Usage**
   - Ensure all layouts use same `clear_games_cache()` parameters
   - Implement consistent cache diagnostic capabilities
   - Add performance monitoring where appropriate