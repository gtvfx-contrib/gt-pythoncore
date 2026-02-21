"""An object oriented progressbar for the repl"""
from __future__ import annotations

import colorama

colorama.init(autoreset=True)

_COLOR_MAP: dict[str, str] = {
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


class ReplProgress:
    """Helper object for making a progressbar in the REPL

    Args:
        total (int): Total number of items being iterated
        caption (str, optional): Optional caption for progressbar
        bar_length (int, optional): Optionally set the progressbar length. Default is 100.
        color (str, optional): Initial bar color. Default is ``'yellow'``.

    """

    def __init__(
        self,
        total: int,
        caption: str = "",
        bar_length: int = 100,
        color: str = "yellow",
    ) -> None:
        self.total: int = total
        self.caption: str = caption
        self.color: str = color
        self.bar_length: int = bar_length
        self._progress: int = 0

    @property
    def progress(self) -> int:
        """(int): The iteration index"""
        return self._progress

    @progress.setter
    def progress(self, progress: int) -> None:
        self._progress = progress

    @property
    def percent(self) -> float:
        """(float): The percent complete."""
        return 100 * (self.progress / float(self.total))

    def start(self) -> None:
        """Reset progress to 0 and print output"""
        self.progress = 0
        self.output()

    def step(self) -> None:
        """Increase progress by one and print output"""
        self.progress += 1
        self.output()

    def output(self) -> None:
        """Print progressbar to console"""
        filled_length = int(round(self.bar_length * self.progress / float(self.total)))
        prog_bar = u"█" * filled_length + u"-" * (self.bar_length - filled_length)
        if self.percent >= 100:
            self.color = "green"
        _fg = _COLOR_MAP.get(self.color, "")
        print(f"\r{_fg}{self.caption}|{prog_bar}| {self.percent:.2f}%{colorama.Style.RESET_ALL}", end="\r")
        if self.percent >= 100:
            print('\n')  # provide a line ending once complete
