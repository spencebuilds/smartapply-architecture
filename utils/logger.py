"""
Logging configuration and utilities.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str | None = None, log_file: str | None = None, log_level: str | None = None) -> logging.Logger:
    """Set up and configure logger for the application."""
    
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    log_file = log_file or os.getenv("LOG_FILE", "job_application_system.log")
    
    # Create logger
    logger_name = name or "job_application_system"
    logger = logging.getLogger(logger_name)
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create file handler for {log_file}: {str(e)}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logger initialized - Level: {log_level}, File: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


class ContextLogger:
    """Context manager for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, context: str):
        self.logger = logger
        self.context = context
        self.original_name = logger.name
    
    def __enter__(self):
        # Create a new logger with context in the name
        self.context_logger = logging.getLogger(f"{self.original_name}.{self.context}")
        self.context_logger.setLevel(self.logger.level)
        
        # Copy handlers from original logger
        for handler in self.logger.handlers:
            self.context_logger.addHandler(handler)
        
        self.context_logger.propagate = False
        return self.context_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up handlers
        for handler in self.context_logger.handlers[:]:
            self.context_logger.removeHandler(handler)


def log_execution_time(logger: logging.Logger):
    """Decorator to log function execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                duration = datetime.now() - start_time
                logger.debug(f"Completed {func.__name__} in {duration.total_seconds():.2f} seconds")
                return result
            except Exception as e:
                duration = datetime.now() - start_time
                logger.error(f"Error in {func.__name__} after {duration.total_seconds():.2f} seconds: {str(e)}")
                raise
                
        return wrapper
    return decorator
