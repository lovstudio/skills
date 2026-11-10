# User Profile contract

Every Skill created by Skill Creator declares `user-profile/v1` in `skill.yaml`.
The contract connects independent sessions to one user-owned JSON Profile while
keeping the Skill source portable across users and brands.

## Shared shape

The host supplies the Profile through `SKILL_PROFILE_PATH` (or the runtime's
configured profile path). The stable shared scopes are:

- `user`: user identity, language, timezone, and other personal working defaults.
- `brand`: public brand facts, site, logo, tone, profile, and design guidance.
- `workspace`: project roots and output locations.
- `preferences`: shared preference values when the host stores them in the Profile.
- `skills.<skill_id>.profile`: Skill-specific defaults.
- `skills.<skill_id>.records`: durable decisions and preferences learned from
  direct user statements for this Skill.

The Profile may also use the runtime's canonical `identity` fields. Manifest
field aliases bridge `identity.*` and the portable `user.*` / `brand.*` names.

## Read on every run

1. Read the current request and project context.
2. Read the shared Profile and the `skills.<skill_id>` namespace.
3. Resolve values in this order: current request, project context, Skill records,
   shared preferences, shared user/brand Profile, safe defaults.
4. Keep `profile_scope` and field provenance available for the final result.

Do not copy resolved personal paths, brand values, or private records into the
committed Skill source.

## Persist directly stated values

When the user explicitly gives a value meant to survive later sessions, save it
immediately after the user statement and report the canonical path:

```bash
python3 scripts/profile_store.py record \
  --skill-id lov-example \
  --path records.subtitle_level \
  --value '"cet4"' \
  --confirm
```

For shared facts, use `--path brand.<field>` or `--path user.<field>`. The
script writes JSON atomically, preserves unrelated Profile data, increments a
numeric Profile revision when present, and never echoes the stored value.

Inferred information, credentials, tokens, cookies, and secret-like fields stay
out of durable records. If the user has not stated that a value should persist,
keep it in the current request context.

## Read the connected context

```bash
python3 scripts/profile_store.py read \
  --skill-id lov-example \
  --pretty
```

The result contains `user`, `brand`, `workspace`, `preferences`, `skill`, and
`records` scopes. A host using `skill-runtime/v1` also returns the same binding
as `profile_scope` and `profile_contract`.

## Compatibility

`--user-config` remains accepted by the Creator as a compatibility flag for old
invocations. The Profile contract is now always generated; users do not choose
an initialization mode.

## lov-tencent-meeting-cowork records

All values live under `skills.lov-tencent-meeting-cowork.records` and are written
only after the user states them directly.

| Path | Type | Example statement | Use |
| --- | --- | --- | --- |
| `records.self_names` | list of strings | “我在腾讯会议里显示的是小川” | each passed to `--self-name`, so to-dos can be marked as mine |
| `records.followup_style` | string | “会后跟进短一点，分条发，对合作方用您” | voice rules for follow-up drafts |
| `records.followup_channel` | string | “跟进一般发微信” / “发邮件” | layout of the draft: chat messages or an email |
| `records.counterpart_notes` | object: person or organisation → note | “王经理是对接人，拍板的是他们负责人” | recipient choice, tone, and who to keep informed |

`self_names` and `counterpart_notes` are whole values. Read the current value,
merge the new entry, and write the whole value back:

```bash
python3 scripts/profile_store.py record --skill-id lov-tencent-meeting-cowork \
  --path records.counterpart_notes \
  --value '{"某合作方": "王经理是对接人，拍板的是他们负责人"}' --confirm
```

When no `self_names` record exists, the Skill offers `user.public_name` and
`user.name` from the shared Profile as candidates and otherwise falls back to
the note owner shown by the page.

Never store meeting content, share links, drafts, attendee lists, or inferred
judgments about people in the Profile.
