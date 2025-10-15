"""
Circuit Breaker Pattern Implementation for Google Sheets API

This module implements the circuit breaker pattern to handle failures gracefully
and prevent cascading failures when the Google Sheets API is unavailable.

Requirements addressed: 2.2, 2.4
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing fast, not calling service
    HALF_OPEN = "HALF_OPEN"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: int = 60          # Seconds to wait before trying again
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: float = 30.0               # Request timeout in seconds


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures.
    
    The circuit breaker monitors failures and prevents calls to a failing service,
    allowing it time to recover while providing fast failure responses.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.lock = Lock()
        
        logger.info(f"Circuit breaker initialized with config: {self.config}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitBreakerError: When circuit is open
            Exception: Original exception from the function
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    logger.warning("Circuit breaker is OPEN - failing fast")
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Service unavailable. "
                        f"Will retry after {self.config.recovery_timeout} seconds."
                    )
        
        try:
            # Execute the function with timeout
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Record success
            self._on_success(duration)
            return result
            
        except Exception as e:
            # Record failure
            self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt service recovery"""
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _on_success(self, duration: float):
        """Handle successful function execution"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.info(f"Circuit breaker success {self.success_count}/{self.config.success_threshold}")
                
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker CLOSED - service recovered")
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
            
            logger.debug(f"Function executed successfully in {duration:.2f}s")
    
    def _on_failure(self, exception: Exception):
        """Handle failed function execution"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(f"Circuit breaker failure {self.failure_count}/{self.config.failure_threshold}: {exception}")
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN - service still failing")
                
            elif (self.state == CircuitState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                # Too many failures, open the circuit
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker OPEN - failure threshold exceeded")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state information"""
        with self.lock:
            return {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time,
                'time_since_last_failure': time.time() - self.last_failure_time if self.last_failure_time else 0,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'success_threshold': self.config.success_threshold,
                    'timeout': self.config.timeout
                }
            }
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = 0
            logger.info("Circuit breaker manually reset to CLOSED")
    
    def force_open(self):
        """Manually force the circuit breaker to OPEN state"""
        with self.lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()
            logger.warning("Circuit breaker manually forced to OPEN")


class GoogleSheetsCircuitBreaker(CircuitBreaker):
    """
    Specialized circuit breaker for Google Sheets API calls.
    
    Provides Google Sheets-specific configuration and error handling.
    """
    
    def __init__(self):
        # Google Sheets specific configuration
        config = CircuitBreakerConfig(
            failure_threshold=3,        # Lower threshold for API calls
            recovery_timeout=30,        # Shorter recovery time
            success_threshold=2,        # Fewer successes needed
            timeout=20.0               # API call timeout
        )
        super().__init__(config)
    
    def call_sheets_api(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a Google Sheets API call through the circuit breaker.
        
        Provides additional logging and error context for Sheets API calls.
        """
        try:
            logger.debug(f"Calling Google Sheets API: {func.__name__}")
            return self.call(func, *args, **kwargs)
        except CircuitBreakerError:
            logger.error("Google Sheets API unavailable - circuit breaker is open")
            raise
        except Exception as e:
            logger.error(f"Google Sheets API call failed: {func.__name__} - {e}")
            raise