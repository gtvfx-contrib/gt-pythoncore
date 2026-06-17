
import ast
import importlib
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)

class LazyImporter:

    def __init__(self):
        _frame = sys._getframe(1)
        self.calling_module = Path(_frame.f_code.co_filename).resolve()
        self.caller_name = _frame.f_globals["__name__"]
        self._lazy_imports = self.buildLazyImports()

    @property
    def lazy_imports(self) -> list[str]:
        return list(self._lazy_imports)

    def buildLazyImports(self) -> dict[str, str]:
        """Scan private submodules and map each exported symbol to its module.

        Parses ``__all__`` from each ``_*.py`` file using AST (no imports
        executed), so new submodules are picked up automatically.

        Returns:
            Mapping of symbol name to submodule stem (e.g. ``"ensurePath"`` →
            ``"_path_functions"``).

        """
        log.debug("Building lazy imports for module: %s", self.calling_module)

        mapping: dict[str, str] = {}
        for path in sorted(self.calling_module.parent.glob("_*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "__all__"
                        for target in node.targets
                    )
                    and isinstance(node.value, ast.List)
                ):
                    for element in node.value.elts:
                        if isinstance(element, ast.Constant) and isinstance(element.value, str):
                            mapping[element.value] = path.stem
                    break
        return mapping


    def resolveLazyImport(self, name: str):
        log.debug("Resolving lazy import, %s, with caller: %s", name, self.caller_name)
        if name in self._lazy_imports:
            module = importlib.import_module(f".{self._lazy_imports[name]}", self.caller_name)
            value = getattr(module, name)
            # Cache in the calling module's __dict__ so that Python's import
            # machinery finds the value on the second getattr pass (from
            # _handle_fromlist) without triggering __getattr__ a second time.
            sys.modules[self.caller_name].__dict__[name] = value
            return value
        raise AttributeError(f"module {self.caller_name!r} has no attribute {name!r}")
