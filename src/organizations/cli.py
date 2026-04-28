"""Click-based CLI: `organizations lint`, `organizations show`, etc."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import yaml

from organizations.lint import format_issues, lint_tree
from organizations.models import Organization
from organizations.paths import expected_path, parse_vb_org_id


@click.group()
def main() -> None:
    """Tools for the curated parties + organizations dataset."""


@main.command()
@click.argument(
    "path", type=click.Path(path_type=Path, exists=True), default="data"
)
def lint(path: Path) -> None:
    """Lint YAML files under PATH (default: data/)."""
    issues = lint_tree(path)
    if issues:
        click.echo(format_issues(issues), err=True)
        click.echo(f"\n{len(issues)} issue(s) found.", err=True)
        sys.exit(1)
    click.echo("ok")


@main.command()
@click.argument("file", type=click.Path(path_type=Path, exists=True))
def show(file: Path) -> None:
    """Load and print an entity YAML as JSON (canonicalized)."""
    with file.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    entity = Organization.model_validate(raw)
    click.echo(entity.model_dump_json(indent=2, exclude_none=True))


@main.command(name="path")
@click.argument("vb_id")
def path_cmd(vb_id: str) -> None:
    """Print the canonical file path for a vb-org id."""
    parse_vb_org_id(vb_id)
    click.echo(expected_path(vb_id))


@main.command()
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=Path("schema/entity.schema.json"),
    help="Where to write the JSON schema.",
)
def schema(out: Path) -> None:
    """(Re)generate the JSON Schema from the pydantic models."""
    out.parent.mkdir(parents=True, exist_ok=True)
    js = Organization.model_json_schema()
    out.write_text(
        json.dumps(js, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    click.echo(f"wrote {out}")


if __name__ == "__main__":
    main()
