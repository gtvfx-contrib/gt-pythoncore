"""Entry point for rest package namespace"""
from gt.lazyimports import LazyImporter


_LAZY_IMPORTS = LazyImporter()


__all__ = _LAZY_IMPORTS.lazy_imports # type: ignore[assignment]


def __getattr__(name: str):
    if name in __all__:
        return _LAZY_IMPORTS.resolveLazyImport(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return __all__
