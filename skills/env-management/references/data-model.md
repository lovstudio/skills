# Data model and lifecycle

## Stable hierarchy

Every credential uses three kebab-case IDs:

```text
platform/account/key
```

- **Platform** is the provider or service boundary, such as `openai`, `github`, or `vercel`.
- **Account** distinguishes personal, work, client, team, region, or billing identities on that platform.
- **Key** identifies one issuance or rotation. Use a stable label such as `primary`, `ci`, or `rotation-2026-08`; never reuse an ID for a different secret.

The registry stores metadata only. A key record includes its expected environment variable, administrative status, optional effective dates, secret backend type, created and updated timestamps, and the latest redacted validation evidence.

## Bindings are the activation layer

A stored Key is not automatically exported. A binding maps exactly one target and environment variable to one locator:

```text
shell + OPENAI_API_KEY -> openai/work/rotation-2026-08
system + OPENAI_API_KEY -> openai/personal/primary
```

The two targets are independent. Rebinding a variable is atomic and retains the unselected Key records for later rotation or audit.

## Administrative status

| Status | Meaning | Eligible by default |
| --- | --- | --- |
| `active` | Intended for current use | Yes |
| `standby` | Stored and potentially valid, but not preferred | Yes, after an explicit bind |
| `disabled` | Temporarily excluded | No |
| `revoked` | Permanently invalidated at the provider | No |

Do not delete revoked metadata during ordinary cleanup. Historical issuance, validation, and binding evidence is useful for incident review.

## Effective health precedence

Health is computed in this order:

1. `revoked` or `disabled` administrative state;
2. `not_before` later than the current time;
3. `expires_at` at or before the current time;
4. latest validation result `invalid`;
5. within the configured expiry warning window;
6. active or standby.

`unknown` means there is no current remote evidence. It does not mean invalid, but audit reports an active binding with stale or missing evidence as a warning.

## Remote validation evidence

The generic probe records only:

- validation result: `valid`, `invalid`, `unknown`, or `error`;
- UTC check time;
- HTTPS origin, never query parameters or response bodies;
- HTTP status code when available;
- a short non-secret note.

A `401` or `403` is treated as invalid credentials. Other non-success responses are recorded as errors because rate limits, upstream outages, and permission scope failures do not prove the Key itself is invalid.
