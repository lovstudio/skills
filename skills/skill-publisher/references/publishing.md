# Publishing to Skill Publisher

This adapter turns validated local source into a GitHub-backed Skill Publisher release,
catalog entry, and verified live detail page.

## Inputs

- Local Skill source path.
- GitHub organization and desired repository visibility.
- The current `lov-skill-pricing` Pricing Card, including free/paid status,
  public CNY price or free-entry decision, confidence, and review trigger.
- Unified `lovstudio/skills` catalog checkout.
- Expected version and a release-specific visible marker.
- Revalidation secret resolved as `LOVSTUDIO_REVALIDATE_SECRET` without printing it.

## Source repository and release

A free Skill passes the public-copy gate below before any of these commands
pushes its content to a public repository. From the validated source directory:

```bash
python3 scripts/validate_skill.py .
git init -b main                         # only when source has no repository
git add -A
git commit -m "feat: initial release"
gh repo create ORG/NAME-skill --VISIBILITY --source=. --push
git tag vVERSION
git push origin vVERSION
gh release create vVERSION --generate-notes
```

For an existing repository, preserve its branch and history, update from the
remote first, commit only intended changes, then tag from the verified commit.
A free Skill whose source records its own distribution state is tagged later, on
the commit that records `live`; see "Free Skills: distribution state in two
steps".

### Public-copy gate for free Skills

A free, non-internal Skill is public even when its source repository is private:
its whole source directory is mirrored into the public `lovstudio/skills`
repository under `skills/<name>/`. Pass this gate before the Skill's content is
first pushed to any public repository: a public source repository, a private
source that is about to be made public (its whole history goes with it), or a
`lovstudio/skills` branch that carries the mirror.

1. List what will be published: `git ls-files` in the source, minus the
   directories the mirror excludes (`RSYNC_EXCLUDES` in the catalog's
   `scripts/sync-skills.py`).
2. Remove personal names, links and account identifiers. This is the first pass
   only; a clean search for them does not finish the gate.
3. Read these in full, one at a time: every real case in `cases/cases.json`
   (its id and any image it links to included), each README and Skill Card
   paragraph that cites a case, every example in `SKILL.md` and `references/`,
   and the test fixtures.
4. Keep structure and counts: how many items there were, which fields, what
   kind of gap was found. Remove the storyline: the subject, the parties, the
   order of events, and the amounts and dates that tie the text to one
   particular meeting, negotiation or project. A synthetic fixture that follows
   a real storyline is rewritten on an unrelated subject with the same numbers,
   units, placeholders and sentence shapes, and the tests are run again.
5. Decide file by file: could someone who took part in the real event recognise
   it from this file alone? If the answer is yes or uncertain, the file does
   not pass.
6. Commit the result, and build the mirror from that commit and nothing earlier.

A commit pushed to a pull request on a public repository cannot be taken back.
It stays reachable from the pull request after a squash merge, a force-push or
deleting the branch, and only GitHub Support can remove it. When content that
fails this gate has already been pushed:

- fix it in the source, refresh the mirror, and push the fix to the same branch;
- merge that pull request with **squash**, so the earlier commit never enters
  `main`;
- tell the user which commit is still visible and where (commit SHA, pull
  request, remote branch), and that asking GitHub Support to remove it is their
  decision. Do not report the content as removed.

## Paid delivery contract

Paid Skills are not encrypted. Paying only controls who can download a Skill:

- Keep the paid source repository private and tag the release as `v{version}`.
  The website download prefers that tag and falls back to the default branch.
- Set `skill_path` in the catalog when SKILL.md is not at the repository root.
- Commit everything the Skill needs at runtime. The installed copy is the
  repository content at that ref; there is no build or packing step.
- Never mirror a paid Skill into `lovstudio/skills/skills/`, and do not add
  `encrypted_bundle` or `public_source` (the catalog validator rejects them).
- `POST https://lovstudio.ai/api/skills/download` returns a short-lived archive
  URL only to accounts that own the Skill (Credits redemption or a license bound
  to the account); `npx lovstudio skills add <name>` installs it as plain files.

## License entitlement contract

- `global` and `all` mean a dynamic license scope: while the license is active,
  they include every Skill that is currently listed in the canonical catalog.
