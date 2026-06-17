"""Helper functions for any win32 apis"""
from __future__ import annotations

__all__ = [
    "getFileVersion"
]

import os
import win32api
from pathlib import Path
from typing import Optional, Union
import pywintypes

from ._data_classes import FileVersion


def getFileVersion(file_path: Union[str, os.PathLike, Path]) -> Optional[FileVersion]:
    """Get the version number from a Windows executable file.
    
    Args:
        file_path: The full path to the executable file as string, os.PathLike, or Path object.
        
    Returns:
        FileVersion: A FileVersion object containing version info, or None if error.
    """
    # Convert Path object to string for compatibility
    file_path_str = os.fspath(file_path)
    
    if not os.path.exists(file_path_str):
        print(f"Error: File not found at {file_path_str}")
        return None

    try:
        # GetFileVersionInfo returns a dictionary-like object with version details
        info = win32api.GetFileVersionInfo(file_path_str, '\\')
        
    except pywintypes.error as e: # type: ignore
        # Win32 API errors (file access, invalid file format, etc.)
        error_code = e.winerror if hasattr(e, 'winerror') else 'unknown'
        print(f"Win32 API error getting version info for {file_path_str}: {e} (code: {error_code})")
        return None
    except PermissionError as e:
        # File access permission denied
        print(f"Permission denied accessing {file_path_str}: {e}")
        return None
    except OSError as e:
        # File system errors (file locked, network issues, etc.)
        print(f"OS error accessing {file_path_str}: {e}")
        return None

    try:
        # The version is composed of two 32-bit integers: FileVersionMS and FileVersionLS
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        
        # Extract the version parts using HIWORD and LOWORD
        major = win32api.HIWORD(ms)
        minor = win32api.LOWORD(ms)
        subminor = win32api.HIWORD(ls)
        revision = win32api.LOWORD(ls)

        return FileVersion(
            version=".".join(map(str, (major, minor, subminor, revision))),
            major=major,
            minor=minor,
            subminor=subminor,
            revision=revision
        )
        
    except KeyError as e:
        # Version info structure doesn't contain expected keys
        print(f"Version info missing expected key for {file_path_str}: {e}")
        return None
    except (TypeError, ValueError) as e:
        # Issues with data type conversion or invalid version data
        print(f"Invalid version data in {file_path_str}: {e}")
        return None
    