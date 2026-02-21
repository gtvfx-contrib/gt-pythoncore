"""Metaclass for creating singleton classes"""

__all__ = [
    "Singleton"
]

import threading
from typing import Dict, Any


class Singleton(type):
    """Thread-safe metaclass for creating singleton classes.
    
    Apply this metaclass to a class to ensure that only one instance of the
    class will exist. The singleton instance is created on first instantiation
    and subsequent calls return the same instance without re-running __init__.
    
    This implementation is thread-safe using double-checked locking pattern.
    
    Examples:
    - Basic singleton usage:
        ```python
        from t2.metaclasses import Singleton
        
        class DatabaseConnection(metaclass=Singleton):
            def __init__(self):
                # This only runs once, even if called multiple times
                self.connection = self._create_connection()
                self.query_count = 0
        
        # First call creates the instance
        db1 = DatabaseConnection()
        db1.query_count = 5
        
        # Second call returns the same instance
        db2 = DatabaseConnection()
        print(db2.query_count)  # 5
        print(db1 is db2)       # True
        ```  
            
    - Force re-initialization:
        ```python
        # Force re-initialization with _reinit parameter
        db3 = DatabaseConnection(_reinit=True)
        print(db3.query_count)  # 0 (re-initialized)
        ```
    
    Args:
        _reinit (bool): If True, forces re-initialization of the singleton
            instance. Default is False.
    
    """
    _instances: Dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args: Any, _reinit: bool = False, **kwargs: Any) -> Any:
        """Create or return the singleton instance.
        
        Args:
            *args: Positional arguments passed to __init__.
            _reinit: If True, forces creation of a new instance. Keyword-only.
            **kwargs: Keyword arguments passed to __init__.
        
        Returns:
            The singleton instance of the class.
        
        """
        if cls not in Singleton._instances or _reinit:
            with Singleton._lock:
                # Double-checked locking pattern
                if cls not in Singleton._instances or _reinit:
                    instance = super().__call__(*args, **kwargs)
                    Singleton._instances[cls] = instance
        return Singleton._instances[cls]
    