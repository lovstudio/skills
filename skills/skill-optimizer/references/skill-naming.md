# Skill naming review

Review names for accuracy, brevity, elegance and consistency. Start with the
user's approved names and style references; read the real input, action, output
and exclusions before changing them. A memorable product name can be accurate
without spelling out every input format or implementation detail.

## Display names

- Favor short, easy-to-say, memorable names with a recognizable product role.
  A reader should grasp the area of use; the description supplies exact scope.
- Functional, result, role and metaphor names are all valid. “大师”, “专家”,
  “神器”, “小能手”, “人人” and similar terms are not automatically disallowed.
  Evaluate them in context; do not make every Skill a “大师” either.
- Preserve user-approved names. Do not replace personality with a dry feature
  summary merely to satisfy a generic object–action naming heuristic.
- Remove creator/studio brand prefixes such as “手工川｜” or “Lovstudio｜”.
  Keep platform names such as GitHub and 微信 when they identify the task's
  actual target. Branding metadata and runtime IDs are separate fields.
- Put input restrictions, secondary features and implementation details in the
  description. A catchy name does not authorize invented capabilities or
  guaranteed results in the name or copy.
- Consistency means compatible tone, brevity and recognition across a catalog,
  not identical syntax, word order or suffixes. Keep neighboring capabilities
  distinguishable without inventing a difference they do not have.
- Chinese and English names should convey the same capability naturally. A
  product metaphor need not be translated word for word.

## Approved style anchors

These examples establish style, not a claim that all tools have the same scope:

| Catalog identity | Approved Chinese name |
| --- | --- |
| wdb-cli | 万能微信秘钥 |
| hanzi-lens | 汉字镜 |
| wxmp-cracker | 公众号神器 |
| bp-deck | BP 大师 |
| any2pdf | PDF大师 |
| any2deck | PPT 大师 |
| write-professional-book | 写书专家 |
| event-poster | 专业海报 |
| professional-infographic | 专业信息图 |
| subtitle-freedom | 人人字幕 |
| oh-my-landingpage | 官网小能手 |

“BP 大师” names the deck capability, not every module in a BP kit. Keep separate
outline and review modules distinguishable. Preserve the approved “PDF大师”
spelling instead of silently adding a space to satisfy a typography preference.

For a focused developer task, the approved “GitHub 仓库简介优化” remains suitable.
The title identifies the core job; topic and homepage updates remain in the
description. Do not rename it “GitHub 大师” just to imitate another product.

## Identity and synchronization

Catalog `name_zh` and `display_name` are display fields; `name`, `runtime_name`,
repository names, paths and Profile keys are compatibility contracts. A display
name cleanup does not authorize renaming those identifiers. New IDs should be
short, meaningful English kebab-case and fit the neighboring naming family.

Record the old name, proposed name, capability evidence and decision for each
reviewed Skill, including names kept unchanged. Record whether a name is
user-approved or an editorial suggestion; preserve that distinction in reports.
Use existing canonical display fields; align corresponding README or Card
titles only where they represent the
same public name. Keep quotations, historical case titles and changelogs intact.
Do not rename third-party products, publish undeclared Skills, merge overlapping
implementations or invent a capability to resolve an ambiguous name.

Verify agreement with approved examples, name–description–body agreement,
memorability, duplicate names and relevant local/catalog surfaces. Using another
task as a naming reference does not replay its publishing or delisting actions.
Publication state requires a separate real channel readback.