- A new Skill becomes available to existing global licenses during catalog sync;
  no per-license grant row, Credits balance, or repurchase is required.
- A delisted Skill leaves the dynamic global scope. Explicit historical
  per-Skill purchases remain fixed unless their own license is revoked.
- Never implement `global` by materializing the current catalog into a fixed
  list of Skill IDs. Catalog sync must maintain the listed/delisted state that
  the entitlement resolver reads.
- Publication verification for a new paid Skill must cover three paths: a
  dynamic global license installs without Credits, an explicit owner installs
  without duplicate Credits, and an unentitled account reaches the purchase
  confirmation before source download.

## Catalog registration

Use the unified `lovstudio/skills` catalog; the former split General and Dev
catalogs are archived. Choose the entry category from product policy, not source
location. Transform the current Pricing Card's public fields into the catalog
manifest; do not independently invent or revise a price in this adapter. Add the
repository, version, category, description, and paid status, then run the
catalog's official mirror/render/validation scripts. Merge the catalog change
into its `main` branch before live revalidation.

Write `tagline_zh` and `tagline_en` to the length the catalog already uses.
Measure before drafting, from the catalog checkout; an entry name passed as an
argument prints that entry's own lengths:

```bash
python3 - SIBLING_NAME <<'EOF'
import statistics, sys, yaml

skills = yaml.safe_load(open("skills.yaml"))["skills"]
for key in ("tagline_zh", "tagline_en"):
    lengths = sorted(len(s[key]) for s in skills if s.get(key))
    print(key, "median", statistics.median(lengths), "max", lengths[-1])
for s in skills:
    if s["name"] in sys.argv[1:]:
        print(s["name"], len(s.get("tagline_zh", "")), len(s.get("tagline_en", "")))
EOF
```

- Neither tagline may be longer than the current maximum for its language.
- Aim for the length of the nearest sibling entries (same series or category).
- Reference on 2026-11-10: `tagline_zh` median 39 and maximum 80 characters,
  `tagline_en` median 89 and maximum 204; one sibling entry measured 51 and 146.

For a paid Skill, add only metadata: `repo`, `version`, `skill_path` when needed,
and the pricing block. Paid entries never get a `skills/<name>/` mirror.

For generated aggregate catalogs, update metadata and run their official sync
and render scripts. Do not hand-edit generated mirror directories.

### Free Skills: carry the mirror when CI cannot clone a private source

On a healthy catalog the `skills.yaml` entry is enough: after the merge the
`Render index` workflow clones the source and commits `skills/<name>/`. Check
before relying on it:

```bash
gh run list --repo lovstudio/skills --workflow render-readme.yml --limit 5
gh run view RUN_ID --repo lovstudio/skills
```

CI cannot mirror a private source when the recent runs on `main` fail at
`Fail on stale mirrors` and their annotations read `clone failed` with
`Authentication failed`, `Invalid username or token` or `Repository not found`;
public sources still clone in that state. The annotation
`SKILLS_SOURCE_TOKEN is empty` means no source was mirrored at all. A new entry
that reaches `main` without a mirror then fails the run with
`installable catalog entry has no mirrored SKILL.md`. Replacing the token is the
repository owner's action: report it, and until it is done put the mirror in the
pull request yourself. This repeats what CI does, with files taken from a pushed
source commit; it is not hand-editing the mirror.

Work on a branch cut from the catalog's current `origin/main`, and export the
pushed source commit you are releasing (`REF`: the tag, or the commit SHA).
`git archive` exports the committed tree only, so untracked and ignored files in
the working directory cannot reach the public mirror:

```bash
tmp=$(mktemp -d)
git -C SOURCE archive --format=tar REF | tar -x -C "$tmp"
```

- **New entry.** Add the entry to `skills.yaml`, then run the mirror script.
  With `SKIP_CLONE=1` it clones only entries that have no `skills/<name>/` yet,
  over SSH with your own key, and leaves the existing mirrors alone:

  ```bash
  SKIP_CLONE=1 SKILLS_CLONE_PROTOCOL=ssh python3 scripts/sync-skills.py
  ```

