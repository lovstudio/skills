# Skill Group Composition

## Nearby Skills Inspected

| Skill or capability | Actual routing contract | Classification |
|---|---|---|
| `lov-image-creator` | Produces a local PNG or other image artifact from a prompt or rendered page. | Upstream atom |
| `lov-media-creator` | Produces local covers, frames, and other media artifacts as part of a larger media workflow. | Optional upstream atom |
| `lov-dev-blog` | Drafts and publishes a blog post; its own Supabase asset uploader owns blog-specific storage paths and publication acceptance. | Optional downstream atom |
| `baoyu-post-to-wechat` | Publishes to WeChat and uploads images into WeChat's platform-specific media flow. | Not composed |
| `lov-media-fetch` | Finds and downloads long-form video to local storage. It does not produce or consume the public image URL contract. | Not composed |
| PicGo GUI / PicGo-Core | Owns image-host configuration, credentials, plugins, upload transport, and returned URL. | Required runtime, not a sibling Skill |

The local source root and installed Skill catalog contained no other generic Skill
whose accepted input is a local image path and whose final result is a PicGo-backed
public URL or a rewritten Markdown document.

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance boundary |
|---|---|---|---|---|
| Upstream | Image generation or editing Skill | Prompt or source media | Verified local image file | Upstream owner confirms the local file is the intended image. |
| Core | `lov-upload-image` | Existing local image path or Markdown file | HTTP(S) image URL, JSON mapping, or rewritten Markdown | This Skill confirms PicGo success, one-to-one mapping, safe rewrite, and optional URL HTTP response. |
| Downstream | Blog, documentation, social, or messaging Skill | Public URL or rewritten Markdown | Destination-specific draft or publication | Downstream owner validates rendering and destination publication state. |

There is no handoff when the requested destination needs a platform media ID rather
than a general public URL. That platform's publishing Skill must perform its own
upload and acceptance checks.

## Overlap Decisions

- `lov-dev-blog` may upload images, but its outcome is a blog-specific storage object
  and published post. Its uploader is not reused here, and this Skill does not take
  ownership of blog publication.
- `baoyu-post-to-wechat` also transfers images, but WeChat rewrites content around its
  own media APIs. A PicGo URL is not substituted for that destination contract.
- PicGo itself is reused as the upload engine instead of duplicating uploader plugins,
  credentials, image-host APIs, or naming transformations.

## Composition Decision

This is a **Single Skill with one deterministic Python CLI**. Direct image upload and
Markdown rewriting share the same PicGo configuration, validation, URL mapping, and
acceptance criterion: local images become verified public URLs. The Markdown mode is
not independently useful without that core upload, so splitting it into a Skill Kit
would add ceremony without a distinct module contract. External Skills remain optional
artifact-level upstream or downstream handoffs.
