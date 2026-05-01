"""Pydantic models for the organizations YAML schema.

This is the canonical definition of the schema. The JSON Schema export
at `schema/entity.schema.json` is regenerated from this module; the
human-readable `SCHEMA.md` is kept in sync by hand.

The schema has a **single** entity class, `Organization`. The
`classification` field discriminates among kinds: parties (`party`),
PACs, advocacy groups, unions, think tanks, foundations, coalitions,
legislative caucuses, religious lobbies, media outlets, etc.

A party is just an organization whose `classification` is `party`.
There is no separate `Party` class — see `CLAUDE.md` "facts here,
projections in consumers" for why.

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
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from organizations.paths import parse_vb_org_id

# ---------------------------------------------------------------------------
# Base config
# ---------------------------------------------------------------------------


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ---------------------------------------------------------------------------
# Sub-objects
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

    `classification` lets consumers filter without string-matching
    free-form notes. Common classifications: ``hq``, ``press``,
    ``donor``, ``members``, ``main``, ``mailing``.
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
    consumers should reference `openstates/people` (via the
    `openstates` key in `ids`) rather than maintaining biographies here.
    """

    name: str
    role: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    ids: dict[str, str] = Field(default_factory=dict)
    note: str | None = None


class SameAs(_Base):
    """A cross-reference to another entity that is the same real-world thing."""

    id: str
    note: str | None = None

    @field_validator("id")
    @classmethod
    def _valid_vb_org_id(cls, v: str) -> str:
        parse_vb_org_id(v)
        return v


class OtherName(_Base):
    name: str
    start_date: date | None = None
    end_date: date | None = None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


