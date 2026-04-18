# lovstudio:fill-web-form

Fill web forms by deep-searching your local knowledge base. Give it a URL, get back a ready-to-paste markdown document.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:fill-web-form
```

No external dependencies — uses Claude's built-in tools only.

## How It Works

```
 ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
 │  Web Form    │     │  Knowledge Base   │     │  Output Doc      │
 │  (URL)       │     │  (local files)    │     │  (markdown)      │
 │              │     │                   │     │                  │
 │  ┌────────┐  │     │  profile/         │     │  ## 1. 姓名      │
 │  │ 姓名   │──┼──┬──│  posts/           │──┬──│  手工川          │
 │  │ 简介   │  │  │  │  projects/        │  │  │  ## 2. 简介      │
 │  │ 案例   │  │  │  │  articles/        │  │  │  <合成内容>      │
 │  │ 成效   │  │  │  │  CLAUDE.md        │  │  │  ## 3. 案例      │
 │  └────────┘  │  │  │  memory/          │  │  │  <合成内容>      │
 └──────────────┘  │  └──────────────────┘  │  └──────────────────┘
                   │                        │
              WebFetch                Agent(Explore)
              提取字段                 深度检索匹配
```

## Usage

```
/fill-web-form https://example.com/apply?formId=123
```

Claude will:
1. Fetch the form and extract all fields
2. Deep-search your knowledge base for matching info
3. Generate a markdown document with all fields pre-filled
4. Flag fields that need manual input (uploads, private data)

## Supported Form Types

| Type | Examples |
|------|----------|
| Conference applications | GIAC, QCon, ArchSummit speaker submissions |
| Event registrations | Hackathon signups, meetup RSVPs |
| Profile forms | Platform bios, author profiles |
| Grant/funding applications | Accelerator apps, grant proposals |

## License

MIT
