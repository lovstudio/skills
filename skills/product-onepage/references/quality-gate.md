# Product OnePage release gate

## Machine proxy

Score 100 points:

| Dimension | Points | Critical minimum |
|---|---:|---:|
| Brand and orientation | 20 | 16 |
| Story and product stage | 20 | 14 |
| Proof integrity | 20 | 12 |
| Conversion | 15 | 12 |
| Visual composition | 15 | 10 |
| Delivery and ownership | 10 | — |

Release threshold: 85, no critical errors, and no critical dimension below its
minimum. The score is a conservative machine proxy, not a taste or truth score.

## Machine checks

- semantic regions and supported layout/style/aspect;
- exactly one headline and primary CTA;
- category, product stage, two to four features, proof, source, Logo;
- proof-to-source linkage and real CTA destination;
- generated-image text-free declarations and image alt text;
- placeholder copy, vague CTA labels, generic card area, overflow, empty blocks;
- canvas and PNG dimensions;
- region area ratios and reading order.

## Human review

Inspect the exact PNG at original size and thumbnail size:

1. five-second category, promise, product, and action recall;
2. headline-spine coherence;
3. product-stage truth and legibility;
4. proof adjacency and source clarity;
5. critical copy accuracy;
6. silhouette hierarchy and signature motif;
7. Logo-swap contradiction;
8. CTA destination/QR match;
9. absence of pseudo-text, fake UI, and synthetic proof;
10. commissioned rather than template-generated finish.

Record specific observations. `passed` without an image and a concrete review
note does not satisfy the strict gate.

## Definition of done

- Editable source and high-resolution PNG both exist.
- A viewer can identify product relevance and action in five seconds.
- Public copy contains only supported product truth.
- Product artifact or conceptual status is explicit.
- Critical text remains code-rendered.
- The CTA reaches the stated next state.
- Source, prompt, brand, and asset lineage are preserved.
- Machine and human gates pass for every delivered aspect.
