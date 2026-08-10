# Alipay SkillPay Distribution Standard

Use this adapter when the user selects 支付宝 SkillPay or requests all configured
channels. SkillPay is a paid-product submission channel: packaging, upload,
parsing, form submission, review, and live listing are separate states.

## Inputs

- A canonical Skill source that passes `scripts/validate_skill.py`.
- Product title and concise user-facing description.
- Explicit CNY price supplied by the user.
- Current version and source locator for release traceability.
- An authenticated SkillPay merchant session.

## Product package

Create the archive outside canonical source. Use one root directory named after
the Skill and include the complete runnable source while excluding `.git`, local
credentials, caches, build outputs, and channel profiles. Test the ZIP before
upload and record its SHA-256 checksum.

## Submission workflow

1. Open `https://skillpay.alipay.com/ais/products` in the configured merchant
   browser session.
2. Start a new product submission and select the Skill ZIP through the page's
   file chooser.
3. Wait until the page explicitly reports that Skill parsing has completed.
4. Review parsed metadata, then fill the public title, description, and exact CNY
   price from the release manifest.
5. Submit the form and wait for the product-success notice.
6. Re-open the product list and record whether the product is reviewing or live.

Do not expose browser credentials, session data, or merchant identifiers in
logs. Do not report `review` before the form submission succeeds, and do not
report `live` until the public product state shows it.

## Completion evidence

- `prepared`: ZIP integrity, file count, and checksum recorded.
- `uploaded`: the page reports parsing completed.
- `review`: the submission success notice is visible and the product appears in
  the merchant list with a review state.
- `live`: the marketplace exposes a purchasable public product entry.
