"""Filesystem manipulation functions (robocopy, rmdir, directory pruning)"""

__all__ = [
    "pruneDirectories",
    "robocopy",
    "rmdir",
]

import logging
import os
import subprocess

from typing import Optional

from ._decorators import timeIt
from ._path_functions import extendedCharacterPath, uncToMappedDrive
from ._str_functions import getTimecodeVersion, formatCommandString
from ._system_functions import getNumCores
from ._user_paths import userLogPathLocal

log = logging.getLogger(__name__)


def pruneDirectories(root: str, max_num_dirs: int = 5) -> None:
    """Clean up directories in the root keeping only the latest ones.
    
    Args:
        root (str): The root directory to clean up
        max_num_dirs (int): The maximum number of directories to keep.
    
    Returns:
        None
    
    """
    root_dirs = [os.path.join(root, d) for d in os.listdir(root)]
    root_dirs.sort(key=os.path.getmtime, reverse=True) # latest to oldest
    for i, folder in enumerate(root_dirs):
        if i < max_num_dirs:
            continue
        rmdir(folder)


@timeIt
def robocopy(src: str, dst: str, 
             params: Optional[list[str]] = None, 
             multithread: bool = True, 
             log_file: Optional[str] = None, 
             unique_log_file: bool = False) -> int:
    """Use the robocopy command to copy files and directories with optional parameters.

    This is roughly 1200% faster than shutils.copytree

    robocopy supports long paths by default and doesn't support adding the
    NFS extension to the input params.
    
    # Return Values
    - 0	No files were copied. No failure was met. No files were mismatched.
    The files already exist in the destination directory; so the copy operation 
    was skipped.
    - 1	All files were copied successfully.
    - 2	There are some additional files in the destination directory that aren't
      present in the source directory. No files were copied.
    - 3	Some files were copied. Additional files were present. No failure was met.
    - 5	Some files were copied. Some files were mismatched. No failure was met.
    - 6	Additional files and mismatched files exist. No files were copied and no
    failures were met. Which means that the files already exist in the
    destination directory.
    - 7	Files were copied, a file mismatch was present, and additional files
    were present.
    - 8	Several files didn't copy.

    ## Source:
        https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
    
    Args:
        src (str): The source directory to copy from.
        dst (str): The destination directory to copy to.
        params (list of str, optional): A list of additional parameters to pass to robocopy.
            Default is ["/E", "/Z", "/J", "/R:3", "/W:5"], which means:
                /E  - Copy all subdirectories, including empty ones.
                /Z  - Copy files in restartable mode.
                /J  - Copy using unbuffered I/O for large files.
                /R:3 - Retry 3 times on failed copies.
                /W:5 - Wait 5 seconds between retries.
        multithread (bool, optional): Whether to use multithreading. Default is True.
            Will use the multiprocessing module to get number of cores.
            Supplies /MT:<num_cores> parameter to command
        log_file (str, optional): Supply a path for the log file to overwrite the
            default file.
        unique_log_file (bool, optional): If true will append a time code to the
            log_file name.

    Returns:
        int: The process return code

    Raises:
        RuntimeError: If the robocopy command fails.
    
    """
    if params is None:
        params = ["/E", "/Z", "/J", "/R:3", "/W:5"]
    
    cmd = ["robocopy", src, uncToMappedDrive(dst)] + params
    
    if multithread:
        cmd.append(f"/MT:{getNumCores()}")
    
    if not log_file:
        log_file = os.path.join(userLogPathLocal("robocopy"), "robocopy.log")
        
    if unique_log_file:
        fpath, ext = os.path.splitext(log_file)
        log_file = os.path.join(fpath, f"_{getTimecodeVersion()}{ext}")
    
    cmd.append(f"/LOG:{log_file}")
    
    log.info("Executing: %s", formatCommandString(cmd))
    
    result = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=False)
    
    # robocopy has a variety of return codes. Several actually indicate success,
    # which is potentially confusing behavior for tools that expect 0 for 
    # success and non-zero for errors.
    if result.returncode == 0:
        log.info(
            "[robocopy result %d]: No files were copied. No failure was met. "
            "No files were mismatched. The files already exist in the "
            "destination directory; so the copy operation was skipped.",
            result.returncode
        )
        return 0
    if result.returncode == 1:
        log.info(
            "[robocopy result %d]: All files were copied successfully.",
            result.returncode
        )
        return 0
    if result.returncode == 2:
        log.info(
            "[robocopy result %d]: There are some additional files in the "
            "destination directory that aren't present in the source directory. "
            "No files were copied.",
            result.returncode
        )
        return 0
    if result.returncode == 3:
        log.info(
            "[robocopy result %d]: Some files were copied. Additional files "
            "were present. No failure was met.",
            result.returncode
        )
        return 0
    if result.returncode == 5:
        log.info(
            "[robocopy result %d]: Some files were copied. Some files were "
            "mismatched. No failure was met.",
            result.returncode
        )
        return 0
    if result.returncode == 6:
        log.info(
            "[robocopy result %d]: Additional files and mismatched files exist. "
            "No files were copied and no failures were met. Which means that "
            "the files already exist in the destination directory.",
            result.returncode
        )
        return 0
    if result.returncode == 7:
        log.info(
            "[robocopy result %d]: Files were copied, a file mismatch was "
            "present, and additional files were present.",
            result.returncode
        )
        return 0
    if result.returncode >= 8:
        log.error(
            "[robocopy result %d]: Robocopy encountered errors.",
            result.returncode
        )
        return result.returncode
    
    # For any unexpected codes (e.g., 4), return as-is
    return result.returncode


@timeIt
def rmdir(path: str, 
          _except: bool = False) -> None:
    """Remove a directory and all its contents.

    Args:
        path (str): The path to the directory to remove.
        _except (bool, optional): Internal flag for recursive error handling.
            Default is False.

    Returns:
        None

    Raises:
        RuntimeError: If the removal process fails.
    
    """
    try:
        _path = extendedCharacterPath(path)
        # Delete all files
        result = subprocess.run(["del", "/f", "/s", "/q", _path],
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to delete files in {path} with exit "
                               f"code {result.returncode}")
        
        if not os.path.exists(_path):
            # del removed the file so no need to run rmdir
            return
        
        # Delete all directories
        result = subprocess.run(["rmdir", "/s", "/q", _path],
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to remove directory {path} with exit "
                               f"code {result.returncode}")
    except RuntimeError as e:
        if _except:
            raise e
        
        # There are seemingly different permissions between UNC paths and drive
        # letter mappings. Where we might get an Access Denied error on a UNC
        # path, we'll have success with a drive letter path to the same source.
        # This logic attempts to find a known drive letter mapping for the 
        # network resource in a UNC path. Then runs the process with the drive
        # letter path.
        
        path = uncToMappedDrive(path)
        if not path.startswith("\\") and os.path.exists(path):
            log.info(f"drive_path: {path}")
            # call the decorated function so we get one time for the original call
            rmdir.__wrapped__(path, _except=True) # type: ignore
        else:
            raise e
