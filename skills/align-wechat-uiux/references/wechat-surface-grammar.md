# WeChat Surface Grammar

This is a comparison lens, not a frozen pixel specification. Verify current
behavior on the matching WeChat platform/version whenever exact values matter.

## Chat timeline

Distinguish these component families before styling:

| Family | Typical ownership | Important parity questions |
|---|---|---|
| User message | sender side of conversation | avatar, sender name, direction, bubble/media surface, grouping |
| System event | conversation timeline | centered/inline placement, weak hierarchy, no false sender ownership |
| Time separator | timeline chronology | gap rule, localized time, no message actions |
| Rich card | embedded app/article/content | title/source/media hierarchy, safe open behavior, footer identity |
| Media | image/video/sticker/voice/file | intrinsic size, preview/original, loading/failure, bubble presence |
| Quote/forward | message containing another object | outer type ownership, nested preview, source attribution |
| Unknown | future or unsupported object | legible fallback, copyable diagnostics, no raw payload leak |

For every family, inspect selection, context menu, copy, export, search location,
loading, failure, long text, emoji baseline, and adjacent-message grouping.

## Conversation list

Check:

- stable identity and correct conversation kind;
- avatar, title, latest-message summary, sender prefix, draft, mute, pin, unread;
- timestamp formatting and ordering;
- folded/hidden/system placeholders;
- live refresh without losing selection or scroll position;
- search and filters using the same canonical summary.

A correct timestamp or badge is not enough if the underlying conversation flags
or latest-message type are wrong.

## Contacts and profiles

Check:

- friend, stranger, group, official account, enterprise, and system identities;
- alias, remark, nickname, real name, account ID, avatar, signature, region;
- addition/source time versus latest chat activity;
- privacy and masking behavior;
- profile entry, navigation, and unavailable fields.

Do not use chat recency as a substitute for contact-add time or display a raw ID
as a polished name when a verified display field exists.

## Moments and feed-like surfaces

Check:

- author identity, post type, text/media/link sharing, location, visibility;
- interaction counts and notifications;
- time formatting and chronological grouping;
- media aspect ratio, grid, preview/original behavior;
- article source and safe link handling;
- missing/deleted/private content states.

## Controls and menus

- Status is text or a badge unless it opens real detail.
- Primary action is singular and labeled when meaning is not obvious.
- Peer toolbar actions share hit target and icon grammar.
- Secondary or extensible actions move into a three-dot menu when crowded.
- Toggle state remains visible without relying on a toast.
- Destructive actions require correct hierarchy and confirmation when data can be lost.
- Tooltip does not rescue an ambiguous core action; use a label when needed.

## System and error states

- Separate user-facing explanation from technical detail.
- Provide copy for error/debug information when the user may report it.
- Include stable case/message/source identifiers where useful.
- Preserve retry and recovery state without exposing internal intent or protocol noise.
- Empty, loading, partial, stale, offline, unsupported, and permission states each
  need distinct semantics.

## Inputs

For search, chat, comments, captions, and command inputs:

- Enter during IME composition accepts the candidate and does not submit.
- Keyboard focus and selection remain visible.
- Send/search behavior is consistent across click, Enter, and shortcut paths.
- Disabled/loading state explains why the action is unavailable when necessary.

## Visual comparison dimensions

Record exact observations rather than “looks like WeChat”:

- container width and background;
- x/y alignment and ownership;
- spacing before/after adjacent events;
- font size, weight, line height, color, opacity;
- radius, border, shadow, surface, tail;
- avatar and media dimensions;
- wrapping and truncation;
- icon source, size, baseline, and text gap;
- motion duration and reduced-motion behavior;
- state and interaction at the tested viewport.
