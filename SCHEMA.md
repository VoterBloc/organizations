# Organizations Schema

This document defines the YAML schema used in this repository to describe
US **political parties** and **political organizations** (PACs, unions,
advocacy groups, think tanks, foundations, coalitions, legislative
caucuses, religious lobbies, media outlets, and other politically-active
non-individual entities).

The repo is scoped to the US. The `vb-org/...` id scheme assumes a
single country; cross-country expansion would require a new prefix.

The schema is intentionally **stack-agnostic**. It records facts about
entities that are true regardless of which application reads them.
Consumer-specific projections — display order, status workflows,
AI-augmented prose, code-format conventions — live in the consumer.
See `CLAUDE.md` for the full design principle.

## Relationship to other ecosystems

This repo is complementary to several existing datasets:

- **[`VoterBloc/divisions`](https://github.com/VoterBloc/divisions)** is
  the sibling repo for [OCD divisions](https://open-civic-data.readthedocs.io/en/latest/proposals/0002.html)
  (states, counties, cities, congressional districts). Fields here
  reference OCD divisions via `ocd-division/...` ids in `headquarters`
  and `jurisdiction`.
- **[`openstates/people`](https://github.com/openstates/people)** is the
  canonical source for individual elected officials. We do **not**
  duplicate person records here — leadership entries are lightweight
  pointers (`Person.ids: openstates: ...`) into that repo.
- **[Wikidata](https://www.wikidata.org/)** holds many of the same
  entities. We add hand-curated metadata that Wikidata is missing or
  wrong about. Always include the Wikidata QID under `ids: wikidata:
  ...` so consumers can join the two.

## Scope

What belongs in a file:

- Names, abbreviations, aliases, and historical names.
- Mission statement (1–3 sentences), motto, ideology / issue tags.
- Founding / dissolution dates.
- Headquarters and operational jurisdiction (as `ocd-division/...` ids).
- Leadership (current chair, executive director, founder, etc.).
- Official contact info (HQ, press, donor relations).
- Social media presence.
- Curated external identifiers (FEC, EIN, Wikidata, Ballotpedia, …).
- Sources (every file should have at least one).

What does **not** belong:

- Long-form narrative (`intro`, `history`, `current_positions`,
  `notable_leaders`, `notable_actions`) — those live in voterbloc's
  enrichment tables.
- Officials / politicians — use `openstates/people`.
- Cycle-bound items: candidates, contests, ballot measures, individual
  endorsements, FEC contribution records.
- OCD divisions themselves — use the `divisions` sibling repo.
- Display order, claim status, projection rules, importer fallbacks —
  consumer-specific concerns.

See `CLAUDE.md` for the rationale (the "facts here, projections in
consumers" principle).

## ID scheme

Every entity has a `vb-org/...` id. The id structure encodes the entity's
classification and a slug:

```
vb-org/{classification}:{slug}                       # flat id (most entities)
vb-org/{classification}:{slug}/{sub-type}:{sub-slug} # nested (state-level affiliates)
```

Concrete examples:

```
vb-org/party:democratic
vb-org/party:democratic/state:ca           # CA Democratic Party
vb-org/advocacy:american_civil_liberties_union
vb-org/union:service_employees_international_union
vb-org/think_tank:heritage_foundation
vb-org/coalition:america_votes
vb-org/caucus:congressional_progressive_caucus
```

The id's root segment **must equal** the YAML's `classification` field.
Both `vb-org/party:democratic` (classification: party) and
`vb-org/advocacy:aclu` (classification: advocacy) are validated this way.

### Slug convention

The slug is the entity's **full official name, lowercased and
snake_cased**. No abbreviations, no nicknames. Short forms live in the
`abbreviation:` and `aliases:` fields.

- `vb-org/party:democratic`, never `:dem` or `:democrat`
- `vb-org/party:republican`, never `:gop`
- `vb-org/advocacy:american_civil_liberties_union`, never `:aclu`

This matches OCD-style slugs in the sister `divisions` repo
(`place:los_angeles`, never `place:la`).

## File layout

Files live under `data/`. Path is derived mechanically from the id:

```
data/
  party/
    democratic.yml                 # vb-org/party:democratic
    republican.yml
    green.yml
    state/
      democratic-ca.yml            # vb-org/party:democratic/state:ca
  advocacy/
    american_civil_liberties_union.yml
  union/
    service_employees_international_union.yml
  think_tank/
    heritage_foundation.yml
  pac/
  super_pac/
  527/
  trade_association/
  professional_association/
  foundation/
  research/
  religious/
  media/
  ngo/
  coalition/
  caucus/
  political_committee/
```

The directory is the OCD-style classification segment, **verbatim and
singular** (`union/`, `think_tank/`, never pluralized). The filename
(minus `.yml`) is the id's last-segment slug exactly. Use
`organizations path <vb-org-id>` to compute a path.

## Top-level shape

There is one entity class, `Organization`. A party is just an
`Organization` whose `classification` is `party`. There is no separate
`Party` class — see `CLAUDE.md` for why (short version: parties are
organizations, and the split was mirroring voterbloc's table boundaries
rather than a fact about the data).

## Required fields

| Field            | Type   | Notes                                                                          |
| ---------------- | ------ | ------------------------------------------------------------------------------ |
| `id`             | string | `vb-org/...` id; validated by `parse_vb_org_id`.                              |
| `name`           | string | Canonical display name, e.g. "Democratic Party".                              |
| `classification` | enum   | One of the values in [Classification values](#classification-values) below.   |

## Optional fields

### Identity

| Field          | Type                | Notes                                                                                                        |
| -------------- | ------------------- | ------------------------------------------------------------------------------------------------------------ |
| `short_name`   | string              | Terser display form, e.g. "Democrats", "ACLU".                                                              |
| `abbreviation` | string              | The short form / acronym (e.g. `DEM`, `ACLU`).                                                              |
| `member_label` | string              | Singular label for an individual affiliated with the entity — for parties, the singular demonym (e.g. "Democrat", "Republican"). Use the form that would appear next to a person's name. Leave empty when no natural singular label exists. |
| `aliases`      | list\[string]       | Alternate names the entity is known by.                                                                     |
| `other_names`  | list\[object]       | Historical / alternate names: `{name, start_date?, end_date?}`. Same shape as openstates/people.            |
| `summary`      | string              | 1–3 sentence factual overview. Used as input/fallback for downstream enrichment.                             |
| `mission`      | string              | Mission statement (verbatim or paraphrased).                                                                 |
| `motto`        | string              | Official motto.                                                                                              |

### Lifecycle & relationships

| Field          | Type                | Notes                                                                                                        |
| -------------- | ------------------- | ------------------------------------------------------------------------------------------------------------ |
| `parent`       | string              | `vb-org/...` id of a parent entity (e.g. state party → national party).                                     |
| `same_as`      | list\[object]       | Cross-references to other ids that point to the same real-world entity: `{id, note?}`.                       |
| `successor`    | string              | `vb-org/...` id of a successor entity if this one was renamed/merged into another.                          |
| `founded`      | date                | ISO 8601 (`YYYY-MM-DD`). Optional — Wikidata often has this.                                                |
| `dissolved`    | date                | When the entity ceased to exist, if applicable.                                                              |
| `headquarters` | string              | `ocd-division/...` id of where the entity is **physically headquartered**.                                  |
| `jurisdiction` | string              | `ocd-division/...` id describing the entity's **scope of operation**. Unset = nationally scoped.            |

### Branding

| Field     | Type          | Notes                                                                                                        |
| --------- | ------------- | ------------------------------------------------------------------------------------------------------------ |
| `website` | string (url)  | Official homepage.                                                                                           |
| `logo`    | string (url)  | URL to a canonical free-license logo. See [Logo policy](#logo-policy).                                       |
| `colors`  | list\[string] | Brand colors as 6-digit hex (`^#[0-9A-Fa-f]{6}$`). **The first entry is the primary** brand color; subsequent entries are secondary / accent in declared order. |

### People & contact

| Field        | Type           | Notes                                                       |
| ------------ | -------------- | ----------------------------------------------------------- |
| `leadership` | list\[Person]  | Current leaders. See [Person](#person).                     |
| `contacts`   | list\[Contact] | Contact channels. See [Contact](#contact).                  |
| `social`     | list\[Social]  | Social-media presence. See [Social](#social).               |

### Political positioning

| Field            | Type          | Notes                                                                                            |
| ---------------- | ------------- | ------------------------------------------------------------------------------------------------ |
| `political_lean` | enum          | `left`, `center_left`, `center`, `center_right`, `right`, `nonpartisan`, `varies`.              |
| `ideology`       | list\[string] | Short tags: `liberal`, `progressive`, `conservative`, `green_politics`, etc.                    |
| `issues`         | list\[string] | Short topic tags: `voting_rights`, `civil_liberties`, `labor_rights`, etc.                      |

### Legal / financial

| Field        | Type   | Notes                                                                                            |
| ------------ | ------ | ------------------------------------------------------------------------------------------------ |
| `tax_status` | enum   | `501c3`, `501c4`, `501c5`, `501c6`, `527`, `for_profit`, `government`, `other`.                 |
| `ein`        | string | IRS Employer Identification Number.                                                              |
| `fec_id`     | string | FEC committee ID.                                                                                |

### Org-to-org relationships

| Field              | Type          | Notes                                                                                            |
| ------------------ | ------------- | ------------------------------------------------------------------------------------------------ |
| `members`          | list\[string] | For coalitions / parent orgs: `vb-org/...` ids of member orgs.                                  |
| `affiliated_party` | string        | `vb-org/party:...` id if formally affiliated with a party (e.g. DCCC ↔ Democratic Party).        |

### Documents

| Field          | Type         | Notes                                              |
| -------------- | ------------ | -------------------------------------------------- |
| `platform_url` | string (url) | Current platform / position document.              |

### External references

| Field     | Type                | Notes                                                                                            |
| --------- | ------------------- | ------------------------------------------------------------------------------------------------ |
| `ids`     | map\[string,string] | External identifiers. See [external identifier vocabulary](#external-identifier-vocabulary).    |
| `links`   | list\[Link]         | Related URLs: `{url, note?}`.                                                                    |
| `sources` | list\[Source]       | Where the data came from: `{url, note?, accessed?}`. **Every file should have at least one entry.** |
| `extras`  | object              | Unvalidated free-form map. Namespace keys when open-sourcing (e.g. `voterbloc.foo`).            |

## Classification values

| Value                       | Description                                      |
| --------------------------- | ------------------------------------------------ |
| `party`                     | Political party (national, state-affiliate, or local chapter). |
| `advocacy`                  | 501(c)(4) advocacy group.                        |
| `pac`                       | FEC-registered political action committee.       |
| `super_pac`                 | Independent-expenditure-only PAC.                |
| `527`                       | Political committee not registered with FEC.     |
| `union`                     | Labor union.                                     |
| `trade_association`         | Industry trade group.                            |
| `professional_association`  | Professional membership organization.            |
| `think_tank`                | Policy research org with normative agenda.       |
| `foundation`                | 501(c)(3) grantmaking.                           |
| `research`                  | Research institute (non-grantmaking).            |
| `religious`                 | Faith-based advocacy / religious lobby.          |
| `media`                     | News outlet with editorial slant.                |
| `ngo`                       | Non-political NGO with civic involvement.        |
| `coalition`                 | Alliance of orgs.                                |
| `caucus`                    | Legislative caucus or formal party faction.      |
| `political_committee`       | Umbrella for committees not otherwise classified. |

## Validation rules

The pydantic model enforces:

- `id` must parse as a `vb-org/...` id.
- `id`'s root segment must equal `classification`.
- `parent`, `successor`, `same_as[].id`, `members[]` must all parse as `vb-org/...` ids.
- `headquarters`, `jurisdiction` must start with `ocd-division/`.
- `affiliated_party` must start with `vb-org/party:`.
- `colors[]` entries must match `^#[0-9A-Fa-f]{6}$`.
- An entity cannot reference itself via `parent`, `successor`, `same_as`, or `members`.
- Unknown top-level fields are rejected (`extra="forbid"`). Use `extras` for ad-hoc data.

## Sub-objects

### Link

```yaml
- url: https://example.org
  note: optional description
```

### Source

```yaml
- url: https://example.org
  note: optional description
  accessed: 2026-04-27
```

### Contact

A contact channel — HQ, press, donor relations, etc.

```yaml
- classification: hq          # hq | press | donor | members | main | mailing | ...
  name: Headquarters
  url: https://example.org/contact
  phone: "+1 555 0100"
  email: contact@example.org
  address: 123 Main St, City, ST 00000
  note: optional
```

`classification` is required so consumers can filter without
string-matching free-form notes.

### Social

```yaml
- platform: twitter           # see SocialPlatform enum
  handle: "@example"
  url: https://twitter.com/example
  verified: true
```

`SocialPlatform` values: `twitter`, `facebook`, `instagram`, `tiktok`,
`youtube`, `bluesky`, `mastodon`, `threads`, `linkedin`, `reddit`,
`rumble`, `truth_social`, `telegram`.

### Person

A lightweight person record — leader, founder, key staffer.
**Not** a first-class entity. For full person records, reference
`openstates/people` via `ids: openstates: ...`.

```yaml
- name: Jane Doe
  role: chair                 # chair | executive_director | president | founder | ceo | …
  start_date: 2023-01-01
  end_date: 2026-04-27
  ids:
    openstates: <openstates id>
    wikidata: Q...
  note: optional
```

### SameAs

```yaml
- id: vb-org/party:democratic
  note: previous name
```

`id` is validated as a `vb-org/...` id.

### OtherName

```yaml
- name: Grand Old Party
  start_date: 1875-01-01
  end_date: null
```

## External identifier vocabulary

The `ids` field is an open `dict[str, str]`. The linter does not enforce
keys, but **prefer these names** so consumers can join across entities:

| Key                       | What                                              |
| ------------------------- | ------------------------------------------------- |
| `wikidata`                | Wikidata QID (e.g. `Q29552`).                    |
| `wikipedia`               | Wikipedia article slug or URL fragment.           |
| `ballotpedia`             | Ballotpedia article slug.                         |
| `fec`                     | FEC committee ID.                                |
| `ein`                     | IRS Employer Identification Number.               |
| `opensecrets`             | OpenSecrets organization ID.                      |
| `guidestar`               | GuideStar / Candid org ID.                        |
| `openstates_organization` | OpenStates org id (for legislative caucuses).     |
| `osm_relation`            | OpenStreetMap relation id (for HQ).               |
| `twitter_id`              | Twitter/X numeric account ID (stable across handle changes). |

If you need a key that's not on this list, add it under a namespaced
prefix (e.g. `voterbloc.internal_id`) or place it in `extras`.

## Logo policy

`logo:` should point to a **canonical free-license source** — Wikimedia
Commons preferred, the entity's own official logo URL as fallback.

- Do not vendor logo files into this repo (most are trademarked; the
  CC0 license here covers our text, not someone else's trademark).
- Do not point at consumer-specific CDNs.
- Where a production app actually serves the bytes from
  (fetch-and-cache, own CDN, etc.) is a consumer concern, not ours.

## JSON Schema

A JSON Schema export of the `Organization` model lives at
`schema/entity.schema.json`. It is **regenerated** from `models.py` —
do not hand-edit. To rebuild:

```sh
.venv/bin/organizations schema
```

The generated schema is committed so non-Python consumers can validate
without a Python toolchain.
