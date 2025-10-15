"""
Progressive data updates service for real-time data streaming and incremental loading.

This service provides functionality for streaming data updates, incremental loading
of large datasets, and smooth transitions between loading states.
"""

import asyncio
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import queue


@dataclass
class DataUpdate:
    """Represents a data update event."""
    update_id: str
    data_type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1  # 1=high, 2=medium, 3=low
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadingState:
    """Represents the loading state of a component."""
    component_id: str
    is_loading: bool = False
    progress: float = 0.0
    stage: str = "idle"  # idle, loading, processing, complete, error
    error_message: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)


class ProgressiveDataService:
    """
    Service for handling progressive data updates and streaming.
    
    Provides real-time data streaming, incremental loading, and smooth
    transitions between loading states.
    """
    
    def __init__(self, data_service):
        """Initialize with base data service."""
        self.data_service = data_service
        self._update_queue = queue.PriorityQueue()
        self._subscribers = {}
        self._loading_states = {}
        self._cache = {}
        self._background_tasks = []
        self._running = False
        
    def start_background_processing(self):
        """Start background processing of data updates."""
        if self._running:
            return
            
        self._running = True
        
        # Start update processor thread
        processor_thread = threading.Thread(
            target=self._process_updates,
            daemon=True
        )
        processor_thread.start()
        self._background_tasks.append(processor_thread)
        
        # Start cache refresh thread
        refresh_thread = threading.Thread(
            target=self._background_cache_refresh,
            daemon=True
        )
        refresh_thread.start()
        self._background_tasks.append(refresh_thread)
    
    def stop_background_processing(self):
        """Stop background processing."""
        self._running = False
        
        # Wait for threads to finish
        for thread in self._background_tasks:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self._background_tasks.clear()
    
    def subscribe_to_updates(self, component_id: str, callback: Callable):
        """Subscribe a component to data updates."""
        if component_id not in self._subscribers:
            self._subscribers[component_id] = []
        
        self._subscribers[component_id].append(callback)
        
        # Initialize loading state
        self._loading_states[component_id] = LoadingState(component_id)
    
    def unsubscribe_from_updates(self, component_id: str, callback: Callable = None):
        """Unsubscribe from data updates."""
        if component_id in self._subscribers:
            if callback:
                try:
                    self._subscribers[component_id].remove(callback)
                except ValueError:
                    pass
            else:
                self._subscribers[component_id].clear()
    
    def queue_data_update(self, update: DataUpdate):
        """Queue a data update for processing."""
        # Priority queue uses tuples (priority, timestamp, update)
        self._update_queue.put((
            update.priority,
            time.time(),
            update
        ))
    
    def get_loading_state(self, component_id: str) -> LoadingState:
        """Get the current loading state of a component."""
        return self._loading_states.get(
            component_id, 
            LoadingState(component_id)
        )
    
    def update_loading_state(self, component_id: str, **kwargs):
        """Update the loading state of a component."""
        if component_id not in self._loading_states:
            self._loading_states[component_id] = LoadingState(component_id)
        
        state = self._loading_states[component_id]
        
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        state.last_updated = datetime.now()
        
        # Notify subscribers of state change
        self._notify_subscribers(component_id, {
            'type': 'loading_state',
            'state': state
        })
    
    def load_data_incrementally(self, component_id: str, data_type: str, 
                              params: Dict[str, Any], chunk_size: int = 100):
        """Load data incrementally in chunks."""
        
        def _load_chunks():
            self.update_loading_state(
                component_id, 
                is_loading=True, 
                stage="loading", 
                progress=0.0
            )
            
            try:
                # Get total count first
                total_count = self._get_data_count(data_type, params)
                
                if total_count == 0:
                    self.update_loading_state(
                        component_id,
                        is_loading=False,
                        stage="complete",
                        progress=100.0
                    )
                    return
                
                # Load data in chunks
                loaded_count = 0
                all_data = []
                
                for offset in range(0, total_count, chunk_size):
                    if not self._running:
                        break
                    
                    # Update progress
                    progress = (loaded_count / total_count) * 100
                    self.update_loading_state(
                        component_id,
                        progress=progress,
                        stage="loading"
                    )
                    
                    # Load chunk
                    chunk_params = params.copy()
                    chunk_params.update({
                        'offset': offset,
                        'limit': chunk_size
                    })
                    
                    chunk_data = self._load_data_chunk(data_type, chunk_params)
                    
                    if chunk_data:
                        all_data.extend(chunk_data)
                        loaded_count += len(chunk_data)
                        
                        # Send incremental update
                        update = DataUpdate(
                            update_id=f"{component_id}_{offset}",
                            data_type=data_type,
                            data={
                                'chunk': chunk_data,
                                'total_loaded': loaded_count,
                                'total_count': total_count,
                                'is_complete': loaded_count >= total_count
                            },
                            priority=2
                        )
                        
                        self._notify_subscribers(component_id, {
                            'type': 'data_chunk',
                            'update': update
                        })
                    
                    # Small delay to prevent overwhelming the UI
                    time.sleep(0.05)
                
                # Mark as complete
                self.update_loading_state(
                    component_id,
                    is_loading=False,
                    stage="complete",
                    progress=100.0
                )
                
                # Cache the complete data
                cache_key = f"{data_type}_{hash(str(params))}"
                self._cache[cache_key] = {
                    'data': all_data,
                    'timestamp': datetime.now(),
                    'ttl': 300  # 5 minutes
                }
                
            except Exception as e:
                self.update_loading_state(
                    component_id,
                    is_loading=False,
                    stage="error",
                    error_message=str(e)
                )
        
        # Start loading in background thread
        thread = threading.Thread(target=_load_chunks, daemon=True)
        thread.start()
    
    def stream_data_updates(self, component_id: str, data_type: str, 
                           params: Dict[str, Any], interval: float = 5.0):
        """Stream real-time data updates."""
        
        def _stream_updates():
            last_update = datetime.now()
            
            while self._running:
                try:
                    # Check if enough time has passed
                    if (datetime.now() - last_update).total_seconds() < interval:
                        time.sleep(0.5)
                        continue
                    
                    # Get fresh data
                    fresh_data = self._get_fresh_data(data_type, params)
                    
                    if fresh_data is not None:
                        # Check if data has changed
                        cache_key = f"{data_type}_{hash(str(params))}"
                        cached_data = self._cache.get(cache_key, {}).get('data')
                        
                        if fresh_data != cached_data:
                            # Data has changed, send update
                            update = DataUpdate(
                                update_id=f"{component_id}_{int(time.time())}",
                                data_type=data_type,
                                data=fresh_data,
                                priority=1,
                                metadata={'is_live_update': True}
                            )
                            
                            self._notify_subscribers(component_id, {
                                'type': 'live_update',
                                'update': update
                            })
                            
                            # Update cache
                            self._cache[cache_key] = {
                                'data': fresh_data,
                                'timestamp': datetime.now(),
                                'ttl': 300
                            }
                    
                    last_update = datetime.now()
                    
                except Exception as e:
                    print(f"Error in stream updates: {e}")
                    time.sleep(interval)
        
        # Start streaming in background thread
        thread = threading.Thread(target=_stream_updates, daemon=True)
        thread.start()
    
    def create_smooth_transition(self, component_id: str, from_state: str, 
                               to_state: str, duration: float = 0.3):
        """Create smooth transition between loading states."""
        
        def _animate_transition():
            steps = 20
            step_duration = duration / steps
            
            for i in range(steps + 1):
                if not self._running:
                    break
                
                progress = i / steps
                
                # Update transition state
                self._notify_subscribers(component_id, {
                    'type': 'transition',
                    'from_state': from_state,
                    'to_state': to_state,
                    'progress': progress,
                    'duration': duration
                })
                
                time.sleep(step_duration)
        
        # Start transition animation
        thread = threading.Thread(target=_animate_transition, daemon=True)
        thread.start()
    
    def _process_updates(self):
        """Background thread to process queued updates."""
        while self._running:
            try:
                # Get update from queue (blocks until available)
                priority, timestamp, update = self._update_queue.get(timeout=1.0)
                
                # Process the update
                self._handle_update(update)
                
                # Mark task as done
                self._update_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing update: {e}")
    
    def _background_cache_refresh(self):
        """Background thread to refresh cached data."""
        while self._running:
            try:
                current_time = datetime.now()
                expired_keys = []
                
                # Check for expired cache entries
                for key, cache_entry in self._cache.items():
                    if 'timestamp' in cache_entry and 'ttl' in cache_entry:
                        age = (current_time - cache_entry['timestamp']).total_seconds()
                        if age > cache_entry['ttl']:
                            expired_keys.append(key)
                
                # Remove expired entries
                for key in expired_keys:
                    del self._cache[key]
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in cache refresh: {e}")
                time.sleep(30)
    
    def _handle_update(self, update: DataUpdate):
        """Handle a single data update."""
        # Find subscribers for this update
        for component_id, callbacks in self._subscribers.items():
            for callback in callbacks:
                try:
                    callback(update)
                except Exception as e:
                    print(f"Error in update callback for {component_id}: {e}")
    
    def _notify_subscribers(self, component_id: str, message: Dict[str, Any]):
        """Notify subscribers of a component about a message."""
        if component_id in self._subscribers:
            for callback in self._subscribers[component_id]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error notifying subscriber {component_id}: {e}")
    
    def _get_data_count(self, data_type: str, params: Dict[str, Any]) -> int:
        """Get the total count of data items."""
        try:
            if data_type == 'player_game_log':
                player_id = params.get('player_id')
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                game_log = self.data_service.get_player_game_log(
                    player_id, team_id, game_type
                )
                return len(game_log) if game_log else 0
                
            elif data_type == 'team_games':
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                games = self.data_service.get_games(team_id, game_type)
                return len(games)
                
            elif data_type == 'team_players':
                team_id = params.get('team_id')
                
                players = self.data_service.get_players(team_id)
                return len(players)
            
            return 0
            
        except Exception as e:
            print(f"Error getting data count for {data_type}: {e}")
            return 0
    
    def _load_data_chunk(self, data_type: str, params: Dict[str, Any]) -> List[Any]:
        """Load a chunk of data."""
        try:
            offset = params.get('offset', 0)
            limit = params.get('limit', 100)
            
            if data_type == 'player_game_log':
                player_id = params.get('player_id')
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                game_log = self.data_service.get_player_game_log(
                    player_id, team_id, game_type
                )
                
                if game_log:
                    return game_log[offset:offset + limit]
                
            elif data_type == 'team_games':
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                games = self.data_service.get_games(team_id, game_type)
                
                if not games.empty:
                    chunk = games.iloc[offset:offset + limit]
                    return chunk.to_dict('records')
            
            return []
            
        except Exception as e:
            print(f"Error loading data chunk for {data_type}: {e}")
            return []
    
    def _get_fresh_data(self, data_type: str, params: Dict[str, Any]) -> Any:
        """Get fresh data for streaming updates."""
        try:
            if data_type == 'team_stats':
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                return self.data_service.calculate_team_stats(team_id, game_type)
                
            elif data_type == 'player_stats':
                player_id = params.get('player_id')
                team_id = params.get('team_id')
                game_type = params.get('game_type')
                
                return self.data_service.calculate_player_stats(
                    player_id, team_id, game_type
                )
            
            return None
            
        except Exception as e:
            print(f"Error getting fresh data for {data_type}: {e}")
            return None


