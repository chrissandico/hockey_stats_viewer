"""
Retry Logic with Exponential Backoff Implementation

This module provides retry mechanisms with exponential backoff and jitter
to handle transient failures gracefully and prevent thundering herd problems.

Requirements addressed: 2.2, 2.4
"""

import time
import random
import logging
import asyncio
from typing import Callable, Any, Optional, Type, Tuple, Union
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3                    # Maximum number of retry attempts
    base_delay: float = 1.0                 # Base delay in seconds
    max_delay: float = 30.0                 # Maximum delay in seconds
    exponential_base: float = 2.0           # Exponential backoff multiplier
    jitter: bool = True                     # Add random jitter to prevent thundering herd
    jitter_range: float = 0.1               # Jitter range (±10% by default)


class RetryableError(Exception):
    """Base class for errors that should trigger retries"""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should not trigger retries"""
    pass


class RetryManager:
    """
    Retry manager with exponential backoff and jitter.
    
    Handles transient failures by retrying operations with increasing delays,
    while preventing thundering herd problems through jitter.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        
        # Default retryable exceptions (can be overridden)
        self.retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,  # Network-related errors
        )
        
        # Default non-retryable exceptions
        self.non_retryable_exceptions = (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        )
        
        logger.info(f"Retry manager initialized with config: {self.config}")
    
    def retry(self, 
              func: Callable, 
              *args, 
              retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
              non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
              **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            retryable_exceptions: Tuple of exception types that should trigger retries
            non_retryable_exceptions: Tuple of exception types that should not trigger retries
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: The last exception if all retries are exhausted
        """
        retryable = retryable_exceptions or self.retryable_exceptions
        non_retryable = non_retryable_exceptions or self.non_retryable_exceptions
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.config.max_retries} for {func.__name__}")
                
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Function {func.__name__} succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a non-retryable error
                if isinstance(e, non_retryable):
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                
                # Check if this is a retryable error
                if not isinstance(e, retryable):
                    logger.error(f"Non-retryable error type in {func.__name__}: {type(e).__name__}: {e}")
                    raise
                
                # If this is the last attempt, don't wait
                if attempt == self.config.max_retries:
                    logger.error(f"All retry attempts exhausted for {func.__name__}: {e}")
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                
                time.sleep(delay)
        
        # All retries exhausted, raise the last exception
        raise last_exception
    
    async def async_retry(self, 
                         func: Callable, 
                         *args, 
                         retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
                         non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
                         **kwargs) -> Any:
        """
        Execute an async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            retryable_exceptions: Tuple of exception types that should trigger retries
            non_retryable_exceptions: Tuple of exception types that should not trigger retries
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: The last exception if all retries are exhausted
        """
        retryable = retryable_exceptions or self.retryable_exceptions
        non_retryable = non_retryable_exceptions or self.non_retryable_exceptions
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Async retry attempt {attempt}/{self.config.max_retries} for {func.__name__}")
                
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Async function {func.__name__} succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a non-retryable error
                if isinstance(e, non_retryable):
                    logger.error(f"Non-retryable error in async {func.__name__}: {e}")
                    raise
                
                # Check if this is a retryable error
                if not isinstance(e, retryable):
                    logger.error(f"Non-retryable error type in async {func.__name__}: {type(e).__name__}: {e}")
                    raise
                
                # If this is the last attempt, don't wait
                if attempt == self.config.max_retries:
                    logger.error(f"All async retry attempts exhausted for {func.__name__}: {e}")
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                logger.warning(f"Async attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                
                await asyncio.sleep(delay)
        
        # All retries exhausted, raise the last exception
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_amount = delay * self.config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay += jitter
            
            # Ensure delay is not negative
            delay = max(0.1, delay)
        
        return delay
    
    def with_retries(self, 
                    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
                    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None):
        """
        Decorator for adding retry logic to functions.
        
        Args:
            retryable_exceptions: Tuple of exception types that should trigger retries
            non_retryable_exceptions: Tuple of exception types that should not trigger retries
            
        Returns:
            Decorated function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.retry(
                    func, 
                    *args, 
                    retryable_exceptions=retryable_exceptions,
                    non_retryable_exceptions=non_retryable_exceptions,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """Get retry manager statistics"""
        return {
            'config': {
                'max_retries': self.config.max_retries,
                'base_delay': self.config.base_delay,
                'max_delay': self.config.max_delay,
                'exponential_base': self.config.exponential_base,
                'jitter': self.config.jitter,
                'jitter_range': self.config.jitter_range
            },
            'retryable_exceptions': [exc.__name__ for exc in self.retryable_exceptions],
            'non_retryable_exceptions': [exc.__name__ for exc in self.non_retryable_exceptions]
        }


class GoogleSheetsRetryManager(RetryManager):
    """
    Specialized retry manager for Google Sheets API calls.
    
    Provides Google Sheets-specific retry configuration and error handling.
    """
    
    def __init__(self):
        # Google Sheets specific configuration
        config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            jitter_range=0.2  # 20% jitter for API calls
        )
        super().__init__(config)
        
        # Google Sheets specific retryable exceptions
        self.retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            # Add Google API specific exceptions here
            # gspread.exceptions.APIError,  # Would need to import gspread
        )
        
        # Google Sheets specific non-retryable exceptions
        self.non_retryable_exceptions = (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            # Add Google API specific exceptions here
            # gspread.exceptions.SpreadsheetNotFound,  # Would need to import gspread
        )
    
    def retry_sheets_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a Google Sheets API call with retry logic.
        
        Provides additional logging and error context for Sheets API calls.
        """
        try:
            logger.debug(f"Executing Google Sheets API call: {func.__name__}")
            return self.retry(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Google Sheets API call failed after all retries: {func.__name__} - {e}")
            raise


# Convenience function for quick retry setup
def with_exponential_backoff(max_retries: int = 3, 
                           base_delay: float = 1.0, 
                           max_delay: float = 30.0):
    """
    Convenience decorator for adding exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Decorator function
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )
    retry_manager = RetryManager(config)
    return retry_manager.with_retries()