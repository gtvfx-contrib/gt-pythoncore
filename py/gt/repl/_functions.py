"""Functions for generating REPL specific content"""
import contextlib
import itertools
import logging
import os
import sys


log = logging.getLogger(__name__)


__all__ = [
    "changeWorkingDir",
    "cmdProgress",
    "waitCursor"
]


def waitCursor():
    """Yields items from the animation sequence until exhausted. Then repeats
    the sequence indefinitely.
    
    Can be called in any loop. Works well in a a while loop.
    
    """
    return itertools.cycle(['|', '/', '-', '\\'])


def cmdProgress(iteration, total, prefix='', suffix='', decimals=1, barLength=100):
    """Call in a loop to create terminal progress bar
    
    Args:
        iteration (Int):
            current iteration 
        total (Int):
            total iterations
        prefix (Str, optional):
            prefix string
        suffix (Str, optional):
            suffix string
        decimals (Int, optional):
            positive number of decimals in percent complete
        barLength (Int, optional):
            character length of bar

    Returns:
        None
    
    """
    if total == 0:
        # To protect from zero division if iterating an empty list
        total = 1
    strFormat = "{0:." + str(decimals) + "f}"
    percents = strFormat.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    progbar = '#' * filledLength + '-' * (barLength - filledLength)

    sys.stdout.write('\n\n') # Empty line between last iteration output
    
    sys.stdout.write("\r{prefix} |{progbar}| {percents}% {suffix}".format(
        prefix=prefix, progbar=progbar, percents=percents, suffix=suffix
    ))

    if iteration == total:
        sys.stdout.write('\n\n')
    sys.stdout.flush()
    
    
@contextlib.contextmanager
def changeWorkingDir(directory):
    """Context manager for executing logic from within the scope of a working
    directory without modifying the scope of parent logic.

    Args:
        directory (str): valid directory path

    Raises:
        assert: If supplied directory does not exist
        assert: If unable to change directory scope
        RuntimeError: if errors occur within the context.

    """
    assert os.path.exists(directory), "Supplied directory does not exist"

    # If a filepath is passed get parent directory
    if os.path.isfile(directory):
        directory = os.path.dirname(directory)

    current_dir = os.getcwd()
    os.chdir(directory)
    assert (os.getcwd() == directory), "Unable to set work directory"
    try:
        yield
    except RuntimeError as e:
        log.error("!!!--- Unable to execute logic within changeWorkingDir context ---!!!")
        log.warning("!!!--- current working dir: {}".format(os.getcwd()))
        raise e
    finally:
        os.chdir(current_dir)
