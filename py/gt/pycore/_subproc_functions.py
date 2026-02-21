"""Subprocess handling utilities."""

__all__ = [
    "processSubprocessOutput"
]

from typing import Optional, Union, Sequence

import logging

log = logging.getLogger(__name__)



def processSubprocessOutput(
    stdout: Union[bytes, str],
    returncode: int,
    process_name: str = 'Process',
    filter_patterns: Optional[Sequence[str]] = None,
    encoding: str = 'utf-8',
    log_success: bool = True,
    log_errors: bool = True
) -> tuple[str, bool]:
    """Process and log subprocess output with filtering and normalization.
    
    Handles subprocess stdout by decoding bytes, normalizing line endings,
    filtering unwanted patterns, and optionally logging results based on
    return code.
    
    Args:
        stdout: Raw subprocess output, either bytes or string.
        returncode: Process exit code. 0 indicates success.
        process_name: Name of process for log messages (e.g., 'Preview',
            'Export'). Used in error/success messages.
        filter_patterns: Optional sequence of string patterns. Lines starting
            with any of these patterns will be filtered out. If None, no
            filtering is applied.
        encoding: Character encoding for byte decoding. Default: 'utf-8'.
        log_success: If True, logs successful output (returncode 0) at
            info level. Default: True.
        log_errors: If True, logs failed output (returncode != 0) at
            error level. Default: True.
    
    Returns:
        tuple[str, bool]: A tuple containing:
            - Processed output string (decoded, normalized, filtered, stripped)
            - Success boolean (True if returncode is 0)
    
    Example:
        >>> proc = subprocess.run(['cmd'], capture_output=True)
        >>> output, success = processSubprocessOutput(
        ...     proc.stdout,
        ...     proc.returncode,
        ...     process_name='Export',
        ...     filter_patterns=['DEBUG:', '!---']
        ... )
        >>> if success:
        ...     print(f"Output: {output}")
        
        >>> # Without logging
        >>> output, success = processSubprocessOutput(
        ...     stdout,
        ...     returncode,
        ...     log_success=False,
        ...     log_errors=False
        ... )
    
    """
    success = returncode == 0
    
    # Handle empty stdout
    if not stdout:
        if returncode != 0 and log_errors:
            error_msg = f'{process_name} failed with exit code: {returncode}'
            log.error(error_msg)
        return '', success
    
    # Decode bytes to string and normalize line endings
    if isinstance(stdout, bytes):
        output = stdout.decode(encoding, errors='replace').replace('\r\n', '\n')
    elif isinstance(stdout, str):
        output = stdout.replace('\r\n', '\n')
    else:
        raise TypeError('stdout must be bytes or str')
    
    # Filter out unwanted patterns if specified
    if filter_patterns:
        output_lines = [
            line for line in output.split('\n')
            if not any(line.startswith(pattern) for pattern in filter_patterns)
        ]
        output = '\n'.join(output_lines).strip()
    else:
        output = output.strip()
    
    # Log based on return code
    if not success and log_errors:
        error_msg = f'{process_name} failed with exit code {returncode}:\n{output}'
        log.error(error_msg)
    elif success and log_success and output:
        log.info(f'{process_name} output:\n{output}')
    
    return output, success
