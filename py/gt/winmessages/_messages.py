"""Simple Windows style dialogs"""
import ctypes


__all__ = [
    "winMessageBox"
]


def winMessageBox(message, title, style=0):
    """Presents a Windows style message box.
    
    Set the style per your needs.
    
    Styles:
        0 : OK
        1 : OK | Cancel
        2 : Abort | Retry | Ignore
        3 : Yes | No | Cancel
        4 : Yes | No
        5 : Retry | Cancel 
        6 : Cancel | Try Again | Continue
    
    Args:
        message (str): The message text to display.
        title (str): Add a title for the dialog.
        style (int): Controls the buttons/options available to the user.
    
    Returns:
        int: result of user choice.
            OK: 1
            Cancel: 2
            Abort: 3
            Retry: 4
            Ignore: 5
            Yes: 6
            No: 7
            Try Again: 10
            Continue: 11
        
    """
    return ctypes.windll.user32.MessageBoxW(0, message, title, style)
