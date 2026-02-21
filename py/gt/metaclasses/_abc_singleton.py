"""Singleton Abstract Base Class metaclass"""
from abc import ABCMeta
import threading
from typing import Dict, Any


__all__ = [
    "ABCSingleton"
]


class ABCSingleton(ABCMeta):
    """Thread-safe metaclass combining Abstract Base Class with Singleton pattern.
    
    This metaclass allows you to create abstract base classes that are also
    singletons. Each concrete implementation will have only one instance, and
    abstract methods must be implemented by subclasses.
    
    The singleton instance is created on first instantiation and subsequent
    calls return the same instance without re-running __init__.
    
    This implementation is thread-safe using double-checked locking pattern.
    
    Examples:
    - Basic abstract singleton usage::
        ```python
        from abc import abstractmethod
        from t2.abstractclasses import ABCSingleton
        
        class DatabaseInterface(metaclass=ABCSingleton):
            @abstractmethod
            def connect(self):
                # Connect to database
                pass
            
            @abstractmethod
            def query(self, sql):
                # Execute query
                pass
        
        class MySQLDatabase(DatabaseInterface):
            def __init__(self):
                # Only runs once per class
                self.connection = None
                self.query_count = 0
            
            def connect(self):
                self.connection = "MySQL connected"
            
            def query(self, sql):
                self.query_count += 1
                return f"Executing: {sql}"
        
        # First call creates the instance
        db1 = MySQLDatabase()
        db1.query_count = 5
        
        # Second call returns the same instance
        db2 = MySQLDatabase()
        print(db2.query_count)  # 5
        print(db1 is db2)        # True
        ```
        
    - Force re-initialization::
        ```python
        # Force re-initialization with _reinit parameter
        db3 = MySQLDatabase(_reinit=True)
        print(db3.query_count)  # 0 (re-initialized)
        ```
    
    Args:
        _reinit (bool): If True, forces re-initialization of the singleton
            instance. Keyword-only argument. Default is False.
    
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
        if cls not in ABCSingleton._instances or _reinit:
            with ABCSingleton._lock:
                # Double-checked locking pattern
                if cls not in ABCSingleton._instances or _reinit:
                    instance = super().__call__(*args, **kwargs)
                    ABCSingleton._instances[cls] = instance
        return ABCSingleton._instances[cls]
    