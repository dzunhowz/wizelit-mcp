"""Wizelit MCP Servers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_pkg_dir = Path(__file__).resolve().parent


def _alias_module(alias: str, folder: str) -> None:
	"""Load a submodule from a hyphenated folder and expose it as a package alias."""
	init_py = _pkg_dir / folder / "__init__.py"
	if not init_py.exists():
		return

	spec = spec_from_file_location(f"{__name__}.{alias}", init_py)
	if spec and spec.loader:
		module = module_from_spec(spec)
		sys.modules[f"{__name__}.{alias}"] = module
		spec.loader.exec_module(module)
		setattr(sys.modules[__name__], alias, module)


_alias_module("code_scout", "code-scout")
_alias_module("refactoring_agent", "refactoring-agent")

__all__ = ["code_scout", "refactoring_agent"]
