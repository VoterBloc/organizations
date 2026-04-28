# organizations

Hand-curated YAML metadata for US political parties and political
organizations — sibling to [`divisions`](../divisions), which curates US
[OCD divisions](https://open-civic-data.readthedocs.io/en/latest/proposals/0002.html).

One file per entity, keyed by a `vb-org/...` id. Inspired by
`openstates/people` and the `divisions` repo.

**US-only.** Don't add country scoping for other nations.

## Scope

This repo curates entities that are:

1. **Stable / slow-changing** — not user-generated, not transactional.
2. **Hard to source programmatically** — mottos, leadership, mission
   statements, governance structure, official contact info, identifiers
   and links.
3. Worth version-controlling as hand-edited YAML.

In scope: parties (national + state affiliates), advocacy groups, PACs,
super PACs, unions, trade associations, think tanks, foundations,
religious lobbies, media outlets, coalitions, legislative caucuses, and
party factions.

Out of scope (use other sources):

- Officials / politicians — use [openstates/people].
- OCD divisions — use the `divisions` sibling repo.
- Bills, votes, committees — use Congress.gov / OpenStates.
- Candidates, contests, ballot measures — cycle-bound; live in voterbloc.
- FEC committee transactions — use OpenFEC directly.

[openstates/people]: https://github.com/openstates/people

## Layout

```
data/
  party/                   parties (national)
    dem.yml, gop.yml, grn.yml, ...
    state/                 state-level affiliates (one file each)
  advocacy/                advocacy groups (501c4)
  pac/                     FEC-registered PACs
  super_pac/               independent-expenditure-only PACs
  union/                   labor unions
  trade_association/       industry trade groups
  think_tank/              policy research orgs
  foundation/              501c3 grantmaking
  religious/               religious lobbies / faith advocacy
  media/                   news outlets
  coalition/               alliances of orgs
  caucus/                  legislative caucuses & party factions
```

The directory is the OCD-style classification segment, verbatim and
singular (e.g. `union/`, not `unions/`). The filename (minus `.yml`) is
the id's last-segment slug.

## ID scheme

```
vb-org/party:democratic
vb-org/party:democratic/state:ca           # state affiliate
vb-org/advocacy:american_civil_liberties_union
vb-org/union:service_employees_international_union
vb-org/think_tank:heritage_foundation
vb-org/coalition:america_votes
```

## Slug convention

The slug is the entity's **full official name, lowercased and snake_cased**.
No abbreviations, no nicknames. This matches OCD-style slugs in the
sister `divisions` repo (`place:los_angeles`, not `place:la`).

- `democratic`, not `dem`
- `republican`, not `gop` (GOP is a nickname, not the legal name)
- `american_civil_liberties_union`, not `aclu`
- `service_employees_international_union`, not `seiu`

The `abbreviation:` field carries the short form (`abbreviation: DEM`,
`abbreviation: ACLU`) for consumers that need it. Common short forms
also belong in `aliases:`.

## Schema

There is one entity class, `Organization`, defined in
`src/organizations/models.py` (pydantic). A party is just an
`Organization` whose `classification` is `party`. Other classification
values cover advocacy groups, PACs, unions, think tanks, foundations,
coalitions, legislative caucuses, religious lobbies, media outlets, and
more — see [`SCHEMA.md`](./SCHEMA.md) for the full list.

For a human-readable reference with field tables, sub-object shapes, and
validation rules, see [`SCHEMA.md`](./SCHEMA.md). A JSON Schema export
of the model is committed at `schema/entity.schema.json` — regenerate
it after model changes with `.venv/bin/organizations schema`.

## License

Public domain under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
