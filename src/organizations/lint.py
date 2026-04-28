"""Validate YAML entity files against the schema and layout rules."""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from organizations.models import Organization
from organizations.paths import expected_path


@dataclass
class LintIssue:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def iter_yaml_files(root: Path) -> Iterator[Path]:
    if root.is_file() and root.suffix in {".yml", ".yaml"}:
        yield root
        return
    for path in sorted(root.rglob("*.yml")):
        yield path
    for path in sorted(root.rglob("*.yaml")):
        yield path


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def lint_file(path: Path, data_root: Path) -> list[LintIssue]:
    """Validate a single YAML file. Returns a list of issues."""
    issues: list[LintIssue] = []

    try:
        raw = _load_yaml(path)
    except yaml.YAMLError as e:
        return [LintIssue(path, f"YAML parse error: {e}")]

    if not isinstance(raw, dict):
        return [LintIssue(path, "top-level YAML must be a mapping")]

    try:
        entity = Organization.model_validate(raw)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "<root>"
            issues.append(LintIssue(path, f"[{loc}] {err['msg']}"))
        return issues

    expected = expected_path(entity.id, data_root).resolve()
    actual = path.resolve()
    if expected != actual:
        try:
            expected_rel = expected.relative_to(data_root.resolve())
        except ValueError:
            expected_rel = expected
        issues.append(
            LintIssue(
                path,
                f"file location does not match id {entity.id!r}; "
                f"expected {expected_rel}",
            )
        )

    if not entity.sources:
        issues.append(LintIssue(path, "no `sources` listed (soft)"))

    return issues


def lint_tree(root: Path, data_root: Path | None = None) -> list[LintIssue]:
    """Lint every YAML file under root."""
    if data_root is None:
        data_root = (
            root if root.is_dir() and root.name == "data" else _find_data_root(root)
        )
    issues: list[LintIssue] = []
    for path in iter_yaml_files(root):
        issues.extend(lint_file(path, data_root))
    return issues


def _find_data_root(start: Path) -> Path:
    """Walk upward from `start` looking for a `data/` directory."""
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        candidate = parent / "data"
        if candidate.is_dir():
            return candidate
    return start


def format_issues(issues: Iterable[LintIssue]) -> str:
    return "\n".join(str(i) for i in issues)


def main(argv: list[str] | None = None) -> int:
    """Simple entry point for ad-hoc CLI use without click."""
    argv = argv or sys.argv[1:]
    if not argv:
        target = Path("data")
    else:
        target = Path(argv[0])
    issues = lint_tree(target)
    if issues:
        print(format_issues(issues), file=sys.stderr)
        print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