class TransitionManager:
    """Manages smooth transitions between loading states."""
    
    @staticmethod
    def create_fade_transition(duration: float = 0.3):
        """Create a fade transition configuration."""
        return {
            'type': 'fade',
            'duration': duration,
            'easing': 'ease-in-out'
        }
    
    @staticmethod
    def create_slide_transition(direction: str = 'up', duration: float = 0.3):
        """Create a slide transition configuration."""
        return {
            'type': 'slide',
            'direction': direction,
            'duration': duration,
            'easing': 'ease-out'
        }
    
    @staticmethod
    def create_skeleton_to_content_transition(duration: float = 0.5):
        """Create transition from skeleton to actual content."""
        return {
            'type': 'skeleton-fade',
            'duration': duration,
            'stages': [
                {'stage': 'skeleton-fade-out', 'duration': duration * 0.3},
                {'stage': 'content-fade-in', 'duration': duration * 0.7}
            ]
        }


# Global progressive data service instance
_progressive_data_service = None


def get_progressive_data_service(data_service=None):
    """Get or create the global progressive data service instance."""
    global _progressive_data_service
    
    if _progressive_data_service is None and data_service is not None:
        _progressive_data_service = ProgressiveDataService(data_service)
        _progressive_data_service.start_background_processing()
    
    return _progressive_data_service


def cleanup_progressive_data_service():
    """Cleanup the global progressive data service."""
    global _progressive_data_service
    
    if _progressive_data_service is not None:
        _progressive_data_service.stop_background_processing()
        _progressive_data_service = None