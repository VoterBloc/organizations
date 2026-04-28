from pathlib import Path

import pytest

from organizations.paths import expected_path, parse_vb_org_id


@pytest.mark.parametrize(
    "vb_id,expected",
    [
        ("vb-org/party:democratic", Path("data/party/democratic.yml")),
        ("vb-org/party:republican", Path("data/party/republican.yml")),
        ("vb-org/party:green", Path("data/party/green.yml")),
        (
            "vb-org/advocacy:american_civil_liberties_union",
            Path("data/advocacy/american_civil_liberties_union.yml"),
        ),
        (
            "vb-org/union:service_employees_international_union",
            Path("data/union/service_employees_international_union.yml"),
        ),
        (
            "vb-org/think_tank:heritage_foundation",
            Path("data/think_tank/heritage_foundation.yml"),
        ),
        (
            "vb-org/party:democratic/state:ca",
            Path("data/party/state/democratic-ca.yml"),
        ),
    ],
)
def test_expected_path(vb_id: str, expected: Path) -> None:
    assert expected_path(vb_id) == expected


def test_parse_vb_org_id_requires_prefix() -> None:
    with pytest.raises(ValueError):
        parse_vb_org_id("party:democratic")


def test_parse_vb_org_id_rejects_empty_after_prefix() -> None:
    with pytest.raises(ValueError):
        parse_vb_org_id("vb-org/")


def test_parse_vb_org_id_rejects_malformed_segment() -> None:
    with pytest.raises(ValueError):
        parse_vb_org_id("vb-org/party")  # missing :slug


def test_parsed_parts() -> None:
    parsed = parse_vb_org_id("vb-org/party:democratic/state:ca")
    assert parsed.root_type == "party"
    assert parsed.root_slug == "democratic"
    assert parsed.leaf_type == "state"
    assert parsed.leaf_slug == "ca"
    assert parsed.parent_id == "vb-org/party:democratic"


def test_parent_id_is_none_for_flat_id() -> None:
    parsed = parse_vb_org_id("vb-org/party:democratic")
    assert parsed.parent_id is None
