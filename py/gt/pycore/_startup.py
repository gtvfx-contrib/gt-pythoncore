"""Utilities for scope-isolated startup sequences."""

__all__ = [
    "Startup",
]

from typing import Callable


class Startup:
    """Scope-isolated initialization runner.

    An instance acts as a decorator to register initialization steps.
    Decorated functions are stored internally; the decorator returns ``None``
    so the decorated name is inert in the calling namespace rather than
    remaining as a live callable.

    Call ``run(globals())`` when all steps have been registered. It executes
    each step in registration order with per-step error isolation, then
    removes every decorated name **and the** ``Startup`` **instance itself**
    from the supplied namespace — leaving the global scope clean.

    This is particularly useful in hosted Python environments (Unreal Engine,
    Maya, Blender, etc.) where any module-level name is accessible from the
    host application's interactive console.

    Args:
        on_error (Callable, optional): Called with ``(func_name, exc)`` when a
            step raises an exception. Defaults to printing a formatted message.

    Examples:
    - Basic usage inside a startup module::
        ```python
        import unreal
        from gt.pycore import Startup

        _startup = Startup(on_error=lambda name, exc: unreal.log_error(
            f"Startup step '{name}' failed: {exc}"
        ))

        @_startup
        def _init_menus():
            from gt.unreal.menulib import MenuSession
            MenuSession("STUDIO_MENU_ROOTS").load()

        @_startup
        def _init_context_menus():
            from gt.unreal.menulib import ContextMenuSession
            ContextMenuSession("CONTEXT_MENU_ROOTS").load()

        _startup.run(globals())
        # After this line: _startup, _init_menus, and _init_context_menus
        # no longer exist in module globals.
        ```

    - Without namespace cleanup (testing or non-global use)::
        ```python
        startup = Startup()

        @startup
        def step_one():
            print("step one")

        startup.run()   # runs steps; no namespace cleanup performed
        ```

    """

    def __init__(self, on_error: Callable | None = None) -> None:
        """Initialize the Startup runner.

        Args:
            on_error: Called with ``(func_name: str, exc: Exception)`` when a
                step raises. Defaults to a ``print``-based fallback.

        """
        self._steps: list[Callable] = []
        self._tracked_names: list[str] = []
        self._on_error = on_error or self._defaultErrorHandler

    # ------------------------------------------------------------------
    # Decorator interface
    # ------------------------------------------------------------------

    def __call__(self, func: Callable) -> None:
        """Register ``func`` as an initialization step.

        Returns ``None`` so the decorated name is inert in the caller's
        namespace rather than remaining as a live callable.

        Args:
            func: The initialization function to register.

        Returns:
            None

        """
        self._steps.append(func)
        self._tracked_names.append(func.__name__)
        return None

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, namespace: dict | None = None) -> None:
        """Execute all registered steps, then clean up the namespace.

        Steps are run in registration order. If a step raises, ``on_error``
        is called with ``(func_name, exc)`` and execution continues with the
        next step.

        When ``namespace`` is provided (typically ``globals()``), the method
        removes every decorated name and the ``Startup`` instance itself from
        that namespace after all steps have run. The caller does **not** need
        a separate ``del`` statement.

        Args:
            namespace: The namespace dict to clean up after running, usually
                ``globals()``. Pass ``None`` to skip cleanup.

        """
        for func in self._steps:
            try:
                func()
            except Exception as exc:
                self._on_error(func.__name__, exc)

        if namespace is not None:
            self._cleanup(namespace)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cleanup(self, namespace: dict) -> None:
        """Remove decorated names and this instance from ``namespace``.

        Args:
            namespace: The namespace dict to clean.

        """
        for name in self._tracked_names:
            namespace.pop(name, None)

        # Remove the Startup instance itself by identity.
        instance_key = next(
            (key for key, value in namespace.items() if value is self),
            None,
        )
        if instance_key is not None:
            del namespace[instance_key]

    @staticmethod
    def _defaultErrorHandler(func_name: str, exc: Exception) -> None:
        """Default error handler — prints a formatted message.

        Args:
            func_name: Name of the step that raised.
            exc: The exception that was raised.

        """
        print(f"Startup: step '{func_name}' raised {type(exc).__name__}: {exc}")
