"""General python context managers"""
from __future__ import annotations

__all__ = [
    "managedOutput",
    "mappedDrive",
    "retry"
]

import logging
import os
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from collections.abc import Callable, Generator

log = logging.getLogger(__name__)

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
    drive_letter: str | None = None
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
def managedOutput(output_path: str, clear_output: bool = True) -> Generator[str, None, None]:
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
        # Event to signal when the directory or file removal is complete
        removal_complete = threading.Event()
        
        def remove_previous_output():
            if os.path.exists(output_path):
                # Clear the final output path before we copy our data there
                if os.path.isdir(output_path):
                    print("Removing previous output directory...")
                    rmdir(output_path)
                else:
                    print("Removing previous output file...")
                    os.remove(output_path)
            removal_complete.set()
        
        # Start the thread to remove the previous output path
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
        
    
class _Attempt:
    """Single attempt produced by :class:`retry`.

    Used as a context manager inside the ``for attempt in retry(...):`` loop.
    Suppresses any exception from the ``with`` body so the outer loop can
    inspect it and decide whether to sleep-and-retry or re-raise.
    """

    def __init__(self) -> None:
        self.exception: BaseException | None = None

    def __enter__(self) -> _Attempt:
        self.exception = None
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> bool:
        if exc_val is not None:
            self.exception = exc_val
        return exc_val is not None  # always suppress so the generator resumes


class retry:
    """Iterable that drives a retry loop via a ``for`` / ``with`` pattern.

    Retrying only a targeted section of a function (rather than the whole
    thing) is achieved by placing the ``with attempt:`` block around just
    the code that may fail::

        for attempt in retry(retries=3, retry_delay=2, exceptions=ConnectionError):
            with attempt:
                result = risky_operation()

    The loop exits as soon as the ``with`` block completes without an
    exception.  On failure the generator sleeps for ``retry_delay`` seconds
    and yields the next attempt.  After all attempts are exhausted the
    original exception is re-raised.

    Args:
        retries (int): Maximum number of attempts (default ``3``).
        retry_delay (int): Seconds to wait between attempts (default ``10``).
        exceptions (type or tuple of types, optional): Exception type(s) to
            catch and retry on.  Defaults to ``RuntimeError``.
        handler (callable, optional): Custom exception handler with signature
            ``(exception, attempt_number, total_retries) -> bool``.  Return
            ``True`` to retry, ``False`` to re-raise immediately.

    Raises:
        The last caught exception once all attempts are exhausted.

    Usage with a custom handler::

        def _handler(e, attempt, retries):
            if isinstance(e, KeyError) and e.args[0] != 'www-authenticate':
                return False  # don't retry
            log.warning("Auth error on attempt %d/%d", attempt, retries)
            return True

        for attempt in retry(retries=3, exceptions=KeyError, handler=_handler):
            with attempt:
                token = fetch_token()

    """

    def __init__(
        self,
        retries: int = 3,
        retry_delay: int = 10,
        exceptions: type[BaseException] | tuple[type[BaseException], ...] | None = None,
        handler: Callable | None = None,
    ) -> None:
        self._retries = retries
        self._retry_delay = retry_delay
        self._exceptions = exceptions if exceptions is not None else RuntimeError
        self._handler = handler

    def __iter__(self) -> Generator[_Attempt, None, None]:
        for attempt_num in range(self._retries):
            is_last = attempt_num == self._retries - 1
            attempt = _Attempt()
            yield attempt

            if attempt.exception is None:
                return  # success — stop iterating

            e = attempt.exception

            # Re-raise immediately if it's not a type we were asked to catch.
            if not isinstance(e, self._exceptions):
                raise e

            if self._handler is not None:
                should_retry = self._handler(e, attempt_num + 1, self._retries)
                if not should_retry or is_last:
                    raise e
            elif is_last:
                raise e

            log.warning(
                "Attempt %d/%d failed: %s. Retrying in %ds...",
                attempt_num + 1, self._retries, e, self._retry_delay,
            )
            time.sleep(self._retry_delay)
