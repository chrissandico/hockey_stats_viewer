# Recent Games Score Issue Investigation

## Problem Statement
Recent games (especially games that ended the same day or very recent games) are showing incorrect scores in:
1. Game log in the team stats screen
2. Listing of games in the game stats screen

## Likely Root Causes

### 1. **Caching Issue** (Most Likely)
The application caches game data with calculated scores. When new games are added or recent games are updated:
- The cache may not be invalidated/refreshed
- Recent game scores are calculated once and cached
- Subsequent updates to events don't trigger cache refresh
- Cache TTL (Time To Live) may be too long for recent games

**Evidence:**
- Issue specifically affects recent games
- Older games show correct scores
- Suggests data is cached at time of first calculation

### 2. **Data Entry Timing**
Recent games may be entered in stages:
- Game record created first (with 0-0 score)
- Events added later
- Score calculation happens before events are fully entered
- Cached score reflects incomplete data

### 3. **Boolean Conversion Timing**
The `IsGoal` column boolean conversion happens at service initialization:
- If events are added after service starts, they may not be converted
- Recent events might have string 'TRUE'/'FALSE' instead of boolean
- Score calculation expects boolean values

### 4. **Date Filtering Edge Cases**
Recent games might be affected by:
- Timezone differences between server and data entry
- Games entered "today" might be filtered as "future" games
- Date comparison logic may exclude same-day games

## Investigation Findings

From existing investigation files:

1. **Test data shows score calculation WORKS correctly** when data is properly formatted
2. **Boolean conversion is functioning** in the data service
3. **Date filtering includes recent games** (not filtering them out)
4. **Team identifier mapping works** for both recent and old games

## Most Probable Cause: **Cache Invalidation**

The score calculation logic is working correctly, but:
- Scores are calculated and cached when games are first loaded
- If events are added/updated after caching, the cache isn't refreshed
- Recent games are more likely to have events added after initial load
- Older games are stable (no new events), so cached scores remain correct

## Recommended Solutions

### Solution 1: Force Cache Refresh for Recent Games
```python
# In get_games method, check if games are recent
# If recent (within last 7 days), force cache refresh
if game_date > (today - timedelta(days=7)):
    # Clear cache for this game
    self.clear_games_cache(team_id, game_type)
```

### Solution 2: Reduce Cache TTL for Recent Data
```python
# Use shorter cache TTL for recent games
if game_is_recent:
    cache_ttl = 300  # 5 minutes
else:
    cache_ttl = 3600  # 1 hour
```

### Solution 3: Add Cache Invalidation on Data Update
```python
# When events are added/updated, invalidate related game caches
def add_event(self, event_data):
    game_id = event_data['GameID']
    # Clear cache for this game
    self.invalidate_game_cache(game_id)
```

### Solution 4: Add "Force Refresh" Button
- Add UI button to force refresh recent games
- Clears cache and recalculates scores
- User-initiated when they know data has been updated

## Testing Recommendations

1. **Test with actual recent game data** from Google Sheets
2. **Check cache timestamps** to see when scores were calculated
3. **Monitor cache hits/misses** for recent vs old games
4. **Test score calculation** immediately after adding new events
5. **Verify boolean conversion** for recently added events

## Next Steps

1. Access Google Sheets to examine actual recent game data
2. Check if events exist for recent games showing wrong scores
3. Verify IsGoal values are correct in the Events sheet
4. Test cache invalidation by forcing refresh
5. Implement one of the recommended solutions

## Key Questions to Answer

1. Do recent games have events in the Events sheet?
2. Are the IsGoal values correct (TRUE/FALSE or boolean)?
3. When were the scores calculated (cache timestamp)?
4. Are events being added after initial cache?
5. Is there a pattern to which recent games show wrong scores?
