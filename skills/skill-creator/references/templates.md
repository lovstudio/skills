# Local Skill Templates

`scripts/init_skill.py` is the source of truth. It creates portable local source
without remote repositories or platform distribution metadata.

## Source frontmatter

```yaml
---
name: lov-<name>
description: >
  Use 50-200 characters to explain the outcome, supported inputs, and concrete
  Chinese and English trigger phrases.
license: MIT
metadata:
  author: skill-publisher
  version: "0.1.0"
  tags:
    - <tag>
  compatibility: "Portable Agent Skills format. List runtime requirements."
  dependencies: []
---
```

Required body sections include `## Triggers`, Chinese and English activation
phrases, explicit non-triggers, ordered workflow, dependencies, and validation.

## Automatic source shape

Every generated Skill includes the Profile contract:

```bash
python3 scripts/init_skill.py <name> --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

Self-contained Skill Kit:

```bash
python3 scripts/init_skill.py <name> \
  --kit \
  --module <module-a> \
  --module <module-b> \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

The generated source always includes `skill.yaml`,
`references/user-profile.md`, and `scripts/profile_store.py`. The old
`--user-config` flag remains accepted as a compatibility alias and does not
change the generated contract.

## Completion

- Replace every placeholder.
- Keep every required module and reference inside the source directory.
- Run `python3 scripts/validate_skill.py .`.
- Verify the local install symlink resolves to the source.
- Exercise trigger routing and at least one Kit pipeline when applicable.

Remote publication is a separate `lov-skill-publisher` workflow.

## Mandatory Skill group composition record

Every new source includes `references/skill-composition.md`. Before replacing
its placeholders, inspect related local and installed Skills and record:

1. nearby Skills considered and their actual routing contract;
2. each upstream/core/downstream atom with the artifact-level handoff;
3. overlaps that should be reused or extended rather than duplicated; and
4. the final Single Skill versus self-contained Kit decision.

External sibling Skills are optional handoffs, not hidden runtime dependencies.
If two or more stages require a hard dependency for the same user-visible
result, embed them in the new Skill Kit and keep the source self-contained.
