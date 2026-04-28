"""vb-org id ↔ filesystem path mapping.

The repository stores one file per entity, placed at a path derived from
its `vb-org/...` id. See README.md / CLAUDE.md for the layout rules this
module encodes.

US-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

VB_ORG_PREFIX = "vb-org/"

# Allow lowercase letters, digits, period, hyphen, underscore, tilde.
_TYPE_RE = r"[a-z][a-z0-9_-]*"
_ID_RE = r"[\w.\-~]+"
_SEGMENT_RE = re.compile(rf"^({_TYPE_RE}):({_ID_RE})$", re.UNICODE)


@dataclass(frozen=True)
class VbOrgId:
    """Parsed vb-org id."""

    raw: str
    segments: tuple[tuple[str, str], ...]

    @property
    def root_type(self) -> str:
        return self.segments[0][0]

    @property
    def root_slug(self) -> str:
        return self.segments[0][1]

    @property
    def leaf_type(self) -> str:
        return self.segments[-1][0]

    @property
    def leaf_slug(self) -> str:
        return self.segments[-1][1]

    @property
    def parent_id(self) -> str | None:
        if len(self.segments) <= 1:
            return None
        parent_segs = self.segments[:-1]
        return VB_ORG_PREFIX + "/".join(f"{k}:{v}" for k, v in parent_segs)


def parse_vb_org_id(value: str) -> VbOrgId:
    """Parse a vb-org id. Raises ValueError if malformed."""
    if not value.startswith(VB_ORG_PREFIX):
        raise ValueError(f"vb-org id must start with {VB_ORG_PREFIX!r}: {value!r}")
    rest = value[len(VB_ORG_PREFIX) :]
    if not rest:
        raise ValueError(f"vb-org id is empty after prefix: {value!r}")
    segments: list[tuple[str, str]] = []
    for i, segment in enumerate(rest.split("/")):
        m = _SEGMENT_RE.match(segment)
        if not m:
            raise ValueError(
                f"vb-org id segment {i} is invalid: {segment!r} (in {value!r})"
            )
        segments.append((m.group(1), m.group(2)))
    return VbOrgId(raw=value, segments=tuple(segments))


def id_to_path(vb_id: str, data_root: Path | str = "data") -> Path:
    """Compute the canonical path on disk for a vb-org id.

    >>> id_to_path('vb-org/party:democratic')
    PosixPath('data/party/democratic.yml')
    >>> id_to_path('vb-org/advocacy:american_civil_liberties_union')
    PosixPath('data/advocacy/american_civil_liberties_union.yml')
    >>> id_to_path('vb-org/think_tank:heritage_foundation')
    PosixPath('data/think_tank/heritage_foundation.yml')
    >>> id_to_path('vb-org/party:democratic/state:ca')
    PosixPath('data/party/state/democratic-ca.yml')
    """
    root = Path(data_root)
    parsed = parse_vb_org_id(vb_id)
    segs = parsed.segments

    # Flat: data/{type}/{slug}.yml
    if len(segs) == 1:
        type_, slug = segs[0]
        return root / type_ / f"{slug}.yml"

    # Nested (e.g. state-level party affiliate). Flatten as
    # `{parent_slug}-{leaf_slug}.yml` in `data/{root_type}/{leaf_type}/`.
    root_type, _ = segs[0]
    _, parent_slug = segs[-2]
    leaf_type, leaf_slug = segs[-1]
    return root / root_type / leaf_type / f"{parent_slug}-{leaf_slug}.yml"


def expected_path(vb_id: str, data_root: Path | str = "data") -> Path:
    """Alias for id_to_path — returns where the file for this id belongs."""
    return id_to_path(vb_id, data_root)
