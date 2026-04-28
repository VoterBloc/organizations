# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Purpose

Hand-curated YAML metadata for US political **parties** and **political
organizations** — PACs, unions, advocacy groups, think tanks, coalitions,
caucuses, etc. One file per entity, keyed by `vb-org/...` id. Sibling to
the `divisions` repo (OCD divisions) and inspired by `openstates/people`.

**US-only.** Don't add country scoping for other nations.

## Architecture

The schema has **one canonical definition**: `src/organizations/models.py`
(pydantic). After changing a model, downstream artifacts (JSON Schema,
human-readable `SCHEMA.md`) need to be regenerated/updated by hand.

File paths are derived mechanically from ids. Rules:

- `data/party/{slug}.yml` for national parties (e.g. `democratic`,
  `republican`, `green`).
- `data/party/state/{slug}-{state}.yml` for state affiliates
  (e.g. `democratic-ca.yml`).
- `data/{classification}/{slug}.yml` for everything else — **directory
  is the OCD-style classification segment, verbatim and singular**
  (`union/`, `think_tank/`, `advocacy/`, not pluralized).
- The filename (minus `.yml`) is the id's last-segment slug exactly.

## Slug convention

The slug (the part after `:` in a vb-org id, and the filename minus
`.yml`) is the entity's **full official name, lowercased and
snake_cased**. No abbreviations, no nicknames.

- `vb-org/party:democratic`, not `vb-org/party:dem`
- `vb-org/party:republican`, not `vb-org/party:gop`
- `vb-org/advocacy:american_civil_liberties_union`, not `:aclu`
- `vb-org/union:service_employees_international_union`, not `:seiu`

This matches OCD-style slugs in the sister `divisions` repo
(`place:los_angeles`, never `place:la`). The short forms live in
the `abbreviation:` and `aliases:` fields, which is where consumers
should look for them.

## Schema conventions easy to get wrong

- **`type` is `party` or `org`** — not the classification. The
  classification is a separate field on `org` entities.
- **`same_as` is a list of `{id, note}`** (not a string). Use for
  alternative ids that point to the same real-world entity.
- **`headquarters`** is an `ocd-division/...` id (cross-link to the
  `divisions` repo), not free-form text. It's the *physical* HQ.
- **`jurisdiction`** is an `ocd-division/...` id describing the entity's
  *scope of operation* (where it acts), not where it sits. National
  entities leave it unset; consumers default to `country:us`. Only set
  it when the entity is bound to a state or smaller jurisdiction
  (state party affiliates, state PACs, a city-only advocacy group).
- **`affiliated_party`** must be a `vb-org/party:...` id (e.g. DCCC
  affiliated with `vb-org/party:democratic`).
- **`members` on coalitions** is a list of `vb-org/...` ids of member orgs.
- **`ids` map has a recommended vocabulary**: `wikidata`, `wikipedia`,
  `ballotpedia`, `fec`, `ein`, `opensecrets`, `guidestar`,
  `openstates_organization`, `osm_relation`, `twitter_id`. Linter (when
  written) should not enforce keys, but prefer these.

## Scope — what belongs in a file

This repo is for data that is **hard to source programmatically**:
mission statements, mottos, leadership, founding history, official
contact info, curated identifiers and links, ideology tags, prose
summaries, classification.

Fields like `headquarters`, `founded`, `dissolved` *exist* but should be
left empty unless wikidata/wikipedia is wrong or missing for that entity.
Consumers of this data should prefer those sources for those facts.
Don't spend curation effort on them.

Every file should have at least one `sources:` entry.

### Prose / enrichment boundary

This repo holds **short factual prose** only: `summary` (1–3 sentence
overview), `mission`, `motto`, plus structured `leadership`. That's it.

**Do not add long-form narrative fields** to YAML or to `models.py`:
no `intro`, `history`, `current_positions`, `notable_leaders`,
`notable_actions`, or other narrative blocks. Those live in voterbloc's
enrichment tables (`party_enrichment`,
`political_organization_enrichment`).

The voterbloc enrichment pipeline:

1. Reads YAML prose (`summary`, `mission`, etc.) as **input** to its
   AI-generation step, and
2. Falls back to the YAML prose at read time when no enrichment row
   exists yet for an entity.

So curated YAML prose is both seed material and a safe default. AI
enrichment is the layer above it; editorial overrides happen in
voterbloc, not here.

If you find yourself wanting to write 3+ paragraphs of narrative into a
YAML file, that's a sign the content belongs in a voterbloc enrichment
override, not in this repo. (Decision recorded in #6, Option A.)

What does **not** belong:

- Officials / politicians (use `openstates/people`).
- Cycle-bound stuff: candidates, contests, ballot measures, individual
  endorsements, FEC contribution records.
- OCD divisions themselves (use the `divisions` sibling repo).
- Bills, votes, legislative committees.

## PR / edit discipline

- Minimize diffs. Don't reorder fields or reflow YAML when fixing a
  single value.
- New entity files must be populated with real verifiable data — no
  stubs. Cite sources.
- Prefer adding to existing files over creating new ones if a sub-entity
  could reasonably be modeled inline (e.g. don't split out a wholly
  controlled subsidiary as a separate file unless it has a meaningful
  independent identity).

## License

Public domain under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).
