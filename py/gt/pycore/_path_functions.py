"""Helper functions for working with paths"""

__all__ = [
    "copytreeWithProgress",
    "extendedCharacterPath",
    "getActiveDriveMappings",
    "initializeNetworkShare",
    "makeRelativePath",
    "netFileExists",
    "ensurePath",
    "explorePath",
    "makeLegalDirectoryName",
    "uncToMappedDrive"
]

import ctypes
import logging
import os
import re
import shutil
import string
import subprocess

from typing import Optional, Callable, Union, overload
from pathlib import Path

log = logging.getLogger(__name__)

from ._constants import NET_STORAGE_MAP
from ._decorators import timeIt



def extendedCharacterPath(path: str) -> str:
    """Add the long path prefix for Windows.
    
    Args:
        path (str): valid path string.
        
    Returns:
        str: Formatted path with extended characters
    
    """
    if os.name == 'nt' and not path.startswith("\\\\?\\"):
        if path.startswith("\\\\"):
            return os.path.abspath(path).replace("\\\\", "\\\\?\\UNC\\")
        return "\\\\?\\" + os.path.abspath(path)
    return path


def initializeNetworkShare(path: str) -> bool:
    """Initialize a Windows network share to make it accessible.

    On Windows, network shares (UNC paths) may not be immediately accessible
    until they are first accessed, similar to browsing them in Windows Explorer.
    This function probes the network share to force Windows to establish the
    connection, making subsequent file operations succeed.

    Args:
        path (str): A file or directory path on a network share (UNC path or
            mapped drive that resolves to UNC).

    Returns:
        bool: True if the network share was successfully initialized or is
            already accessible, False if initialization failed.

    Examples:
        >>> initializeNetworkShare(r"\\\\server\\share\\path\\to\\file.txt")
        True
        >>> # W: is mapped to UNC
        >>> initializeNetworkShare(r"W:\\data\\file.txt")
        True

    """
    try:
        # Convert to Path object and normalize
        path_obj = Path(path)
        
        if not path_obj.parts:
            log.warning(f"Path does not appear to be a network path: {path}")
            return False
        
        # Extract the network share root (\\server\share)
        is_unc = (
            path_obj.is_absolute() 
            and len(path_obj.parts) >= 2 
            and path_obj.parts[0].startswith("\\\\")
        )
        if is_unc and path_obj.parts:
            # UNC path - construct share root from first two parts
            # Path.parts for UNC: ('\\\\server\\share', 'subfolder', 'file.txt')
            share_root = Path(path_obj.parts[0])
        else:
            share_root = Path(path_obj.anchor)
        
        # Probe the share root to force Windows to establish the connection
        # Using iterdir() with exception handling to gracefully handle failures
        list(share_root.iterdir())
        return True
        
    except (OSError, ValueError, IndexError):
        # Failed to initialize - could be offline, authentication issue, etc.
        log.warning(f"Failed to initialize network share for path: {path}")
        return False
    
    
def netFileExists(filepath: str) -> bool:
    """Check if a file exists on a network share.
    
    This function handles network share initialization before checking for file
    existence. On Windows, network shares may not be accessible until they are
    first accessed. This function ensures the share is initialized before
    checking if the file exists.
    
    Args:
        filepath (str): The path to the file to check (UNC path or mapped drive).
    
    Returns:
        bool: True if the file exists and is accessible, False otherwise.
    
    Examples:
        >>> netFileExists(r"\\\\server\\share\\data\\config.json")
        True
        >>> netFileExists(r"W:\\assets\\image.png")
        False
    
    """
    if not initializeNetworkShare(filepath):
        return False
    return os.path.exists(filepath)


def makeRelativePath(path: str, relative_token: str="") -> str:
    """Concatenate a path relative to the relative_token arg.
    
    Args:
        path (str): Any system path
        relative_token (str): A folder name within path
    
    Returns:
        str
    
    """
    rel = "...\\"
    path = os.path.normpath(path)
    tokens = path.split(os.sep)
    
    if relative_token == "":
        tokens[0] = "..."
        return os.path.join(*tokens)
    
    if relative_token in tokens:
        token_index = tokens.index(relative_token)
    else:
        token_index = 0
        
    rel_tokens = tokens[token_index:]
    return os.path.join(rel, *rel_tokens)


@overload
def ensurePath(directory: str) -> str: ...

@overload
def ensurePath(directory: Path) -> Path: ...
        
def ensurePath(directory: Union[str, Path]) -> Union[str, Path]:
    """Function to ensure a directory exists without raising an exception.

    Args:
        directory (str | Path): directory path to create. Can be a filepath, and this
            will ensure the path up to the filename.

    Returns:
        str | Path: supplied directory path, returns same type as input

    """
    _directory = directory if isinstance(directory, Path) else Path(directory)
    
    if _directory.suffix: 
        # If the path has a file suffix, we want to ensure the parent directory exists
        _directory = _directory.parent
    
    _directory.mkdir(parents=True, exist_ok=True)

    return directory


