"""Namespace for metaclasses"""
from gt.lazyimports import LazyImporter


_LAZY_IMPORTS = LazyImporter()


__all__ = _LAZY_IMPORTS.lazy_imports # type: ignore[assignment]


def __getattr__(name: str):
    return _LAZY_IMPORTS.resolveLazyImport(name)


def __dir__():
    return __all__
