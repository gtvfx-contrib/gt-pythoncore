"""Archive compression and extraction functions using 7-Zip"""

__all__ = [
    "compressFiles",
    "extractArchive",
]

import logging
import os
import subprocess

from typing import Optional

from ._decorators import timeIt
from ._system_functions import findExecutable, getNumCores

log = logging.getLogger(__name__)

_SEVEN_ZIP_DEFAULT = "C:/Program Files/7-Zip/7z.exe"


def _get7zipPath() -> str:
    """Locate the 7-Zip executable, returning its full path.

    Tries ``findExecutable('7z')`` first so that non-default installs and
    PATH-registered copies are found automatically.  Falls back to the
    standard installation path if the lookup fails.

    Returns:
        str: Absolute path to ``7z.exe``.

    Raises:
        RuntimeError: If 7-Zip cannot be found.

    """
    path = findExecutable("7z") or \
           (_SEVEN_ZIP_DEFAULT if os.path.exists(_SEVEN_ZIP_DEFAULT) else None)
    
    if not path:
        raise RuntimeError(
            "7-Zip executable not found. Install 7-Zip or ensure '7z' is on PATH."
        )
    
    return path


@timeIt
def compressFiles(src: str, dst: str, compression_level: int = 5, 
                  exclude_patterns: Optional[list[str]] = None) -> str:
    """Compress a provided directory or single file using 7-Zip.
    
    Examples:
        compressFiles("path/to/source", "path/to/destination.7z")
        compressFiles("path/to/source", "path/to/destination.7z", 
                      exclude_patterns=[".git*", "*.tmp", "__pycache__"])

    Args:
        src (str): The source directory or file to compress.
        dst (str): The destination compressed file path.
        compression_level (int, optional): Compression level (0-9). Default is 5.
        exclude_patterns (list of str, optional): List of file/folder patterns to exclude.
            Patterns support wildcards (* and ?). Examples: ".git*", "*.tmp", "node_modules".
            Default is None (no exclusions).

    Returns:
        str: The path to the archive file

    Raises:
        RuntimeError: If the compression process fails.
        
    """
    seven_zip = _get7zipPath()

    # Build the 7-Zip command
    cmd = [
        seven_zip,
        "a",  # Add to archive
        "-t7z",  # Archive type
        f"-mx={compression_level}",  # Compression level
        f"-mmt={getNumCores()}",  # Multi-Threading with all cores
        dst,  # Destination archive
        src  # Source file or directory
    ]
    
    # Add exclusion patterns if provided
    if exclude_patterns:
        for pattern in exclude_patterns:
            # Use -xr! for recursive exclusion
            cmd.append(f"-xr!{pattern}")

    # Execute the 7-Zip command
    log.info("Compressing files...")
    result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise RuntimeError("Compression failed: {}".format(result.stderr.decode()))

    log.info("Compression completed successfully.")
    return dst


@timeIt
def extractArchive(src: str, dst: str) -> None:
    """Extract the contents of a compressed file using 7-Zip.

    Args:
        src (str): The source compressed file to extract.
        dst (str): The destination directory to extract the contents to.

    Returns:
        None

    Raises:
        RuntimeError: If the extraction process fails.
        
    """
    seven_zip = _get7zipPath()

    # Build the 7-Zip command
    cmd = [
        seven_zip,
        "x",  # Extract files from archive
        src,  # Source archive
        f"-o{dst}",  # Destination directory
        f"-mmt={getNumCores()}",  # Multi-Threading with all cores
        "-md=4096m",
    ]

    # Execute the 7-Zip command
    log.info("Extracting files...")
    result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise RuntimeError("Extraction failed: {}".format(result.stderr.decode()))

    log.info("Extraction completed successfully.")
