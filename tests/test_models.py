import pytest
from pydantic import ValidationError

from organizations.models import Entity, Organization, Party


def _minimal_party(**overrides):
    base = {
        "id": "vb-org/party:democratic",
        "name": "Democratic Party",
        "type": "party",
    }
    base.update(overrides)
    return base


def _minimal_org(**overrides):
    base = {
        "id": "vb-org/advocacy:american_civil_liberties_union",
        "name": "American Civil Liberties Union",
        "type": "org",
        "classification": "advocacy",
    }
    base.update(overrides)
    return base


def test_minimal_party_validates() -> None:
    e = Entity.validate_python(_minimal_party())
    assert isinstance(e, Party)
    assert e.type == "party"


def test_minimal_org_validates() -> None:
    e = Entity.validate_python(_minimal_org())
    assert isinstance(e, Organization)
    assert e.classification == "advocacy"


def test_party_id_root_must_be_party() -> None:
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(_minimal_party(id="vb-org/advocacy:democratic"))
    assert "party" in str(exc.value).lower()


def test_org_id_root_must_match_classification() -> None:
    """Id root segment must equal the classification (e.g. union/* must
    have classification=union)."""
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(
            _minimal_org(
                id="vb-org/union:service_employees_international_union"
            )
        )
    # advocacy classification + union/ id should fail
    assert "classification" in str(exc.value).lower()


def test_org_classification_required() -> None:
    raw = _minimal_org()
    raw.pop("classification")
    with pytest.raises(ValidationError):
        Entity.validate_python(raw)


def test_id_must_have_vb_org_prefix() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(id="party:democratic"))


def test_headquarters_must_be_ocd_division() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(
            _minimal_org(headquarters="vb-org/place:new_york")
        )


def test_affiliated_party_must_be_party_id() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(
            _minimal_org(affiliated_party="vb-org/advocacy:foo")
        )


def test_member_ids_must_be_vb_org() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(
            _minimal_org(
                classification="coalition",
                id="vb-org/coalition:america_votes",
                members=["not-a-vb-org-id"],
            )
        )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(some_unknown_field=42))


# ---------------------------------------------------------------------------
# #7 validation hardening
# ---------------------------------------------------------------------------


def test_successor_validates_as_vb_org_id() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(successor="not-an-id"))


def test_successor_accepts_valid_id() -> None:
    Entity.validate_python(
        _minimal_party(successor="vb-org/party:republican")
    )


def test_same_as_id_validates_as_vb_org_id() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(
            _minimal_party(same_as=[{"id": "ocd-division/country:us"}])
        )


def test_same_as_id_accepts_valid_id() -> None:
    Entity.validate_python(
        _minimal_party(same_as=[{"id": "vb-org/party:republican"}])
    )


def test_color_accepts_six_digit_hex() -> None:
    e = Entity.validate_python(_minimal_party(color="#0015BC"))
    assert e.color == "#0015BC"


def test_color_accepts_lowercase_hex() -> None:
    Entity.validate_python(_minimal_party(color="#abcdef"))


def test_color_rejects_three_digit_hex() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(color="#abc"))


def test_color_rejects_named_color() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(color="blue"))


def test_color_rejects_missing_hash() -> None:
    with pytest.raises(ValidationError):
        Entity.validate_python(_minimal_party(color="0015BC"))


def test_color_optional() -> None:
    e = Entity.validate_python(_minimal_party())
    assert e.color is None


def test_self_parent_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(
            _minimal_party(parent="vb-org/party:democratic")
        )
    assert "own parent" in str(exc.value)


def test_self_successor_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(
            _minimal_party(successor="vb-org/party:democratic")
        )
    assert "own successor" in str(exc.value)


def test_self_same_as_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(
            _minimal_party(
                same_as=[{"id": "vb-org/party:democratic"}]
            )
        )
    assert "same_as" in str(exc.value)


def test_self_in_members_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        Entity.validate_python(
            _minimal_org(
                classification="coalition",
                id="vb-org/coalition:america_votes",
                members=["vb-org/coalition:america_votes"],
            )
        )
    assert "members" in str(exc.value)
