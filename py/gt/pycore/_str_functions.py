
"""Helper functions for working with String objects"""

__all__ = [
    "isMatch",
    "formatDataSize",
    "formatTime",
    "formatCommandString",
    "verPadding",
    "getTimecodeVersion"
]

import re

from datetime import datetime



def isMatch(match, word, ignoreCase=True, switch=False):
    """Check if the word matches the supplied match.
    
    Args:
        match (str): The string to match
        word (str | list): The objects to check for a match
        ignoreCase (bool): Optional, ignore case when checking for match
        switch (bool): Optional, switch the search between 'match' and 'word'.
            Only applicable when searching a list.
    
    Returns:
        bool
    
    """
    if isinstance(word, str):
        # Regular Expression to match if word contains match
        if ignoreCase:
            return bool(re.search(match, word, re.IGNORECASE))
        
        return bool(re.search(match, word))
    
    if isinstance(word, list):
        if ignoreCase:
            if switch:
                return any(bool(re.search(w, match, re.IGNORECASE)) for w in word)
            
            return any(bool(re.search(match, w, re.IGNORECASE)) for w in word)
        
        if switch:
            return any(bool(re.search(w, match)) for w in word)
        
        return any(bool(re.search(match, w)) for w in word)

    # Default if no matched conditions
    return False
            
            
def verPadding(baseNumber, digitCount=2):
    """Adds zeros ("0") infront of the base number util the
    desired digitCount is achieved.

    Args:
        baseNumber (int | str):
        digitCount (int | str, optional): default is 2. Determines the maximum number
            of digits to return.

    Returns:
        str
    
    """
    return "{0:0>{1}}".format(baseNumber, digitCount)


def getTimecodeVersion():
    """Get a human-readable, but unique timestamp version string.
    
    Returns:
        str
    
    """
    now = datetime.now()

    format_str = "{year}-{month}-{day}.{hour}{minute}{second}"

    return format_str.format(
        year=verPadding(now.year, 2),
        month=verPadding(now.month, 2),
        day=verPadding(now.day, 2),
        hour=verPadding(now.hour, 2),
        minute=verPadding(now.minute, 2),
        second=verPadding(now.second, 2)
    )
    
    
def formatDataSize(bytesize: int) -> str:
    """Convert bytesize to a more readable value

    Args:
        bytesize (int): Filesize returned by common functions

    Returns:
        str: Formatted string converting to bytesize to closest type.
        
    """
    # pylint: disable=C0415
    # Localizing import where needed
    import math
    # pylint: enable=C0415
    
    if bytesize == 0:
        return "0B"
    conversion_type = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    idx = int(math.floor(math.log(bytesize, 1024)))
    exp = math.pow(1024, idx)
    adjusted_size = round(bytesize / exp, 2)
    return f"{adjusted_size} {conversion_type[idx]}"


def formatCommandString(cmd: list[str]) -> str:
    """Format a command list into a copy-pasteable command line string.
    
    Adds quotes around arguments containing spaces for proper shell execution.
    
    Args:
        cmd (list[str]): List of command arguments.
    
    Returns:
        str: Formatted command string suitable for copy-paste to command line.
    
    Examples:
        >>> formatCommandString(["robocopy", "C:\\My Path", "D:\\Dest", "/E"])
        'robocopy "C:\\My Path" D:\\Dest /E'
    
    """
    return ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)


def formatTime(input_seconds):
    """Convert a time duration from seconds into a human-readable string format.

    Args:
        input_seconds (float): The time duration in seconds.

    Returns:
        str: The formatted time string in seconds, minutes and seconds, or
        hours, minutes, and seconds.
         
    """
    if input_seconds < 60:
        time_str = f"{input_seconds:.2f} seconds"
    elif input_seconds < 3600:
        minutes, seconds = divmod(input_seconds, 60)
        time_str = f"{int(minutes)} minutes, {seconds:.2f} seconds"
    else:
        hours, remainder = divmod(input_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours)} hours, {int(minutes)} minutes, {seconds:.2f} seconds"
        
    return time_str
        