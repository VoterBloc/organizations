# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Purpose

Hand-curated YAML metadata for US political **parties** and **political
organizations** — PACs, unions, advocacy groups, think tanks, coalitions,
caucuses, etc. One file per entity, keyed by `vb-org/...` id. Sibling to
the `divisions` repo (OCD divisions) and inspired by `openstates/people`.

**US-only.** Don't add country scoping for other nations.

## Design principle: facts here, projections in consumers

This repo holds **facts about entities** — values that are true
regardless of which application reads them. Founding dates, EINs,
member lists, leader names and roles, ideology tags, official
identifiers. Things a researcher, mobile app, or civic-tech project
would want as much as voterbloc would.

It does **not** hold consumer-specific projections: display order,
status workflows, AI-augmented prose, code-format conventions,
default-fill behavior, claim/verification state, or anything else
shaped by how a particular application uses the data. Those live in
the consumer.

**The test for a proposed field:** *would a competing consumer want
this field with the same value?* If two consumers would reasonably
want different values (display order, sort precedence), or one
wouldn't want it at all (verification status, importer fallbacks),
the field belongs in the consumer, not here.

The apparent purism is a strength, not a weakness. Decoupling means
voterbloc's tables can evolve without coordinating with curators,
*and* the dataset stays useful to anyone else who shows up. See
closed issues #3, #4, #5, and #6 for the principle applied.

## Architecture

There is **one entity class**, `Organization`, defined in
`src/organizations/models.py` (pydantic). A party is just an
`Organization` whose `classification` is `party`. There is no separate
`Party` class — parties are organizations, and splitting them was
mirroring voterbloc's table boundaries rather than a fact about the
data. See `SCHEMA.md` for the full field list.

After changing the model, regenerate the JSON Schema export
(`organizations schema`) and update `SCHEMA.md` by hand to keep the
human-readable doc in sync.

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

- **`classification` is the only top-level discriminator.** There is no
  `type` field. `classification: party` means "this is a party";
  `classification: advocacy` means "this is an advocacy group"; etc.
  See `SCHEMA.md` for the full list of values.
- **The id's root segment must equal `classification`.** A file with
  `classification: party` must have an id like `vb-org/party:...`. The
  linter enforces this.
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
- **`logo`** points to a canonical free-license source — prefer
  Wikimedia Commons; fall back to the entity's own official logo URL.
  Do not vendor logo files into this repo (most are trademarked and CC0
  doesn't cover trademarks) and do not point at consumer-specific CDNs.
  The field records *which* logo is canonical; how a production app
  serves it (fetch-and-cache, own CDN, etc.) is a consumer concern.
- **`colors`** is a list of 6-digit hex strings. **The first entry is
  the primary brand color**; subsequent entries are secondary / accent
  colors in declared order. Don't include white as the primary unless
  it's actually the brand's primary. Empty list (or omitted) means no
  curated colors — consumers should not invent values.
- **`ids` map has a recommended vocabulary**: `wikidata`, `wikipedia`,
  `ballotpedia`, `fec`, `ein`, `opensecrets`, `guidestar`,
  `openstates_organization`, `osm_relation`, `twitter_id`. Linter (when
  written) should not enforce keys, but prefer these.

## Scope — what belongs in a file

This repo is for data that is **hard to source programmatically**:
mission statements, mottos, leadership, founding history, official
contact info, curated identifiers and links, ideology tags, prose
summaries, classification, brand colors.

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
