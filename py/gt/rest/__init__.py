"""Entry point for rest package namespace"""

__all__ = [
    "BaseInterface",
    "RestException",
    "CaptureException",
]

from ._baseInterface import BaseInterface, RestException
from ._captureException import CaptureException
