"""Helper functions for general logging operations"""

__all__ = [
    "setLevel"
]


from typing import Optional, Union

import logging

log = logging.getLogger(__name__)


def setLevel(level: Union[str, int], name: Optional[str] = None) -> None:
    """Set the logging output level for easier debugging.
    
    Configures the logging output level globally or for a specific named logger.
    Accepts both string names (case-insensitive) and integer level constants.
    
    NOTE: Calling this function multiple times may add multiple handlers. If you
    set DEBUG and then INFO, you may still see DEBUG messages. To fully reset
    logging, you may need to restart your Python session. For one-time debugging,
    set the level once at the start.
    
    Args:
        level: Log level as string ('debug', 'info', 'warning'/'warn') or 
            integer constant (logging.DEBUG, logging.INFO, logging.WARNING).
        name: Optional logger name. If None, sets the root logger level.
            Examples: 'p4', 't2.preview', __name__
    
    Returns:
        None
    
    Examples:
        ```python
        >>> # Set global logging to DEBUG (do this once at session start)
        >>> setLevel('debug')
        
        >>> # Set specific logger to INFO
        >>> setLevel('info', name='p4')
        
        >>> # Use integer constant
        >>> setLevel(logging.WARNING)
        
        >>> # Set current module's logger to DEBUG
        >>> setLevel('debug', name=__name__)
        
        >>> # For debugging workflow:
        >>> # 1. Start fresh Python session
        >>> # 2. Import and set level once
        >>> from gt.logging import setLevel
        >>> setLevel('debug')  # See all debug messages
        >>> # 3. Do your debugging work
        >>> # 4. To reduce verbosity, restart session and set to 'info'
        ```
    
    """
    # Map string levels to logging constants
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
    }
    
    # Handle string input
    if isinstance(level, str):
        mapped_level = level_map.get(level.lower())
        if not mapped_level:
            valid_levels = ', '.join(f"'{k}'" for k in level_map)
            log.warning(
                f"Invalid log level '{level}'. Valid levels: {valid_levels} "
                f"or integer constants (logging.DEBUG, logging.INFO, logging.WARNING)"
            )
            return
        level = mapped_level
    
    # Configure the target logger and ensure it has at least one StreamHandler
    target_logger = logging.getLogger(name) if name else logging.getLogger()
    target_logger.setLevel(level)
    if not target_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        target_logger.addHandler(handler)
    else:
        for handler in target_logger.handlers:
            handler.setLevel(level)
    log.info(f"Set log level for '{name or 'root'}' to {level}")
        