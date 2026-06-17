
"""General functions for working with local system data"""

__all__ = [
    "findExecutable",
    "getNumCores"
]

import os
import shutil
import subprocess

from typing import Optional


def findExecutable(name: str) -> Optional[str]:
    """Locate an executable by name, returning its full path.

    Resolution order:

    1. ``shutil.which`` — searches ``PATH`` and honours ``PATHEXT`` on Windows,
       covering ``.exe``, ``.cmd``, ``.bat`` etc. with no process overhead.
    2. Windows ``where`` command — fallback that can surface executables
       registered outside the standard ``PATH`` (e.g. App Execution Aliases).

    Args:
        name (str): The executable name to search for, e.g. ``'7z'``,
            ``'robocopy'``, ``'python'``.

    Returns:
        Optional[str]: Absolute path to the executable, or ``None`` if not found.

    Examples:
        >>> findExecutable('robocopy')
        'C:\\Windows\\system32\\Robocopy.exe'
        >>> findExecutable('7z')
        'C:\\Program Files\\7-Zip\\7z.exe'
        >>> findExecutable('nonexistent')
        None

    """
    # shutil.which handles PATH + PATHEXT with no subprocess overhead.
    result = shutil.which(name)
    if result:
        return os.path.abspath(result)

    # Fallback: Windows `where` can find executables that shutil.which misses
    # (e.g. App Execution Aliases, per-user installs).
    if os.name == 'nt':
        try:
            proc = subprocess.run(
                ["where", name],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if proc.returncode == 0:
                # `where` may return multiple matches; take the first.
                first_line = proc.stdout.decode().splitlines()[0].strip()
                if first_line:
                    return first_line
        except OSError:
            pass

    return None


def getNumCores():
    """Get the number of CPU cores available on the local system.

    Returns:
        int: The number of CPU cores.
        
    """
    # pylint: disable=C0415
    # Isolating import as needed
    import multiprocessing
    # pylint: enable=C0415
    
    return multiprocessing.cpu_count()