- **Existing mirror.** `SKIP_CLONE=1` skips it, so copy the export with the
  script's own exclude list (`RSYNC_EXCLUDES`; read it from the script instead
  of trusting this copy), then run the script once more so it applies the
  catalog's display names:

  ```bash
  rsync -a --delete \
    --exclude .git --exclude .github --exclude node_modules --exclude .venv \
    --exclude venv --exclude __pycache__ --exclude .pytest_cache --exclude dist \
    --exclude build --exclude .next --exclude .DS_Store \
    "$tmp/" skills/NAME/
  SKIP_CLONE=1 SKILLS_CLONE_PROTOCOL=ssh python3 scripts/sync-skills.py
  ```

For a new entry, run the rest of the workflow's chain as well:

```bash
python3 scripts/sync-runtime-names.py --write
python3 scripts/render-marketplace.py
python3 scripts/render-readme.py
```

Then check both cases the same way:

```bash
git status --short                      # only the intended paths changed
diff -r -x .github "$tmp" skills/NAME   # no output: the mirror equals the source commit
```

The comparison is empty only when the source already uses the forms the script
writes from the catalog entry's `name_zh` and `display_name`. It sets the first
H1 of `SKILL.md`, `README.md` and `README.zh-CN.md` to `{name_zh} · {display_name}`,
of `README.en.md` to `{display_name}`, and of `skill-card.md` to
`{name_zh} · {display_name} · Skill Card`; it rewrites `display_name` and
`display_name_en` in `skill.yaml` as double-quoted strings; and it adds the
missing non-interactive and scope flags to `npx skills add <owner>/<repo>`
commands, so write those with `-g -y`. Put these forms in the source instead of
accepting a mirror that differs from it.

The `Render index` run on the merge stays red at `Fail on stale mirrors` for as
long as other private sources cannot be cloned. Read its steps instead of its
colour: the remaining `render` steps and the `mirror-cn` job must have passed.

### Free Skills: distribution state in two steps

When the source records its own distribution state (the `distribution` block of
`skill-card.yaml` and the matching row of `skill-card.md`), it states only what
has been observed, so it is written twice:

1. Before the catalog pull request, write `pending` with the date and what is
   still unverified. Commit and push; do not tag yet.
2. Merge the catalog change, revalidate, and pass "Verify the visible result".
3. Write `live` with the dated evidence (page status, visible version, install
   result). Commit and push, then create the `v{version}` tag and the Release on
   this commit, so the tag, `main` and the mirror hold the same files.
4. The mirror is now one source commit behind. CI refreshes it on its next run
   when it can clone the source; when it cannot, open a second pull request
   that refreshes only `skills/<name>/`, as in the section above.
5. A merge that changes only `skills/**` does not start `Render index`: the
   workflow's path filter does not include that directory. GitHub, the
   installer and lovstudio.ai read the refreshed mirror from `main`, but the
   copy lovstudio.cn reads from OSS stays behind until the next run: the
   nightly schedule (in 2026-11 it started 7 to 8 hours after its 03:17 UTC
   cron time), the next merge that touches `skills.yaml`, or a manual dispatch
   if the user asks for one. The OSS copy is current when this header names a
   `main` commit at or after the one that holds the refreshed mirror:

   ```bash
   curl -sI https://lovstudio-downloads.oss-cn-hangzhou.aliyuncs.com/catalogs/skills/NAME/SKILL.md \
     | grep -i x-oss-meta-source-commit
   ```

   Until then report the lovstudio.cn documents as pending, not as synced.

## Revalidate

Since lovstudio/lovstudio-home#148 (2026-11-10), lovstudio.ai reads
`skills.yaml`, and the free Skill documents mirrored into the catalog, at the
commit `main` points to, so this call can follow the merge right away. The
response names the commit the site read.

The catalog's `Refresh website` workflow (lovstudio/skills#66) also sends a
catalog-only refresh after every push to `main` that touches `skills.yaml` or
`skills/`, and fails when the site read another commit. It does not purge the
per-Skill tags below, and while the catalog repository lacks the
`LOVSTUDIO_REVALIDATE_SECRET` secret it only warns. Send this request anyway.

