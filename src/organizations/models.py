"""Pydantic models for the organizations YAML schema.

This is the canonical definition of the schema. Sibling to the
`divisions` repo, which curates US OCD divisions; this repo curates
political parties and organizations.

Schema is structured as a discriminated union: each `type` value
dispatches to a specific subclass.

Class hierarchy:

    BaseEntity (universal: id, name, type, parent, lifecycle, leadership,
                contacts, social, ids, links, sources, ...)
      ├─ Party          type=party
      └─ Organization   type=org   (with `classification` for subtype)

Slug convention (full official name, lowercased + snake_cased — no
abbreviations or nicknames; see CLAUDE.md):

    vb-org/party:democratic
    vb-org/party:democratic/state:ca       # state-level affiliate
    vb-org/advocacy:american_civil_liberties_union
    vb-org/union:service_employees_international_union
    vb-org/think_tank:heritage_foundation
    vb-org/coalition:america_votes

File path is derived mechanically from the id (analogous to divisions):

    data/party/democratic.yml
    data/party/state/democratic-ca.yml     # state affiliates flatten parent slug
    data/advocacy/american_civil_liberties_union.yml
    data/think_tank/heritage_foundation.yml

A `paths.py` module (not yet written) should enforce id ↔ path
consistency in the linter.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    TypeAdapter,
    field_validator,
    model_validator,
)

from organizations.paths import parse_vb_org_id

# ---------------------------------------------------------------------------
# Base configs
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Shared sub-objects
# ---------------------------------------------------------------------------


class Link(_Base):
    url: HttpUrl
    note: str | None = None


class Source(_Base):
    url: HttpUrl
    note: str | None = None
    accessed: date | None = None


class Contact(_Base):
    """A contact point: HQ, press, donor relations, members services, etc.

    `classification` lets consumers filter without string-matching free-form
    notes. Common classifications: ``hq``, ``press``, ``donor``, ``members``,
    ``main``, ``mailing``.
    """

    classification: str
    name: str | None = None
    url: HttpUrl | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    note: str | None = None


SocialPlatform = Literal[
    "twitter",
    "facebook",
    "instagram",
    "tiktok",
    "youtube",
    "bluesky",
    "mastodon",
    "threads",
    "linkedin",
    "reddit",
    "rumble",
    "truth_social",
    "telegram",
]


class Social(_Base):
    """A social-media presence."""

    platform: SocialPlatform
    handle: str | None = None
    url: HttpUrl | None = None
    verified: bool | None = None


class Person(_Base):
    """A person record — leader, founder, key staffer.

    Lightweight; not a primary entity. For first-class person records,
    consumers should reference `openstates/people` (via the `openstates`
    key in `ids`) rather than maintaining biographies here.
    """

    name: str
    role: str | None = None  # "chair", "executive_director", "president", "founder"
    start_date: date | None = None
    end_date: date | None = None
    ids: dict[str, str] = Field(default_factory=dict)
    note: str | None = None


class SameAs(_Base):
    """A cross-reference to another entity that is the same real-world thing."""

    id: str
    note: str | None = None


class OtherName(_Base):
    name: str
    start_date: date | None = None
    end_date: date | None = None


# ---------------------------------------------------------------------------
# Base entity — universal fields shared by all types
# ---------------------------------------------------------------------------


class BaseEntity(_Base):
    """Universal fields present on every entity regardless of type."""

    # Required
    id: str
    name: str
    type: str  # narrowed to a Literal in each subclass

    # Identity & lifecycle
    short_name: str | None = None
    abbreviation: str | None = None
    aliases: list[str] = Field(default_factory=list)
    other_names: list[OtherName] = Field(default_factory=list)
    summary: str | None = None
    motto: str | None = None
    mission: str | None = None

    parent: str | None = None
    same_as: list[SameAs] = Field(default_factory=list)
    successor: str | None = None  # if dissolved/renamed/merged

    founded: date | None = None
    dissolved: date | None = None
    headquarters: str | None = None  # ocd-division/... id of HQ city/state

    # The OCD division this entity operates within (scope of operation,
    # not HQ location). Set when the entity is bound to a state or smaller
    # jurisdiction — e.g. state party affiliates, state-level PACs, a
    # city-only advocacy group. Leave unset for nationally-scoped entities;
    # consumers default to country:us.
    jurisdiction: str | None = None

    website: HttpUrl | None = None
    logo: HttpUrl | None = None

    leadership: list[Person] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    social: list[Social] = Field(default_factory=list)

    # Recommended `ids` vocabulary (linter does not enforce keys, but prefer
    # these): wikidata, wikipedia, ballotpedia, fec, ein, opensecrets,
    # guidestar, gnis, openstates_organization, osm_relation, twitter_id.
    ids: dict[str, str] = Field(default_factory=dict)
    links: list[Link] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    extras: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def _valid_vb_org_id(cls, v: str) -> str:
        parse_vb_org_id(v)
        return v

    @field_validator("parent")
    @classmethod
    def _valid_optional_parent(cls, v: str | None) -> str | None:
        if v is None:
            return v
        parse_vb_org_id(v)
        return v

    @field_validator("headquarters", "jurisdiction")
    @classmethod
    def _valid_ocd_division_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith("ocd-division/"):
            raise ValueError(f"must be an ocd-division/... id: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Party
# ---------------------------------------------------------------------------


PartyClassification = Literal[
    "major",       # current major US party (Dem, Rep)
    "minor",       # active minor party with national presence (Green, Lib, ...)
    "regional",    # active in some states only
    "historical",  # dissolved
]

PartyLevel = Literal["national", "state", "local"]


class Party(BaseEntity):
    """A political party — national, state-level affiliate, or local chapter."""

    type: Literal["party"]

    classification: PartyClassification | None = None
    level: PartyLevel | None = None  # national / state / local affiliate
    color: str | None = None         # canonical brand color, e.g. "#0015BC"
    ideology: list[str] = Field(default_factory=list)  # short tags
    platform_url: HttpUrl | None = None  # current platform document

    @model_validator(mode="after")
    def _check_id_root(self) -> "Party":
        parsed = parse_vb_org_id(self.id)
        if parsed.root_type != "party":
            raise ValueError(
                f"Party id root segment must be 'party', got "
                f"{parsed.root_type!r} (in {self.id!r})"
            )
        return self


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


OrgClassification = Literal[
    "advocacy",                # 501(c)(4) advocacy groups
    "pac",                     # FEC-registered political action committee
    "super_pac",               # independent-expenditure-only PAC
    "527",                     # political committee not registered with FEC
    "union",                   # labor union
    "trade_association",       # industry trade group
    "professional_association",
    "think_tank",
    "foundation",              # 501(c)(3) grantmaking
    "research",                # research institute (non-grantmaking)
    "religious",               # faith-based advocacy / religious lobby
    "media",                   # news outlet
    "ngo",                     # non-political NGO with civic involvement
    "coalition",               # alliance of orgs
    "caucus",                  # legislative caucus or formal party faction
    "political_committee",     # umbrella for committees not otherwise classified
]


PoliticalLean = Literal[
    "left",
    "center_left",
    "center",
    "center_right",
    "right",
    "nonpartisan",
    "varies",
]


TaxStatus = Literal[
    "501c3",
    "501c4",
    "501c5",
    "501c6",
    "527",
    "for_profit",
    "government",
    "other",
]


class Organization(BaseEntity):
    """Any non-party political organization: PAC, union, advocacy group,
    think tank, coalition, caucus, media outlet, etc.
    """

    type: Literal["org"]

    classification: OrgClassification
    political_lean: PoliticalLean | None = None
    tax_status: TaxStatus | None = None
    ein: str | None = None     # IRS Employer Identification Number
    fec_id: str | None = None  # FEC committee ID

    # For coalitions/parent orgs: list of member-org ids (vb-org/...).
    members: list[str] = Field(default_factory=list)

    # If the org is formally affiliated with a party (e.g. DCCC ↔ Dem Party).
    affiliated_party: str | None = None

    issues: list[str] = Field(default_factory=list)  # short topic tags

    @field_validator("affiliated_party")
    @classmethod
    def _valid_party_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith("vb-org/party:"):
            raise ValueError(
                f"affiliated_party must be a vb-org/party:... id: {v!r}"
            )
        return v

    @field_validator("members", mode="after")
    @classmethod
    def _valid_member_ids(cls, v: list[str]) -> list[str]:
        for m in v:
            parse_vb_org_id(m)
        return v

    @model_validator(mode="after")
    def _check_id_classification(self) -> "Organization":
        parsed = parse_vb_org_id(self.id)
        if parsed.root_type != self.classification:
            raise ValueError(
                f"Organization id root segment ({parsed.root_type!r}) does "
                f"not match classification ({self.classification!r})"
            )
        return self


# ---------------------------------------------------------------------------
# Discriminated union
# ---------------------------------------------------------------------------


# `Entity` is a TypeAdapter for the discriminated union. Use
# `Entity.validate_python(raw)` to parse arbitrary YAML into the appropriate
# subclass based on the `type` field.
Entity = TypeAdapter(
    Annotated[
        Union[Party, Organization],
        Field(discriminator="type"),
    ]
)


ENTITY_CLASSES: tuple[type[BaseEntity], ...] = (Party, Organization)
