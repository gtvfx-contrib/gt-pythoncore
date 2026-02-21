# -*- coding: utf-8 -*-
# Encoding is needed for printing unicdoe symbol in Python 2
"""An object oriented progressbar for the repl"""
import colorama

colorama.init(autoreset=True)

_COLOR_MAP = {
    "red":     colorama.Fore.RED,
    "green":   colorama.Fore.GREEN,
    "yellow":  colorama.Fore.YELLOW,
    "blue":    colorama.Fore.BLUE,
    "magenta": colorama.Fore.MAGENTA,
    "cyan":    colorama.Fore.CYAN,
    "white":   colorama.Fore.WHITE,
}


__all__ = [
    "ReplProgress"
]


class ReplProgress(object):
    """Helper object for making a progressbar in the REPL
    
    Args:
        total (int): Total number of items being iterated
        caption (str, optional): Optional caption for progressbar
        bar_length (int, optional): Optionally set the progressbar length. Default is 100.
            
    """
    def __init__(self, total, caption="", bar_length=100, color='yellow'):
        super(ReplProgress, self).__init__()
        self.total = total
        self.caption = caption
        self.color = color
        self.bar_length = bar_length
        self._progress = 0
        
    @property
    def progress(self):
        """(int): The iteration index"""
        return self._progress
    
    @progress.setter
    def progress(self, progress):
        self._progress = progress
    
    @property
    def percent(self):
        """(float): The percent complete."""
        return "{percent:.2f}%".format(percent=100 * (self.progress / float(self.total)))

    def start(self):
        """Reset progress to 0 and print output"""
        self.progress = 0
        self.output()

    def step(self):
        """Increase progress by one and print output"""
        self.progress += 1
        self.output()
    
    def output(self):
        """Print progressbar to console"""
        filled_length = int(round(self.bar_length * self.progress / float(self.total)))
        prog_bar = u"█" * filled_length + u"-" * (self.bar_length - filled_length)
        if self.percent == 100:
            self.color = "green"
        _fg = _COLOR_MAP.get(self.color, "")
        print(f"\r{_fg}{self.caption}|{prog_bar}| {self.percent}%{colorama.Style.RESET_ALL}", end="\r")
        if self.percent == 100:
            print('\n') # provide a line ending once complete
    
