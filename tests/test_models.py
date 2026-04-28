import pytest
from pydantic import ValidationError

from organizations.models import Organization


def _minimal(**overrides):
    """A minimal valid Organization, defaulting to a party. Override
    `id` and `classification` together when testing other classifications."""
    base = {
        "id": "vb-org/party:democratic",
        "name": "Democratic Party",
        "classification": "party",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Basic validation
# ---------------------------------------------------------------------------


def test_minimal_party_validates() -> None:
    e = Organization.model_validate(_minimal())
    assert e.classification == "party"


def test_minimal_advocacy_validates() -> None:
    e = Organization.model_validate(
        _minimal(
            id="vb-org/advocacy:american_civil_liberties_union",
            name="American Civil Liberties Union",
            classification="advocacy",
        )
    )
    assert e.classification == "advocacy"


def test_classification_required() -> None:
    raw = _minimal()
    raw.pop("classification")
    with pytest.raises(ValidationError):
        Organization.model_validate(raw)


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(some_unknown_field=42))


# ---------------------------------------------------------------------------
# ID validation
# ---------------------------------------------------------------------------


def test_id_must_have_vb_org_prefix() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(id="party:democratic"))


def test_id_root_must_match_classification() -> None:
    """An id with root segment X requires classification X."""
    with pytest.raises(ValidationError) as exc:
        Organization.model_validate(
            _minimal(
                id="vb-org/advocacy:foo",  # root=advocacy
                classification="party",     # but classification=party
            )
        )
    assert "classification" in str(exc.value).lower()


# ---------------------------------------------------------------------------
# Cross-reference validation
# ---------------------------------------------------------------------------


def test_headquarters_must_be_ocd_division() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(headquarters="vb-org/place:new_york")
        )


def test_jurisdiction_must_be_ocd_division() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(jurisdiction="vb-org/place:new_york")
        )


def test_affiliated_party_must_be_party_id() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(
                id="vb-org/advocacy:foo",
                classification="advocacy",
                affiliated_party="vb-org/advocacy:bar",
            )
        )


def test_affiliated_party_accepts_party_id() -> None:
    Organization.model_validate(
        _minimal(
            id="vb-org/advocacy:foo",
            classification="advocacy",
            affiliated_party="vb-org/party:democratic",
        )
    )


def test_member_ids_must_be_vb_org() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(
                classification="coalition",
                id="vb-org/coalition:america_votes",
                members=["not-a-vb-org-id"],
            )
        )


def test_successor_validates_as_vb_org_id() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(successor="not-an-id"))


def test_successor_accepts_valid_id() -> None:
    Organization.model_validate(
        _minimal(successor="vb-org/party:republican")
    )


def test_same_as_id_validates_as_vb_org_id() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(same_as=[{"id": "ocd-division/country:us"}])
        )


def test_same_as_id_accepts_valid_id() -> None:
    Organization.model_validate(
        _minimal(same_as=[{"id": "vb-org/party:republican"}])
    )


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------


def test_colors_accepts_six_digit_hex() -> None:
    e = Organization.model_validate(_minimal(colors=["#0015BC"]))
    assert e.colors == ["#0015BC"]


def test_colors_accepts_multiple_entries_first_is_primary() -> None:
    e = Organization.model_validate(
        _minimal(colors=["#0015BC", "#FFFFFF"])
    )
    assert e.colors[0] == "#0015BC"
    assert e.colors[1] == "#FFFFFF"


def test_colors_accepts_lowercase_hex() -> None:
    Organization.model_validate(_minimal(colors=["#abcdef"]))


def test_colors_rejects_three_digit_hex() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(colors=["#abc"]))


def test_colors_rejects_named_color() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(colors=["blue"]))


def test_colors_rejects_missing_hash() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(_minimal(colors=["0015BC"]))


def test_colors_rejects_bad_entry_among_good() -> None:
    with pytest.raises(ValidationError):
        Organization.model_validate(
            _minimal(colors=["#0015BC", "blue"])
        )


def test_colors_default_empty() -> None:
    e = Organization.model_validate(_minimal())
    assert e.colors == []


# ---------------------------------------------------------------------------
# Self-reference
# ---------------------------------------------------------------------------


def test_self_parent_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Organization.model_validate(
            _minimal(parent="vb-org/party:democratic")
        )
    assert "own parent" in str(exc.value)


def test_self_successor_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Organization.model_validate(
            _minimal(successor="vb-org/party:democratic")
        )
    assert "own successor" in str(exc.value)


def test_self_same_as_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Organization.model_validate(
            _minimal(same_as=[{"id": "vb-org/party:democratic"}])
        )
    assert "same_as" in str(exc.value)


def test_self_in_members_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Organization.model_validate(
            _minimal(
                classification="coalition",
                id="vb-org/coalition:america_votes",
                members=["vb-org/coalition:america_votes"],
            )
        )
    assert "members" in str(exc.value)