1. Send the request. Replace `NAME` and the site URL with configured values:

   ```bash
   test -n "$LOVSTUDIO_REVALIDATE_SECRET"

   curl -fsS -X POST "SITE_URL/api/revalidate" \
     -H "x-revalidate-secret: $LOVSTUDIO_REVALIDATE_SECRET" \
     -H "content-type: application/json" \
     -o /tmp/lov-revalidate.json \
     -d '{
       "tags":[
         "skills-index",
         "skills-index:lovstudio",
         "skills-updates",
         "skill:NAME",
         "skill-cases:NAME"
       ],
       "paths":["/skills","/skills/NAME","/agent"]
     }'
   ```

2. Compare the commit the site read with the one `main` points to now, before
   verifying anything else:

   ```bash
   gh api repos/lovstudio/skills/commits/main -H 'Accept: application/vnd.github.sha'
   python3 -c "import json; print(json.load(open('/tmp/lov-revalidate.json')).get('catalog_commits'))"
   ```

   - Same commit: the site read the catalog that holds the change. Go on to
     "Verify the visible result".
   - A different commit: `main` moved after the site read it. Send the request
     again.
   - No `lovstudio/skills` commit: the site could not ask GitHub where `main`
     points (no `GITHUB_TOKEN` on the site, or the API failed or took longer
     than 5 seconds) and read `main` through `raw.githubusercontent.com`, whose
     CDN keeps the previous file for up to 5 minutes (`cache-control:
     max-age=300`); a read inside that window caches the old catalog again for
     up to 10 minutes. Send the request again; if the commit is still missing,
     wait until 5 minutes have passed since the merge and send it once more.
   - `pricing_sync` reports `catalog_skills` as before. `{"status":"deferred"}`
     instead of counts means the site's catalog sync failed: report it and
     judge by the detail page.

A read of the previous catalog shows up in two places, both fed by the catalog
cache this call refreshes: `/skills/NAME` keeps returning 404 for a new entry
(or shows the previous version for an update), and `npx lovstudio skills add
NAME` answers `目录中没有找到 Skill：NAME`, because the CLI asks the site's
catalog endpoint first. That endpoint needs no secret and lists the entries the
site currently knows (internal ones excepted), so it is also the direct check:

```bash
curl -fsS "SITE_URL/api/skills/catalog" | grep -c '"name":"NAME"'   # 1: the site has read the entry
```

Neither symptom means the publication failed: go back to step 2.

lovstudio.cn is a separate deployment, and this call does not reach it. It reads
the catalog and the free Skill documents from the OSS copy uploaded by the
`mirror-cn` job of `Render index`, on a 10-minute cache. Read it back after that
job has succeeded and the cache has had time to expire; the first request after
expiry can still return the previous page, so request it again before calling it
stale. The catalog endpoint above, asked on lovstudio.cn, shows whether that
deployment has read a new entry. Report lovstudio.cn on its own line.

## Verify the visible result

```bash
curl -fsS -o /tmp/lov-skill-page.html \
  -w '%{http_code}\n' "SITE_URL/skills/NAME"
rg -n 'Version|EXPECTED_VERSION|EXPECTED_MARKER' \
  /tmp/lov-skill-page.html
```

Completion requires the intended catalog to list the Skill, the detail page to
return HTTP 200, the visible version plus marker to match the release, and the
exact catalog install command to pass from a clean isolated directory. For a paid
Skill, verify with an account that already owns it: the install must download the
tagged source and put plain files on disk without a duplicate purchase.

### Install verification must not touch the maintainer's install root

`npx lovstudio skills add <name>` installs **globally** by default and writes a real
copy into `~/.agents/skills/<name>/`. On a maintainer machine that path is often a
symlink into the development checkout, so a default install silently replaces the
symlink (and any dependency it pulls) with a copy of the released version.

Verify with the project-local mode from a throwaway directory instead:

```bash
tmp=$(mktemp -d /tmp/skill-install-XXXX) && cd "$tmp" \
  && npx -y lovstudio skills add NAME --project \
  && grep -m1 'version' "./.agents/skills/lov-NAME/skill.yaml"
```

Then confirm the delivered payload, not just the exit code: the version matches the
release, a release-specific file exists, and the skill's own CLI or script starts.
If the receipt shows `→ ~/.agents/skills/...`, stop and restore the previous state
from a backup before continuing.
