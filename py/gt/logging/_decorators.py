"""Logging decorators"""
import functools
import inspect
import os

from gt.pycore import makeRelativePath


__all__ = [
    "logFunc",
]



def logFunc(force=False):
    """Logs the call to the wrapped func with all args and kwargs"""
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            _log_debug = os.getenv("LOG_DEBUG", "")
            if force or _log_debug and _log_debug.lower() in ("1", "true"):
                from_module = inspect.stack()[1][1]
                
                if from_module == '<stdin>':
                    # This means we're in a python REPL
                    module_path = from_module
                else:
                    module_path = makeRelativePath(from_module, relative_token="t2")
                
                msg = f"call: {module_path} | {func.__name__}("
                if args:
                    msg = f"{msg}{str(args)[1:-2]}"
                if kwargs:
                    if args:
                        # If we had args add a ',' before kwargs
                        msg += ", "
                    msg = f"{msg}{', '.join([f'{k}={v}' for k,v in kwargs.items()])}"
                msg += ")"
                print(msg)
            return func(*args, **kwargs)
        return _wrapper
    return _decorator
