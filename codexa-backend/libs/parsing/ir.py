from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IRFile:
    file: str
    language: str
    functions: list[dict[str, Any]] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    variables: list[dict[str, Any]] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)
    control_structures: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)
    definitions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "language": self.language,
            "functions": self.functions,
            "classes": self.classes,
            "variables": self.variables,
            "imports": self.imports,
            "control_structures": self.control_structures,
            "calls": self.calls,
            "definitions": self.definitions,
        }