Classification = Literal[
    # Parties
    "party",
    # Political organizations
    "advocacy",                 # 501(c)(4) advocacy groups
    "pac",                      # FEC-registered political action committee
    "super_pac",                # independent-expenditure-only PAC
    "527",                      # political committee not registered with FEC
    "union",                    # labor union
    "trade_association",        # industry trade group
    "professional_association",
    "think_tank",
    "foundation",               # 501(c)(3) grantmaking
    "research",                 # research institute (non-grantmaking)
    "religious",                # faith-based advocacy / religious lobby
    "media",                    # news outlet
    "ngo",                      # non-political NGO with civic involvement
    "coalition",                # alliance of orgs
    "caucus",                   # legislative caucus or formal party faction
    "political_committee",      # umbrella for committees not otherwise classified
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


_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ---------------------------------------------------------------------------
# Organization — the only entity class
# ---------------------------------------------------------------------------


class Organization(_Base):
    """Any politically-active non-individual entity in the curated dataset.

    Discriminated by `classification`: parties (`party`), advocacy
    groups, PACs, unions, think tanks, foundations, coalitions,
    legislative caucuses, religious lobbies, media outlets, etc.
    """

    # ----------------------------------------------------------------------
    # Required
    # ----------------------------------------------------------------------

    id: str
    name: str
    classification: Classification

    # ----------------------------------------------------------------------
    # Identity
    # ----------------------------------------------------------------------

    short_name: str | None = None
    abbreviation: str | None = None

    # Singular label for an individual affiliated with the entity — for
    # parties, the singular demonym used to describe one member (e.g.
    # "Democrat", "Republican", "Libertarian"). Use the form that would
    # appear next to a person's name. Leave empty when no natural
    # singular label exists (e.g. "Working Families Party member").
    member_label: str | None = None

    aliases: list[str] = Field(default_factory=list)
    other_names: list[OtherName] = Field(default_factory=list)
    summary: str | None = None
    mission: str | None = None
    motto: str | None = None

    # ----------------------------------------------------------------------
    # Lifecycle & relationships
    # ----------------------------------------------------------------------

    parent: str | None = None
    same_as: list[SameAs] = Field(default_factory=list)
    successor: str | None = None  # if dissolved/renamed/merged

    founded: date | None = None
    dissolved: date | None = None

    # The OCD division where the entity is *physically headquartered*.
    headquarters: str | None = None

    # The OCD division this entity *operates within* (scope of operation,
    # not HQ location). Set when the entity is bound to a state or
    # smaller jurisdiction — e.g. state party affiliates, state PACs, a
    # city-only advocacy group. Leave unset for nationally-scoped
    # entities; consumers default to country:us.
    jurisdiction: str | None = None

    # ----------------------------------------------------------------------
    # Branding
    # ----------------------------------------------------------------------

    website: HttpUrl | None = None
    logo: HttpUrl | None = None

    # Brand colors as 6-digit hex (e.g. "#0015BC"). The **first entry is
    # the primary** brand color; subsequent entries are secondary /
    # accent colors in declared order. Empty list = no curated colors.
    colors: list[str] = Field(default_factory=list)

    # ----------------------------------------------------------------------
    # People & contact
    # ----------------------------------------------------------------------

    leadership: list[Person] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    social: list[Social] = Field(default_factory=list)

    # ----------------------------------------------------------------------
    # Political positioning
    # ----------------------------------------------------------------------

    political_lean: PoliticalLean | None = None
    ideology: list[str] = Field(default_factory=list)  # short tags
    issues: list[str] = Field(default_factory=list)    # short topic tags

    # ----------------------------------------------------------------------
    # Legal / financial
    # ----------------------------------------------------------------------

    tax_status: TaxStatus | None = None
    ein: str | None = None     # IRS Employer Identification Number
    fec_id: str | None = None  # FEC committee ID

    # ----------------------------------------------------------------------
    # Org relationships
    # ----------------------------------------------------------------------

    # For coalitions / parent orgs: list of member-org ids (vb-org/...).
    members: list[str] = Field(default_factory=list)

    # If formally affiliated with a party (e.g. DCCC ↔ Democratic Party).
    affiliated_party: str | None = None

    # ----------------------------------------------------------------------
    # Documents
    # ----------------------------------------------------------------------

    platform_url: HttpUrl | None = None  # platform / position document

    # ----------------------------------------------------------------------
    # External references
    # ----------------------------------------------------------------------

    # Recommended `ids` vocabulary (linter does not enforce keys, but
    # prefer these): wikidata, wikipedia, ballotpedia, fec, ein,
    # opensecrets, guidestar, openstates_organization, osm_relation,
    # twitter_id.
    ids: dict[str, str] = Field(default_factory=dict)
    links: list[Link] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    # ----------------------------------------------------------------------
    # Extension
    # ----------------------------------------------------------------------

    extras: dict[str, Any] = Field(default_factory=dict)

    # ----------------------------------------------------------------------
    # Field validators
    # ----------------------------------------------------------------------

    @field_validator("id")
    @classmethod
    def _valid_vb_org_id(cls, v: str) -> str:
        parse_vb_org_id(v)
        return v

    @field_validator("parent", "successor")
    @classmethod
    def _valid_optional_vb_org_id(cls, v: str | None) -> str | None:
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

    @field_validator("members")
    @classmethod
    def _valid_member_ids(cls, v: list[str]) -> list[str]:
        for m in v:
            parse_vb_org_id(m)
        return v

    @field_validator("colors")
    @classmethod
    def _valid_colors(cls, v: list[str]) -> list[str]:
        for c in v:
            if not _HEX_COLOR_RE.match(c):
                raise ValueError(
                    f"colors entries must be 6-digit hex (e.g. '#0015BC'): {c!r}"
                )
        return v

    # ----------------------------------------------------------------------
    # Model validators
    # ----------------------------------------------------------------------

    @model_validator(mode="after")
    def _check_id_classification(self) -> "Organization":
        parsed = parse_vb_org_id(self.id)
        if parsed.root_type != self.classification:
            raise ValueError(
                f"id root segment ({parsed.root_type!r}) does not match "
                f"classification ({self.classification!r})"
            )
        return self

    @model_validator(mode="after")
    def _check_no_self_reference(self) -> "Organization":
        if self.parent == self.id:
            raise ValueError(f"entity cannot be its own parent: {self.id!r}")
        if self.successor == self.id:
            raise ValueError(f"entity cannot be its own successor: {self.id!r}")
        for sa in self.same_as:
            if sa.id == self.id:
                raise ValueError(
                    f"entity cannot reference itself via same_as: {self.id!r}"
                )
        if self.id in self.members:
            raise ValueError(
                f"entity cannot list itself in members: {self.id!r}"
            )
        return self
