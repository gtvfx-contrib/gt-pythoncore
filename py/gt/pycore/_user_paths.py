"""Helper functions for working with user paths"""

__all__ = [
    "userConfigPathLocal",
    "userDataPathLocal",
    "userLogPathLocal"
]


import logging
from pathlib import Path

from ._constants import LOCAL_ROOT
from ._path_functions import ensurePath


log = logging.getLogger(__name__)



def userConfigPathLocal(appName: str, *subDirs: str) -> Path:
    """Get a local path to where per-user config data can be saved.
    
    The user config is is shared across host machines. The directory will
    be created if needed, and is guaranteed to exist upon return. Do NOT
    make assumptions about where this path is, or try to get the parent
    path(s).
    
    Additional subdirectories can be passed in as positional arguments, which
    will create subdirectories under the config location.
        
    Examples:
        >>> from t2.pycore import userConfigPathLocal
        >>> userConfigPathLocal('Foo', 'Bar')
        Path("%LOCALAPPDATA%/bliz/t2/config/Foo/Bar")
    
    Args:
        appName (str): The associated application or tool name.
        *subDirs (str): Separate string arguments specifying subfolders.
    
    Returns:
        Path: File path object.
        
    """
    result = ensurePath(
        Path(LOCAL_ROOT.user_config_path, "config", appName, *subDirs)
    )
    return result if isinstance(result, Path) else Path(result)
    
    
def userDataPathLocal(appName: str, *subDirs: str) -> Path:
    """Get a local path to where per-user scratch data can be saved.
       
    The directory will be created if needed, and is guaranteed to exist
    upon return.  Do NOT make assumptions about where this path is, or
    try to get the parent path(s).
    
    ``applicationName`` should be a studio-wide unique name used to group
    the directories, and should be named after the application that is
    creating the files (e.g. ``'Aurora'``, ``'Monocle'``, etc).
    
    One or more additional subdirectories may be passed in as positional
    arguments, which will create subdirectories under the main application
    location.
    
    Examples:
        >>> from t2.pycore import userDataPathLocal
        >>> userDataPathLocal('wowcreator', 'scripts', 'awesome')
        Path("%LOCALAPPDATA%/bliz/t2/data/wowcreator/scripts/awesome")
        
    Args:
        appName (str): The associated application or tool name.
        *subDirs (str): Separate string arguments specifying subfolders.
        
    Returns:
        Path: File path object.
        
    """
    result = ensurePath(
        Path(LOCAL_ROOT.user_data_path, "data", appName, *subDirs)
    )
    return result if isinstance(result, Path) else Path(result)

    
def userLogPathLocal(appName: str, *subDirs: str) -> Path:
    """Get a local path to where per-user logs can be saved.
    
    The directory will be created if needed, and is guaranteed to exist
    upon return.  Do NOT make assumptions about where this path is, or
    try to get the parent path(s).
    
    ``applicationName`` should be a studio-wide unique name used to group
    the directories, and should be named after the application that is
    creating the files (e.g. ``'Aurora'``, ``'Monocle'``, etc).
    One or more additional subdirectories may be passed in as positional
    arguments, which will create subdirectories under the main application
    location.
   
    Examples:
        >>> from t2.pycore import userLogPathLocal
        >>> userLogPathLocal('wowcreator', 'restapi')
        Path("%LOCALAPPDATA%/bliz/t2/log/wowcreator/restapi")
    
    Args:
        appName (str): The associated application or tool name.
        *subDirs (str): Separate string arguments specifying subfolders.
    
    Returns:
        Path: File path object.
    
    """
    result = ensurePath(
        Path(LOCAL_ROOT.user_log_path, "log", appName, *subDirs)
    )
    return result if isinstance(result, Path) else Path(result)