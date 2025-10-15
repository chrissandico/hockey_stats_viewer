# Requirements Document

## Introduction

The hockey stats web application has a critical bug in the game statistics screen where game scores are not updating correctly when the game type filter is changed. When users select different game types (Exhibition, Regular Season, Tournament, or All Games) using the radio buttons, the individual game statistics update correctly, but the game list still shows incorrect scores from the previously cached data. This creates a confusing user experience where the game list shows one score but clicking on the game shows different, correct statistics.

## Requirements

### Requirement 1

**User Story:** As a coach or player viewing game statistics, I want the game scores in the game list to update immediately when I change the game type filter, so that I can see accurate scores for the selected game type.

#### Acceptance Criteria

1. WHEN a user changes the game type filter THEN the game dropdown list SHALL display updated scores that match the selected game type
2. WHEN a user selects a specific game after changing the game type filter THEN the displayed score in the game list SHALL match the score shown in the detailed game view
3. WHEN the game type filter is set to "All Games" THEN the game list SHALL show scores calculated from all game events regardless of game type
4. WHEN the game type filter is set to a specific type (Exhibition, Regular Season, Tournament) THEN the game list SHALL show scores calculated only from events of that game type

### Requirement 2

**User Story:** As a user of the hockey stats application, I want consistent data display across all views, so that I can trust the accuracy of the statistics being shown.

#### Acceptance Criteria

1. WHEN viewing game statistics THEN the scores shown in the game dropdown SHALL always match the scores shown in the detailed game summary
2. WHEN switching between different game type filters THEN the application SHALL clear any stale cached data that could cause inconsistencies
3. WHEN game data is recalculated due to filter changes THEN the new calculations SHALL be immediately reflected in all UI components
4. IF there are caching mechanisms in place THEN they SHALL be invalidated when filter parameters change

### Requirement 3

**User Story:** As a developer maintaining the hockey stats application, I want the caching system to properly handle filter-dependent data, so that users always see accurate and up-to-date information.

#### Acceptance Criteria

1. WHEN game data is cached THEN the cache key SHALL include all relevant filter parameters (team_id, game_type)
2. WHEN filter parameters change THEN the system SHALL use the appropriate cached data or recalculate if no matching cache exists
3. WHEN game scores are calculated THEN the calculation SHALL respect the current game type filter settings
4. WHEN the game dropdown is updated due to filter changes THEN the score calculations SHALL use the same filter parameters as the dropdown update