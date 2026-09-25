# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Contract and boundary |
|---|---|---|
| `lark-doc` | upstream atom | Creates, updates and fetches Docx/Wiki document content. It does not own knowledge-space resolution plus public-permission acceptance. |
| `lark-wiki` | upstream atom | Resolves spaces and creates, reads or moves Wiki nodes. It does not edit document bodies or set link visibility. |
| `lark-drive` | downstream atom | Reads and patches public permission settings for the underlying document. It does not publish Markdown into a Wiki. |
| `feishu-doc` | not composed | Primarily fetches Feishu content into Markdown; it does not own verified Markdown-to-Wiki publication. |
| `feishu-perm` | overlap, not selected | Manages collaborators through a separate MCP surface. Public link visibility and fresh readback are already covered by the current `lark-drive` contract. |
| `lov-publish-wechat-article` | pattern reference | Its state separation and remote-readback discipline are reused conceptually, but WeChat cover, Lovpen, gateway and publish APIs do not hand off artifacts to this Skill. |

## Atomic Handoffs

1. Local Markdown is preflighted by this Skill and passed to `lark-doc` as prepared Markdown. This Skill owns source fidelity acceptance.
2. The requested space name or parent node is passed to `lark-wiki`; it returns `space_id`, `node_token`, `obj_token` and hierarchy evidence. This Skill owns target-location acceptance.
3. The verified `docx obj_token` and explicit visibility tier are passed to `lark-drive`; it returns current and updated permission settings. This Skill owns the final permission acceptance.

No sibling Skill owns the combined `source -> Wiki document -> verified content and visibility` result.

## Overlap Decisions

This source does not duplicate the low-level Feishu API implementations. It defines cross-atom routing, conflict handling, state semantics and final acceptance. `feishu-perm` is not required because collaborator membership is outside the requested outcome and public-link settings use `lark-drive`.

## Composition Decision

Use a Single Skill. The user-visible outcome is one atomic publication result, while Docs, Wiki and Drive operations share one context and one acceptance receipt. A Skill Kit would add module boundaries without creating independently useful packaged stages.
