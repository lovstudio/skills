# Public Exhibit benchmark

Use public consulting-company output as an editorial benchmark, not as a
trademarked style kit. Do not claim affiliation.

Consulting reports often use answer-first figure titles because the surrounding
page already establishes context. A standalone public infographic has to
introduce itself. For that use case, keep the subject/purpose in the header and
place the evidence-backed recommendation after the visual. Preserve
answer-first titles as `action` mode, not as the universal default.

## Primary observed benchmark

### Bain Technology Report 2025

Official PDF:

`https://www.bain.com/globalassets/noindex/2025/bain_report_technology_report_2025.pdf`

Observed examples:

1. Figure 4 in “Will Agentic AI Disrupt SaaS?”:
   - the title states the business conclusion: mapping workflows into four
     scenarios helps executives set offensive and defensive priorities;
   - both axes have directional endpoints and decision meaning;
   - quadrants are named as business scenarios, not “high/high” placeholders;
   - definition boxes sit adjacent to the relevant axis;
   - marks use position, length, and red/gray category encoding;
   - a note/source line closes the evidence chain.
2. Figure 1 in “From Pilots to Payoff”:
   - the title contains the key number, “as much as 40%”;
   - stacked segments and a dashed overlay show what coding assistants can
     address;
   - all segments are directly labeled;
   - unit, denominator, note, and source are visible;
   - color distinguishes addressable work instead of decorating the page.

Article:

`https://www.bain.com/insights/from-pilots-to-payoff-generative-ai-in-software-development-technology-report-2025/`

## Additional official references

Use these as additional review material when available:

- McKinsey, *The state of AI: How organizations are rewiring to capture value*:
  `https://www.mckinsey.com/~/media/mckinsey/business%20functions/quantumblack/our%20insights/the%20state%20of%20ai/2025/the-state-of-ai-how-organizations-are-rewiring-to-capture-value_final.pdf`
- McKinsey, *Global Private Markets Review 2024*:
  `https://www.mckinsey.com/~/media/mckinsey/industries/private%20equity%20and%20principal%20investors/our%20insights/mckinseys%20private%20markets%20annual%20review/2024/mckinsey-global-private-markets-review-2024.pdf`
- BCG, *Where’s the Value in AI?*:
  `https://web-assets.bcg.com/75/ab/7ec60ba84385ad89321f8739ecaf/bcg-wheres-the-value-in-ai.pdf`

Check for:

- a deliberate title mode: subject/purpose for standalone visuals or
  answer-first for contextual executive Exhibits;
- recommendation placement after evidence in topic-led standalone visuals;
- shared scales and direct labels;
- annotation placed at the decisive evidence;
- meaningful whitespace, not empty containers;
- explicit notes, sources, dates, and units;
- restrained brand color used semantically.

## Open-source comparison

- `VoltAgent/awesome-design-md` is useful for brand tokens and interface style,
  but it does not define Exhibit argument quality or chart integrity.
- `JimLiu/baoyu-skills/baoyu-infographic` provides a broad layout/style menu,
  but its default “layout × aesthetic” approach is not a consulting quality
  system.
- `antvis/Infographic` may provide rendering primitives, but a stock template
  is not a finished Exhibit.

Use these projects for implementation ideas only. The acceptance bar remains:
evidence → conclusion → encoding → annotation → decision.

## Extraction checklist

When reviewing a public Exhibit, record:

1. title mode and exact title;
2. figure number and source note;
3. main visual area ratio;
4. variables encoded by position, length, color, shape, and connection;
5. count and placement of annotations;
6. how units, periods, caveats, and methodology are shown;
7. what was deliberately omitted;
8. what business decision the Exhibit supports.
