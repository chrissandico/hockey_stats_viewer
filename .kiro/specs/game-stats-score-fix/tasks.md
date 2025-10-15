# Implementation Plan

- [x] 1. Extract and enhance score calculation logic





  - Create new `_calculate_game_scores()` method in DataService to centralize score calculation with proper event filtering
  - Add game type filtering logic to only count events that match the current filter context
  - Handle "All Games" case (None game_type) to include all events regardless of game type
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Fix game score calculation in get_games method





  - Modify the score calculation loop in `DataService.get_games()` to use the new `_calculate_game_scores()` method
  - Ensure event filtering respects the game_type parameter passed to get_games
  - Update the goal calculation logic to filter events by game type before counting goals
  - _Requirements: 1.1, 1.2, 2.1, 3.4_

- [x] 3. Add event filtering helper method





  - Create `_filter_events_by_game_type()` method to handle event filtering logic
  - Implement proper handling of None game_type (All Games) vs specific game types
  - Add validation for game type values and fallback behavior
  - _Requirements: 1.3, 1.4, 3.3_

- [ ]* 4. Add comprehensive unit tests for score calculation
  - Write unit tests for `_calculate_game_scores()` method with different game type filters
  - Test "All Games" scenario includes all events regardless of game type
  - Test specific game type filters only include matching events
  - Test edge cases like games with no events or invalid game types
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 5. Add integration tests for UI consistency
  - Create test to verify game dropdown scores match detail view scores
  - Test rapid filter switching scenarios
  - Verify cache behavior with different game type contexts
  - Test session context handling and team filtering
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6. Add error handling and logging









  - Add proper error handling for edge cases in score calculation
  - Implement logging to track score calculation context and results
  - Add fallback behavior for missing or invalid data
  - Handle cases where team identifier mapping fails
  - _Requirements: 2.3, 3.2, 3.3_

- [ ] 7. Update cache invalidation strategy
  - Ensure cache keys properly differentiate between different game type contexts
  - Add cache clearing mechanism for development/testing purposes
  - Verify existing cache entries don't interfere with new calculations
  - _Requirements: 3.1, 3.2_