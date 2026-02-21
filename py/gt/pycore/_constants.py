"""Constants used across modules in this package"""

__all__ = [
    "LOCAL_ROOT",
    "NET_STORAGE_MAP"
]

import ast
import json
import os

from pathlib import Path
from platformdirs import PlatformDirs, PlatformDirsABC



def _getLocalRoot() -> PlatformDirsABC:
    """Get a PlatformDirs object for user local paths.
    
    Test environment for USER_LOCAL_PATH. If defined use path components to 
    derive appauthor and appname. Otherwise set appauther to 'bliz' and 
    appname to the env var value of BL_TEAM.
    
    Returns:
        PlatformDirs: A PlatformDirs object configured for local user paths.

    """
    if os.getenv("USER_LOCAL_PATH"):
        user_local_path = Path(os.getenv("USER_LOCAL_PATH", ""))
        if user_local_path.parts:
            appauthor, appname = user_local_path.parts[-2:]
            return PlatformDirs(appauthor=appauthor, appname=appname)
    return PlatformDirs(appauthor="bliz", appname=os.getenv("BL_TEAM"))


def _getNetStorageMap() -> dict:
    """Get a mapping of UNC paths to drive letters for network storage.
    
    This is used to convert UNC paths to drive letters when possible for better
    compatibility with tools that may not handle UNC paths well.

    The environment variable value is expected to be a JSON object, e.g.::

        {"//server/share": "Z:"}

    Python dict repr (single-quoted strings) is also accepted as a fallback.
    
    Returns:
        dict: A mapping of UNC paths to drive letters.
    
    """
    raw = os.getenv("NET_STORAGE_MAP", "")
    if not raw:
        return {}
    try:
        raw_map = json.loads(raw)
    except json.JSONDecodeError:
        try:
            raw_map = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return {}
    # Normalize keys to the OS path separator so that entries written with
    # forward slashes (e.g. "//server/share") match correctly on Windows.
    return {os.path.normpath(k): v for k, v in raw_map.items()}


LOCAL_ROOT: PlatformDirsABC = _getLocalRoot()
# Root object for local user paths.


NET_STORAGE_MAP: dict = _getNetStorageMap()
# Mapping UNC resource to potential drive letter. Accounting for string casing
# here to make using this more straight forward rather than having to test for
# a string match and not being able to determine the string we need to replace.
