# Cover source: Codex base_instructions

## Article metadata

- Title: Codex 的 base_instructions（默认 prompt）到底写了什么
- Slug: codex-base-instructions-default-prompt
- Excerpt: 我拆开 codex-cli 0.149.1 中 17,730 字符的 base_instructions，看看 Codex 如何定义人格、协作、授权、工程操作与 Skill，并说明这份默认 prompt 没写什么。
- Tags: dev, codex, prompt-engineering, agent
- Author: Mark

## Core message

Codex 的默认 prompt 不是代码生成秘籍，而是一份 Agent Operating Manual。
它主要定义人机协作、授权边界、真实工作区操作、破坏性动作和 Skill
加载协议；模型能力、runtime developer instructions、工具、项目上下文与
服务端约束仍位于这份 base instructions 之外。

## Verified evidence

- Local CLI snapshot: codex-cli 0.149.1 on 2026-08-26.
- Model: gpt-5.6-sol.
- Base instructions: 17,730 characters and 168 lines.
- Bundled and refreshed catalog SHA-256:
  35d8b5d513fff3b55344d5f9f3169305cc276aee053f5be140a77708e0926e7c.
- The model's base_instructions equals model_messages.instructions_template.
- The largest sections are Working with the user, Rules for getting work done,
  and Using skills.

## Cover metaphor

One small central stack of nested instruction sheets forming a compact operating
manual, with a simple agent cursor or thread passing through five quiet layers.
No readable text, logos, dense interface, glow, gradient, or complex scene.
