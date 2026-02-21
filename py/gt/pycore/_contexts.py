"""General python context managers"""

__all__ = [
    "managedOutput",
    "mappedDrive",
    "retryContext"
]

import os
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from typing import Generator, Optional

from ._fs_functions import robocopy, rmdir
from ._path_functions import ensurePath, uncToMappedDrive


@contextmanager
def mappedDrive(unc_path: str) -> Generator[str, None, None]:
    """Context manager that provides a drive-letter path for a UNC path.

    Resolves a UNC path to a mapped drive letter for use inside the ``with``
    block. Resolution order:

    1. Static ``NET_STORAGE_MAP`` config.
    2. Currently active Windows drive mappings (``WNetGetConnectionW``).
    3. Creates a temporary mapping with ``net use * <share>`` and removes it
       on exit with ``net use <drive> /delete /y``.

    The share root (``\\\\server\\share``) is mapped, not the full path — so
    sub-paths within the share are preserved under the drive letter.

    Args:
        unc_path (str): A UNC path to map, e.g. ``r'\\\\server\\share\\dir\\file.txt'``.

    Yields:
        str: The drive-letter equivalent of ``unc_path``.

    Raises:
        RuntimeError: If a temporary drive mapping cannot be created.

    Examples:
        >>> with mappedDrive(r'\\\\server\\share\\assets\\file.txt') as path:
        ...     # path is something like 'Z:\\\\assets\\\\file.txt'
        ...     process(path)

    """
    normalised = os.path.normpath(unc_path)

    # Try the cheap static + active-mapping lookup first.
    mapped = uncToMappedDrive(normalised)
    if mapped != normalised:
        yield mapped
        return

    # Extract the share root: first element of UNC parts is '\\\\server\\share'.
    path_obj = Path(normalised)
    parts = path_obj.parts
    if not parts or not parts[0].startswith("\\\\"):
        # Not a UNC path — nothing to map.
        yield unc_path
        return

    share_root = parts[0]  # e.g. '\\\\server\\share'
    sub_path = os.path.join(*parts[1:]) if len(parts) > 1 else ""

    # Create a temporary mapping with net use.
    result = subprocess.run(
        ["net", "use", "*", share_root],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to map '{share_root}' to a drive letter: "
            f"{result.stderr.decode().strip()}"
        )

    # net use prints: "Drive X: is now connected to \\server\share."
    output = result.stdout.decode()
    drive_letter: Optional[str] = None
    for token in output.split():
        if len(token) == 2 and token[1] == ":" and token[0].isalpha():
            drive_letter = token.upper()
            break

    if not drive_letter:
        raise RuntimeError(
            f"Could not determine the drive letter assigned to '{share_root}'. "
            f"net use output: {output.strip()}"
        )

    try:
        yield os.path.join(drive_letter + os.sep, sub_path) if sub_path else drive_letter + os.sep
    finally:
        subprocess.run(
            ["net", "use", drive_letter, "/delete", "/y"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


@contextmanager
def managedOutput(output_path: str, clear_output: bool=True) -> Generator[str, None, None]:
    """Context manager that writes output to a local temp location and then
    copies the local output to the initial supplied output location.
    
    Args:
        output_path (str): The final output path where the file or directory should be copied.
        clear_output (bool): Optional, if true will attempt to delete any content
            in the output_path before copying data there.
    
    Yields:
        str: The temporary file or directory path to write output to.
        
    """
    temp_dir = tempfile.mkdtemp()
    temp_output_path = os.path.join(temp_dir, os.path.basename(output_path))
    
    if os.path.isdir(output_path):
        ensurePath(temp_output_path)
    
    if clear_output:
        # Event to signal when the directory removal is complete
        removal_complete = threading.Event()
        
        def remove_previous_output():
            if os.path.isdir(temp_output_path) and os.path.exists(output_path):
                # Clear the final output path before we copy our data there
                print("Removing previous output directory...")
                rmdir(output_path)
            removal_complete.set()
        
        # Start the thread to remove the previous output directory
        removal_thread = threading.Thread(target=remove_previous_output)
        removal_thread.start()
    
    try:
        yield temp_output_path
        
        if clear_output:
            # Wait for the removal thread to complete
            removal_complete.wait() # type: ignore
        
        # Ensure robocopy completes before proceeding
        result = robocopy(temp_output_path, output_path)
        if result != 0:
            raise RuntimeError(f"Robocopy failed with exit code {result}")
    finally:
        print("Cleaning temp directory...")
        rmdir(temp_dir)
        
    
@contextmanager
def retryContext(retries=3, retry_delay=10, exceptions=None, handler=None):
    """Context manager to retry logic a specified number of times.

    Args:
        retries (int): Number of retry attempts.
        retry_delay (int): Time to wait between retries in seconds.
        exceptions (Exception or tuple of Exceptions, optional): Exception(s) 
            to catch and retry on. Defaults to RuntimeError if None.
        handler (callable, optional): Custom exception handler with signature 
            (exception, attempt, retries) -> bool
            Returns True to retry, False to re-raise immediately.

    Yields:
        None

    Raises:
        The last exception caught after all retry attempts fail.
        
    Example handlers:
    ```python
    def keyErrorHandler(e, attempt, retries):
        '''Custom handler for KeyError exceptions'''
        if isinstance(e, KeyError) and e.args[0] != 'www-authenticate':
            # Don't retry for KeyErrors that aren't 'www-authenticate'
            return False
        print(f"Authentication error, retrying ({attempt}/{retries})...")
        return True
        
    # For more complex error handling
    def advancedErrorHandler(e, attempt, retries):
        '''Advanced error handling with different behaviors based on exception type'''
        if isinstance(e, ConnectionError):
            print(f"Connection error on attempt {attempt}/{retries}, retrying...")
            return True
        elif isinstance(e, TimeoutError):
            # Only retry timeouts twice
            if attempt < 2:
                print(f"Timeout on attempt {attempt}/{retries}, retrying...")
                return True
            return False
        elif isinstance(e, KeyError):
            if e.args[0] == 'www-authenticate':
                print(f"Authentication error on attempt {attempt}/{retries}, "
                      f"retrying...")
                return True
            return False
        return True  # Default: retry other exceptions
    ```
        
    """
    # Default to RuntimeError if no exceptions specified
    if exceptions is None:
        exceptions = RuntimeError

    for attempt in range(retries):
        try:
            yield
            break
        except exceptions as e:
            # Use the last attempt
            is_last_attempt = attempt == retries - 1
            
            # Handle the exception with custom handler if provided
            if handler is not None:
                should_retry = handler(e, attempt + 1, retries)
                if not should_retry or is_last_attempt:
                    raise e
            else:
                # Default handling
                if is_last_attempt:
                    raise e
                print(f"Request failed: {str(e)}. Retrying in {retry_delay} "
                      f"seconds... (Attempt {attempt + 1}/{retries})")
                
            time.sleep(retry_delay)
