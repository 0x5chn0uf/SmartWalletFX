"""Compatibility package mapping to `app.domains`.

This module exists solely to maintain backward-compatibility with
older import paths (`app.domain.*`) after the project migrated to the
pluralised package name `app.domains`.
"""

import importlib
import sys

# Lazily proxy submodules from `app.domains`.
_submodules = ["errors"]
for _name in _submodules:
    full_old = f"{__name__}.{_name}"
    full_new = f"app.domains.{_name}"
    try:
        sys.modules[full_old] = importlib.import_module(full_new)
    except ModuleNotFoundError:  # pragma: no cover – defensive
        # If the new module doesn't exist yet, skip.
        pass

del importlib, sys, _name, full_old, full_new, _submodules
