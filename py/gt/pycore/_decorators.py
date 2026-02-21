"""General python utility decorators"""

__all__ = [
    "conformPath",
    "normalizePaths",
    "PathStyle",
    "timeIt"
]

import os
import inspect
import time

from enum import Enum
from functools import wraps
from typing import Callable, Union

from ._str_functions import formatTime


class PathStyle(Enum):
    """Enum to represent different path styles."""
    WINDOWS = "windows"
    UNIX = "unix"


def conformPath(style: Union[PathStyle, Callable, str]) -> Callable:
    """Decorator to conform the return value of a function to a path style.

    Args:
        style (PathStyle or Callable or Str): A PathStyle enum specifying the 
            desired path style ("windows" or "unix") or a callable that returns 
            the desired style dynamically or a string matching a PathStyle 
            value. The callable type is for use when decorating a method in a 
            class and passing the style value in from a class or instance 
            attribute using a lambda or similar callable.

    Returns:
        Callable: A decorator function that, when applied to another function,
        wraps that function and ensures its return value (assumed to be a path 
        string) is conformed to the specified path style (PathStyle.WINDOWS or 
        PathStyle.UNIX)
        
    """
    def decorator(func):
        @wraps(func)
        def _wrapFunction(*args, **kwargs):
            # Call the original function
            result = func(*args, **kwargs)

            # Ensure the result is a string (assumed to be a path)
            if not isinstance(result, str):
                raise ValueError(f"Expected the return value to be a string, got {type(result)}")

            # Determine the style
            if callable(style):
                # Pass `self` if the callable expects it
                path_style = style(args[0]) if len(args) > 0 else style()
            elif isinstance(style, (PathStyle, str)):
                path_style = style
            else:
                raise ValueError(f"Invalid style type: {type(style)}. "
                                 "Must be a PathStyle, string or callable.")
            
            # Conform the path to the specified style
            if path_style in (PathStyle.WINDOWS, PathStyle.WINDOWS.value):
                conformed_path = result.replace("/", "\\")
            elif path_style in (PathStyle.UNIX, PathStyle.UNIX.value):
                conformed_path = result.replace("\\", "/")
            else:
                raise ValueError(f"Invalid style '{path_style}'. Use 'windows' or 'unix'.")

            return conformed_path
        return _wrapFunction
    return decorator


def normalizePaths(*path_params: str) -> Callable:
    """Decorator to automatically normalize specified path parameters"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature to map parameters
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Normalize specified path parameters
            for param in path_params:
                if param in bound_args.arguments and bound_args.arguments[param]:
                    bound_args.arguments[param] = os.path.normpath(bound_args.arguments[param])
            
            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator


def timeIt(func: Callable) -> Callable:
    """Time the execution of a function

    Args:
        func (function): The function to time

    Prints:
        Formatted string of elapsed time.
        
    See Also:
        formatTime

    """
    @wraps(func)
    def _wrapFunction(*args, **kwargs):
        start_time = time.time()
        out = func(*args, **kwargs)
        perf_time = time.time() - start_time
        print(f"!-- {func.__name__} execution time: {formatTime(perf_time)} --!")
        return out
    return _wrapFunction