def explorePath(osPath: str) -> None:
    """Open an explorer window to the supplied path.

    If the supplied path is a file, its parent directory will be opened.

    Args:
        osPath (str): The file or directory path to open.

    Returns:
        None

    Raises:
        FileNotFoundError: If the supplied path does not exist.
        OSError: If the platform is not Windows.
    """
    if os.name != "nt":
        raise OSError("Explorer window can only be opened on Windows.")

    if not os.path.exists(osPath):
        raise FileNotFoundError(f"Supplied path does not exist: {osPath}")

    # Normalize and resolve the path
    path = os.path.abspath(osPath)
    if os.path.isfile(path):
        # If it's a file, open its parent directory and select the file
        subprocess.run(["explorer", "/select,", path], check=False)
    else:
        # If it's a directory, open it
        subprocess.run(["explorer", path], check=False)
        
        
def makeLegalDirectoryName(string: str, 
                           rem_strings: Optional[list[str]] = None, 
                           max_chars: int = 0) -> str:
    """Conforms a supplied string to a string that is valid as a directory name.
    
    Options for removing subsring components supplied by rem_strings arg.
    Optionally, set a maximum character limit to return.
    
    Args:
        string (str): Base string to operate on.
        rem_strings (list of str, optional): List of substrings to remove from
            base string.
        max_chars (int, optional): Set a maximum limit on the number of characters
            in the returned string.
    
    Returns:
        str
    
    """
    conformed_str = re.sub(r'\W+', '_', string)
    if rem_strings:
        for rem_str in rem_strings:
            conformed_str = conformed_str.replace(rem_str, "")
            
    if max_chars:
        conformed_str = conformed_str[:max_chars]
        
    return conformed_str


def getActiveDriveMappings() -> dict[str, str]:
    """Query Windows for currently active UNC-to-drive-letter mappings.

    Uses the Win32 ``WNetGetConnectionW`` API to enumerate all drive letters
    and resolve any that are mapped network drives.

    Returns:
        dict[str, str]: Mapping of normalised UNC share root to drive letter,
            e.g. ``{'\\\\\\\\server\\\\share': 'Z:'}``.  Returns an empty dict on
            non-Windows platforms or if the query fails.

    """
    if os.name != 'nt':
        return {}
    try:
        mpr = ctypes.windll.mpr  # type: ignore[attr-defined]
        result: dict[str, str] = {}
        buf = ctypes.create_unicode_buffer(1024)
        buf_size = ctypes.c_ulong(1024)
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            buf_size.value = 1024
            ret = mpr.WNetGetConnectionW(drive, buf, ctypes.byref(buf_size))
            if ret == 0:  # NO_ERROR
                unc = os.path.normpath(buf.value)
                result[unc] = drive
        return result
    except Exception:  # pylint: disable=broad-except
        log.debug("WNetGetConnectionW query failed", exc_info=True)
        return {}


def uncToMappedDrive(path: str) -> str:
    """Convert a UNC path to a mapped drive path if a mapping exists.

    Checks the static ``NET_STORAGE_MAP`` configuration first, then falls back
    to querying Windows for any currently active drive mappings.

    Args:
        path (str): The UNC path to convert.

    Returns:
        str: The mapped drive path if a mapping exists, otherwise the original
            path unchanged.

    """
    path = os.path.normpath(path)

    if not path.startswith("\\\\"):
        # Not a UNC path – nothing to convert.
        return path

    # 1. Check the static config map.
    for unc, driveletter in NET_STORAGE_MAP.items():
        if path.startswith(unc):
            return path.replace(unc, driveletter, 1)

    # 2. Fall back to currently active Windows drive mappings.
    for unc, driveletter in getActiveDriveMappings().items():
        if path.startswith(unc):
            return path.replace(unc, driveletter, 1)

    return path


@timeIt
def copytreeWithProgress(src: str, dst: str, 
                         symlinks: bool = False, 
                         ignore: Optional[Callable[[str, list[str]], list[str]]] = None) -> None:
    """Copy a directory tree with progress bar.
    
    Args:
        src (str): The source directory to copy from.
        dst (str): The destination directory to copy to.
        symlinks (bool, optional): If True, symbolic links will be copied as links.
            Default is False.
        ignore (Callable, optional): A callable that takes a directory path and a list
            of directory contents, and returns a list of names to ignore.
    
    Returns:
        None
        
    """
    # pylint: disable=C0415
    # Isolating import as needed
    from tqdm import tqdm
    import win32com.client
    # pylint: enable=C0415
    
    # Safeguard against file paths longer than the 260 character limit in NFS
    src = extendedCharacterPath(src)
    dst = extendedCharacterPath(dst)
    
    # Get the total size of the files to copy
    print(f"Analyzing files in {src}...")
    file_system_object = win32com.client.Dispatch("Scripting.FileSystemObject")
    folder = file_system_object.GetFolder(src)
    total_size = folder.Size
    
    print(f"\nCopying files to {dst}...")
    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
        def _copy(src, dst):
            shutil.copy2(src, dst)
            pbar.update(os.path.getsize(src))

        shutil.copytree(src, dst, symlinks=symlinks, ignore=ignore, copy_function=_copy)
        