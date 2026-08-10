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
  author: lovstudio
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

No persistent settings:

```bash
python3 scripts/init_skill.py <name> --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

Persistent workspace, brand, locale, output, or provider settings:

```bash
python3 scripts/init_skill.py <name> \
  --user-config \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

Self-contained Skill Kit:

```bash
python3 scripts/init_skill.py <name> \
  --kit \
  --module <module-a> \
  --module <module-b> \
  --user-config \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

The agent infers these flags from requirements. They are implementation inputs,
not questions for the user.

## Completion

- Replace every placeholder.
- Keep every required module and reference inside the source directory.
- Run `python3 scripts/validate_skill.py .`.
- Verify the local install symlink resolves to the source.
- Exercise trigger routing and at least one Kit pipeline when applicable.

Remote publication is a separate `lov-skill-publisher` workflow.
