"""Helper functions for working with users"""
import os

from typing import Optional

__all__ = [
    "getUserInfo",
    "getUserRealName"
]


def getUserInfo(username: Optional[str] = None, level: int = 2) -> dict:
    """Get the win32net.NetUserGetInfo dict for the supplied username.
    
    Info:
        dict = win32net.NetUserGetInfo(server, username , level)
    
    Args:
        username (str, optional): A valid LDAP username. If unsupplied will
            get the current runtime username.
        level (int, 0-4): The level of info to collect in the user info dict.
            Higher numbers return more info. 
    
    Returns:
        dict
    
    """
    # pylint: disable=C0415
    # Isolating import as needed
    import win32net
    # pylint: enable=C0415
    
    if not username:
        username = os.getenv("USERNAME", "")

    return win32net.NetUserGetInfo(win32net.NetGetAnyDCName(),
                                   username,
                                   level)


def getUserRealName(username: Optional[str] = None) -> Optional[str]:
    """Get the real name from the supplied username
    
    info:
        dict = NetUserGetInfo(server, username , level)
    
    Args:
        username (str, optional): A valid LDAP username. If unsupplied will
            get the current runtime username.
    
    Returns:
        str: First and Last name
    
    Raises:
        pywintypes.error: If username not valid
    
    """
    user_info = getUserInfo(username)
    return user_info.get("full_name")
