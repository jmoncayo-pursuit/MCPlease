"""Logging utilities for MCPlease MVP."""

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str, level: str = "INFO", log_file: Optional[Path] = None) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Set level
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger