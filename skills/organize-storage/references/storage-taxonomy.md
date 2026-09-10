# Project-First Storage Taxonomy

Use this taxonomy when a volume mixes projects, personal archives, finished
media, app libraries, installers, and system directories.

## Target top level

| 目录 | 放入什么 | 不放入什么 |
|---|---|---|
| `01_项目/` | 有明确交付、事件、客户、课程、拍摄或制作边界的项目 | 通用下载、日期快照、app 库 |
| `02_个人归档/` | 照片视频总库、按日期切片的下载归档、长期个人资料 | 正在进行的项目、成片交付 |
| `03_媒体库/` | 成片、影片、散片、素材库 | 剪辑工程数据库、相机整卡归档 |
| `04_应用数据/` | app 管理的库、数据库、工程缓存 | 人工整理的普通项目文件 |
| `99_管理/` | 安装包、待处理、隔离区、旧链接、迁移记录 | 业务项目正文 |

Hidden system directories remain at the volume root and are never part of the
taxonomy. The exact category names may be localized; the responsibility split is
what matters.

## Project-first decision order

1. Can the content be named as one project or event with a delivery or source set?
   Put the whole project in `01_项目/`.
2. Is it personal material with no project delivery? Put it in `02_个人归档/`.
3. Is it a finished film, clip, or published output? Put it in `03_媒体库/`.
4. Is it owned and written by an app library? Put it in `04_应用数据/`.
5. Is it an installer, pending intervention, broken link, or migration record?
   Put it in `99_管理/`.
6. Is it a system directory or trash? Leave it where it is.

## Project boundaries

- Group by event or delivery, not by camera model or file type. Three camera
  cards from one event belong to one project with card-level subdirectories.
- Preserve an existing internal convention. A camera ingest project keeps its
  `原始素材/`、`处理素材/`、`转存校验/` structure.
- Keep date-sliced downloads as separate snapshots. Do not merge them just
  because filenames overlap; a later snapshot may be the only complete copy.
- Keep app-managed libraries at their expected path unless the consuming app has
  been repointed or the library is confirmed to be a cold backup.
- Keep a project folder if its content is empty but the folder name is the only
  evidence of a lost or pending delivery. Move it to `99_管理/待处理/` instead of
  deleting it.

## Naming rules

- Use numeric prefixes: `01_`, `02_`, `03_`, `04_`, `99_`.
- Use the language and naming convention already present on the volume.
- Include a date only when it is present in the existing folder name or another
  reliable source. Never invent a date to make sorting look better.
- Name camera subdirectories by camera and card when that is known.
- Rename a moved container only when the new name removes real ambiguity; do not
  rename its internal files merely for style.
- Keep paths free of characters that are invalid or lossy on the target
  filesystem. ExFAT is case-insensitive and lacks POSIX ownership.

## Minimum move map

Build the smallest map that achieves the project boundary. Move whole containers
first. Do not reshuffle their interiors unless the boundary itself is wrong.

```json
{
  "moves": [
    {"src": "old-camera-card-a", "dst": "01_projects/event-x/fx3-card-a"},
    {"src": "old-camera-card-b", "dst": "01_projects/event-x/fx30-card-b"},
    {"src": "loose-installers", "dst": "99_admin/installers"}
  ]
}
```

## What not to do

- Do not create a category tree solely from file extensions.
- Do not move `.Trashes`, `.Spotlight-V100`, `.fseventsd`, `$RECYCLE.BIN`, or
  `System Volume Information`.
- Do not merge snapshots, quarantine a zero-byte export, or delete duplicates in
  the same operation as a structural move.
- Do not move a source that is open by an editor, a source with files modified
  within the last 48 hours, or an app library at its expected path.
- Do not update historical logs and manifests to make old paths look current.
  Record the old → new mapping instead.
