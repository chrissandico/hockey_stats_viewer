"""
Request Coalescing Module

This module implements request coalescing to merge similar requests,
reduce API calls, and implement request prioritization with timeout
and retry logic.
"""

import time
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
from concurrent.futures import Future, ThreadPoolExecutor
import json


class RequestPriority(Enum):
    """Request priority levels for coalescing and execution."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class RequestType(Enum):
    """Types of requests that can be coalesced."""
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class CoalescedRequest:
    """Represents a coalesced request with multiple similar requests merged."""
    request_id: str
    base_method: str
    request_type: RequestType
    priority: RequestPriority
    created_at: datetime
    timeout: float
    
    # Coalescing data
    similar_requests: List['SingleRequest'] = field(default_factory=list)
    coalescing_key: str = ""
    merged_params: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: Optional[datetime] = None
    
    def add_request(self, request: 'SingleRequest'):
        """Add a similar request to this coalesced request."""
        self.similar_requests.append(request)
        self._update_merged_params(request)
        
        # Update priority to highest among all requests
        if request.priority.value < self.priority.value:
            self.priority = request.priority
    
    def _update_merged_params(self, request: 'SingleRequest'):
        """Update merged parameters with new request data."""
        # Merge parameters intelligently based on request type
        if self.request_type == RequestType.READ:
            # For read requests, merge filters and field selections
            self._merge_read_params(request)
        elif self.request_type == RequestType.WRITE:
            # For write requests, batch the data
            self._merge_write_params(request)
    
    def _merge_read_params(self, request: 'SingleRequest'):
        """Merge parameters for read requests."""
        # Merge field selections
        if 'fields' in request.kwargs:
            existing_fields = set(self.merged_params.get('fields', []))
            new_fields = set(request.kwargs['fields'])
            self.merged_params['fields'] = list(existing_fields.union(new_fields))
        
        # Merge filters (combine with OR logic for similar filters)
        if 'filters' in request.kwargs:
            existing_filters = self.merged_params.get('filters', {})
            new_filters = request.kwargs['filters']
            
            for key, value in new_filters.items():
                if key in existing_filters:
                    # Combine filter values
                    if isinstance(existing_filters[key], list):
                        if isinstance(value, list):
                            existing_filters[key].extend(value)
                        else:
                            existing_filters[key].append(value)
                    else:
                        existing_filters[key] = [existing_filters[key], value]
                else:
                    existing_filters[key] = value
            
            self.merged_params['filters'] = existing_filters
    
    def _merge_write_params(self, request: 'SingleRequest'):
        """Merge parameters for write requests."""
        # Batch write operations
        if 'data' in request.kwargs:
            existing_data = self.merged_params.get('batch_data', [])
            new_data = request.kwargs['data']
            
            if isinstance(new_data, list):
                existing_data.extend(new_data)
            else:
                existing_data.append(new_data)
            
            self.merged_params['batch_data'] = existing_data


@dataclass
class SingleRequest:
    """Represents a single request before coalescing."""
    request_id: str
    method: str
    args: tuple
    kwargs: dict
    priority: RequestPriority
    request_type: RequestType
    created_at: datetime
    timeout: float
    future: Future
    callback: Optional[Callable] = None
    
    def get_coalescing_key(self) -> str:
        """Generate a key for identifying similar requests that can be coalesced."""
        # Create a key based on method and similar parameters
        key_components = [
            self.method,
            self.request_type.value,
            str(self.priority.value)
        ]
        
        # Add relevant kwargs for coalescing
        if self.request_type == RequestType.READ:
            # For reads, coalesce based on data source and basic filters
            key_components.extend([
                self.kwargs.get('worksheet', ''),
                self.kwargs.get('force_refresh', False)
            ])
        elif self.request_type == RequestType.WRITE:
            # For writes, coalesce based on target worksheet
            key_components.extend([
                self.kwargs.get('worksheet', ''),
                self.kwargs.get('operation_type', '')
            ])
        
        key_string = "_".join(str(c) for c in key_components)
        return hashlib.md5(key_string.encode()).hexdigest()


class RequestCoalescer:
    """
    Manages request coalescing to merge similar requests and reduce API calls.
    
    Features:
    - Intelligent request merging based on similarity
    - Priority-based execution ordering
    - Timeout and retry logic with exponential backoff
    - Request deduplication and optimization
    """
    
    def __init__(self, coalescing_window: float = 1.0, max_coalesced_size: int = 20,
                 max_workers: int = 4):
        """
        Initialize the request coalescer.
        
        Args:
            coalescing_window (float): Time window for coalescing similar requests
            max_coalesced_size (int): Maximum number of requests to coalesce together
            max_workers (int): Maximum concurrent worker threads
        """
        self.coalescing_window = coalescing_window
        self.max_coalesced_size = max_coalesced_size
        self.max_workers = max_workers
        
        # Request tracking
        self.pending_requests: Dict[str, SingleRequest] = {}
        self.coalesced_requests: Dict[str, CoalescedRequest] = {}
        self.coalescing_groups: Dict[str, List[str]] = {}  # coalescing_key -> request_ids
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
        self.is_running = False
        self.coalescing_thread = None
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'coalesced_requests': 0,
            'api_calls_saved': 0,
            'average_coalescing_ratio': 0,
            'retry_attempts': 0,
            'timeout_errors': 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the request coalescing processor."""
        if not self.is_running:
            self.is_running = True
            self.coalescing_thread = threading.Thread(target=self._coalescing_processor, daemon=True)
            self.coalescing_thread.start()
            self.logger.info("Request coalescer started")
    
    def stop(self):
        """Stop the request coalescing processor."""
        self.is_running = False
        if self.coalescing_thread:
            self.coalescing_thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)
        self.logger.info("Request coalescer stopped")
    
    def add_request(self, method: str, args: tuple = (), kwargs: dict = None,
                   priority: RequestPriority = RequestPriority.MEDIUM,
                   request_type: RequestType = RequestType.READ,
                   timeout: float = 30.0, callback: Optional[Callable] = None) -> Future:
        """
        Add a request for coalescing.
        
        Args:
            method (str): Method name to execute
            args (tuple): Method arguments
            kwargs (dict): Method keyword arguments
            priority (RequestPriority): Request priority level
            request_type (RequestType): Type of request for coalescing logic
            timeout (float): Request timeout in seconds
            callback (Optional[Callable]): Optional callback function
            
        Returns:
            Future: Future object for the request result
        """
        if kwargs is None:
            kwargs = {}
        
        # Create request object
        request = SingleRequest(
            request_id=self._generate_request_id(),
            method=method,
            args=args,
            kwargs=kwargs,
            priority=priority,
            request_type=request_type,
            created_at=datetime.now(),
            timeout=timeout,
            future=Future(),
            callback=callback
        )
        
        with self.lock:
            self.pending_requests[request.request_id] = request
            self.metrics['total_requests'] += 1
            
            # Add to coalescing group
            coalescing_key = request.get_coalescing_key()
            if coalescing_key not in self.coalescing_groups:
                self.coalescing_groups[coalescing_key] = []
            self.coalescing_groups[coalescing_key].append(request.request_id)
        
        # Start processing if not already running
        if not self.is_running:
            self.start()
        
        self.logger.debug(f"Request added for coalescing: {method} (key: {coalescing_key[:8]})")
        return request.future
    
    def _coalescing_processor(self):
        """Main coalescing processor loop."""
        while self.is_running:
            try:
                self._process_coalescing_groups()
                self._execute_ready_requests()
                time.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                self.logger.error(f"Error in coalescing processor: {e}")
                time.sleep(1.0)
    
    def _process_coalescing_groups(self):
        """Process coalescing groups and create coalesced requests."""
        current_time = datetime.now()
        
        with self.lock:
            ready_groups = []
            
            # Find groups ready for coalescing
            for coalescing_key, request_ids in self.coalescing_groups.items():
                if not request_ids:
                    continue
                
                # Get the oldest request in the group
                oldest_request_id = min(request_ids, 
                                      key=lambda rid: self.pending_requests[rid].created_at)
                oldest_request = self.pending_requests[oldest_request_id]
                
                # Check if coalescing window has elapsed or group is full
                time_elapsed = (current_time - oldest_request.created_at).total_seconds()
                
                if (time_elapsed >= self.coalescing_window or 
                    len(request_ids) >= self.max_coalesced_size):
                    ready_groups.append(coalescing_key)
            
            # Create coalesced requests for ready groups
            for coalescing_key in ready_groups:
                self._create_coalesced_request(coalescing_key)
    
    def _create_coalesced_request(self, coalescing_key: str):
        """Create a coalesced request from a group of similar requests."""
        request_ids = self.coalescing_groups.get(coalescing_key, [])
        if not request_ids:
            return
        
        # Get all requests in the group
        requests = [self.pending_requests[rid] for rid in request_ids 
                   if rid in self.pending_requests]
        
        if not requests:
            return
        
        # Use the highest priority request as the base
        base_request = min(requests, key=lambda r: r.priority.value)
        
        # Create coalesced request
        coalesced = CoalescedRequest(
            request_id=self._generate_request_id(),
            base_method=base_request.method,
            request_type=base_request.request_type,
            priority=base_request.priority,
            created_at=base_request.created_at,
            timeout=max(r.timeout for r in requests),
            coalescing_key=coalescing_key
        )
        
        # Add all requests to the coalesced request
        for request in requests:
            coalesced.add_request(request)
        
        # Store coalesced request
        self.coalesced_requests[coalesced.request_id] = coalesced
        
        # Remove from pending and coalescing groups
        for request_id in request_ids:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
        del self.coalescing_groups[coalescing_key]
        
        # Update metrics
        self.metrics['coalesced_requests'] += len(requests)
        if len(requests) > 1:
            self.metrics['api_calls_saved'] += len(requests) - 1
        
        self.logger.info(f"Created coalesced request with {len(requests)} similar requests")
    
    def _execute_ready_requests(self):
        """Execute coalesced requests that are ready."""
        current_time = datetime.now()
        ready_requests = []
        
        with self.lock:
            for request_id, coalesced in list(self.coalesced_requests.items()):
                # Check if request should be executed
                if self._should_execute_request(coalesced, current_time):
                    ready_requests.append(coalesced)
                    del self.coalesced_requests[request_id]
        
        # Execute ready requests
        for coalesced in ready_requests:
            self.executor.submit(self._execute_coalesced_request, coalesced)
    
    def _should_execute_request(self, coalesced: CoalescedRequest, current_time: datetime) -> bool:
        """Determine if a coalesced request should be executed."""
        # Execute immediately for high priority
        if coalesced.priority == RequestPriority.HIGH:
            return True
        
        # Check timeout
        time_elapsed = (current_time - coalesced.created_at).total_seconds()
        if time_elapsed >= coalesced.timeout:
            return True
        
        # Execute after a small delay for medium/low priority to allow more coalescing
        min_delay = 0.5 if coalesced.priority == RequestPriority.MEDIUM else 1.0
        return time_elapsed >= min_delay
    
    def _execute_coalesced_request(self, coalesced: CoalescedRequest):
        """Execute a coalesced request with retry logic."""
        coalesced.last_attempt = datetime.now()
        
        try:
            # Execute the coalesced request
            result = self._perform_coalesced_execution(coalesced)
            
            # Distribute results to all original requests
            self._distribute_results(coalesced, result)
            
        except Exception as e:
            self.logger.error(f"Error executing coalesced request: {e}")
            
            # Handle retry logic
            if coalesced.retry_count < coalesced.max_retries:
                self._schedule_retry(coalesced, e)
            else:
                self._handle_final_failure(coalesced, e)
    
    def _perform_coalesced_execution(self, coalesced: CoalescedRequest) -> Any:
        """
        Perform the actual execution of a coalesced request.
        This method should be overridden or integrated with your service layer.
        """
        # This is a placeholder for the actual execution logic
        # In real implementation, this would call the appropriate service methods
        
        method_name = coalesced.base_method
        merged_params = coalesced.merged_params
        
        self.logger.info(f"Executing coalesced {method_name} with {len(coalesced.similar_requests)} requests")
        
        # Example integration points:
        if method_name == 'get_players':
            # Execute optimized batch read for players
            return self._execute_batch_read('players', merged_params)
        elif method_name == 'get_games':
            # Execute optimized batch read for games
            return self._execute_batch_read('games', merged_params)
        elif method_name == 'update_events':
            # Execute batch write for events
            return self._execute_batch_write('events', merged_params)
        
        # Default mock execution
        return f"Coalesced result for {method_name}"
    
    def _execute_batch_read(self, resource: str, params: Dict[str, Any]) -> Any:
        """Execute a batch read operation."""
        # This would integrate with your actual sheets service
        # For now, return a mock result
        fields = params.get('fields', [])
        filters = params.get('filters', {})
        
        return {
            'resource': resource,
            'fields': fields,
            'filters': filters,
            'data': f"Batch data for {resource}",
            'count': len(fields) if fields else 100
        }
    
    def _execute_batch_write(self, resource: str, params: Dict[str, Any]) -> Any:
        """Execute a batch write operation."""
        # This would integrate with your actual sheets service
        batch_data = params.get('batch_data', [])
        
        return {
            'resource': resource,
            'written_count': len(batch_data),
            'success': True
        }
    
    def _distribute_results(self, coalesced: CoalescedRequest, result: Any):
        """Distribute execution results to all original requests."""
        for request in coalesced.similar_requests:
            try:
                # Transform result for individual request if needed
                individual_result = self._transform_result_for_request(request, result)
                
                # Set future result
                request.future.set_result(individual_result)
                
                # Call callback if provided
                if request.callback:
                    request.callback(individual_result)
                    
            except Exception as e:
                self.logger.error(f"Error distributing result to request {request.request_id}: {e}")
                request.future.set_exception(e)
    
    def _transform_result_for_request(self, request: SingleRequest, coalesced_result: Any) -> Any:
        """Transform coalesced result for individual request needs."""
        # If the coalesced result contains more data than the individual request needed,
        # filter it down to what was actually requested
        
        if isinstance(coalesced_result, dict) and 'data' in coalesced_result:
            # Apply individual request filters if needed
            if 'filters' in request.kwargs:
                # Filter the result based on original request filters
                return self._apply_individual_filters(coalesced_result, request.kwargs['filters'])
        
        return coalesced_result
    
    def _apply_individual_filters(self, result: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply individual request filters to coalesced result."""
        # This is a simplified implementation
        # In practice, you'd implement proper filtering logic based on your data structure
        filtered_result = result.copy()
        filtered_result['applied_filters'] = filters
        return filtered_result
    
    def _schedule_retry(self, coalesced: CoalescedRequest, error: Exception):
        """Schedule a retry for a failed coalesced request."""
        coalesced.retry_count += 1
        self.metrics['retry_attempts'] += 1
        
        # Exponential backoff
        delay = min(2 ** coalesced.retry_count, 30)  # Max 30 seconds
        
        self.logger.warning(f"Scheduling retry {coalesced.retry_count} for coalesced request in {delay}s")
        
        # Schedule retry
        def retry_execution():
            time.sleep(delay)
            with self.lock:
                self.coalesced_requests[coalesced.request_id] = coalesced
        
        threading.Thread(target=retry_execution, daemon=True).start()
    
    def _handle_final_failure(self, coalesced: CoalescedRequest, error: Exception):
        """Handle final failure after all retries exhausted."""
        self.logger.error(f"Coalesced request failed after {coalesced.max_retries} retries: {error}")
        
        # Set exception for all original requests
        for request in coalesced.similar_requests:
            request.future.set_exception(error)
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return f"coal_{int(time.time() * 1000000)}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get coalescing performance metrics."""
        with self.lock:
            metrics = self.metrics.copy()
            
            # Calculate coalescing ratio
            if metrics['total_requests'] > 0:
                metrics['average_coalescing_ratio'] = (
                    metrics['coalesced_requests'] / metrics['total_requests']
                )
            
            # Add current queue status
            metrics['pending_requests'] = len(self.pending_requests)
            metrics['coalesced_requests_pending'] = len(self.coalesced_requests)
            metrics['coalescing_groups'] = len(self.coalescing_groups)
            
            return metrics
    
    def clear_metrics(self):
        """Clear performance metrics."""
        with self.lock:
            self.metrics = {
                'total_requests': 0,
                'coalesced_requests': 0,
                'api_calls_saved': 0,
                'average_coalescing_ratio': 0,
                'retry_attempts': 0,
                'timeout_errors': 0
            }


# Global coalescer instance (singleton pattern)
_coalescer_instance = None
_coalescer_lock = threading.Lock()


def get_request_coalescer() -> RequestCoalescer:
    """Get the global request coalescer instance (singleton)."""
    global _coalescer_instance
    
    if _coalescer_instance is None:
        with _coalescer_lock:
            if _coalescer_instance is None:
                _coalescer_instance = RequestCoalescer()
                _coalescer_instance.start()
    
    return _coalescer_instance


def shutdown_request_coalescer():
    """Shutdown the global request coalescer instance."""
    global _coalescer_instance
    
    if _coalescer_instance is not None:
        _coalescer_instance.stop()
        _coalescer_instance = None