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
