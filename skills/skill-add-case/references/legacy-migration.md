# Migrating Skill-owned cases

Migration is a requested maintainer operation, not an automatic side effect of
ordinary submissions. The canonical public store is `lovstudio/skills` at
`cases/cases.json`. Each case owns its ID, content, public assets and `skillIds`.
The website fetches this source dynamically; no copied data in website source.

1. Inventory the live catalog and every existing showcase source, including
   public mirrors of paid Skills. Record source URLs, original IDs, full public
   fields, image resolution and failures. Articles remain articles. Local drafts
   and uncommitted examples are outside the published inventory.
2. Refuse partial inventories. Generate a reviewable migration report before any
   remote write. Retain an exact local snapshot of each original public record.
3. Assign a deterministic global ID to missing or conflicting legacy IDs. Match
   duplicates using exact normalized public content, including images and
   Input/Prompt/Output; equal titles or IDs alone are insufficient. Merge all
   actual Skill associations and retain each source in `legacy` provenance.
4. Preserve language variants, testimonials, evidence, custom public fields and
   Session access/prices. Resolve relative assets against their original source;
   never silently convert a paid Session or substitute generated images.
5. Preserve old source files as historical records. New writes go only to the
   shared registry. Old `/skills/<skill>/cases/<old-id>` routes resolve provenance
   and redirect to `/cases/<global-id>`. Transitional reads must not duplicate
   an already migrated case on its Skill page.
6. Publish the reviewed registry atomically and fast-forward only. A rerun is
   idempotent and preserves new submissions made after the initial migration.
   Check registry size before writing; the current service limit is 900 KB.
7. Verify record counts, relation counts, content equality, distinct ID
   collisions, repeat migration, all old link mappings and reachable assets.
   Then verify the collection and related Skill pages from the deployed website.
   Report pre-existing broken assets separately from migration defects.

The website repository contains executable maintainers' tools:
`scripts/cases/inventory.mjs` and `scripts/cases/migrate.mjs`. They write local
review files only. The user’s migration authorization governs a later source
commit; script completion alone does not prove publication or website rendering.
