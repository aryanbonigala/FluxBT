from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
from dataclasses import dataclass
from typing import Type

import httpx

from .base import BaseStrategy


@dataclass(frozen=True)
class GitHubSource:
    owner: str
    repo: str
    branch: str
    file_path: str

    def raw_url(self) -> str:
        base = "https://raw.githubusercontent.com/"
        return base + f"{self.owner}/{self.repo}/{self.branch}/{self.file_path}"


class StrategyLoadError(Exception):
    pass


def fetch_strategy_code(src: GitHubSource, timeout_s: float = 20.0) -> str:
    try:
        resp = httpx.get(src.raw_url(), timeout=timeout_s)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - we attach context and rethrow
        msg = f"Failed to fetch strategy from GitHub: {src.raw_url()}\n{exc}"
        raise StrategyLoadError(msg) from exc
    return resp.text


def _load_module_from_code(module_name: str, code: str) -> types.ModuleType:
    # Use a temp file to give the module a proper __file__ and better tracebacks
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    spec = importlib.util.spec_from_file_location(module_name, tmp_path)
    if spec is None or spec.loader is None:
        raise StrategyLoadError("Could not create module spec for strategy code")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:  # noqa: BLE001
        raise StrategyLoadError(f"Error importing strategy module: {exc}") from exc
    return module


def _find_strategy_class(module: types.ModuleType, class_name: str | None) -> Type[BaseStrategy]:
    candidates: list[type] = []
    for _obj_name, obj in vars(module).items():
        if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
            candidates.append(obj)

    if class_name:
        for cls in candidates:
            if cls.__name__ == class_name:
                return cls  # type: ignore[return-value]
        available = [c.__name__ for c in candidates]
        raise StrategyLoadError(f"Strategy class '{class_name}' not found. Available: {available}")

    if not candidates:
        raise StrategyLoadError("No subclass of BaseStrategy found in the module")
    if len(candidates) > 1:
        names = ", ".join(c.__name__ for c in candidates)
        raise StrategyLoadError(
            f"Multiple strategy classes found ({names}); specify --class-name explicitly"
        )
    return candidates[0]  # type: ignore[return-value]


def load_github_strategy(
    owner: str,
    repo: str,
    file_path: str,
    branch: str = "main",
    class_name: str | None = None,
) -> BaseStrategy:
    """Fetch and load a strategy class from a GitHub repository.

    Parameters
    ----------
    owner, repo: GitHub project where the file resides
    file_path: Path within repository, e.g. "strategies/momentum.py"
    branch: Branch or tag name
    class_name: Optional class name; if omitted, auto-detect a single BaseStrategy subclass
    """
    src = GitHubSource(owner=owner, repo=repo, branch=branch, file_path=file_path)
    code = fetch_strategy_code(src)
    module = _load_module_from_code(module_name="fluxbt_remote_strategy", code=code)
    cls = _find_strategy_class(module, class_name)

    # Validate required interface by instantiation and attribute access
    try:
        instance = cls()  # type: ignore[call-arg]
    except TypeError as exc:
        msg = (
            f"Strategy class '{cls.__name__}' must be instantiable without args "
            f"or provide defaults: {exc}"
        )
        raise StrategyLoadError(msg) from exc

    # Basic interface checks
    missing: list[str] = []
    for attr in ("name", "params", "reset", "on_bar"):
        if not hasattr(instance, attr):
            missing.append(attr)
    if missing:
        missing_msg = ", ".join(missing)
        raise StrategyLoadError(
            f"Loaded strategy missing required attributes/methods: {missing_msg}"
        )

    # Ensure types where feasible
    _ = instance.name  # property access
    _ = instance.params  # property access
    return instance
