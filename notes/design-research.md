# Snowfall report: design research and revision

Reviewed November 23, 2026. This is a design rationale, not evidence that a
particular visual style can reliably identify AI authorship. Human designers
use these patterns too.

## Sources

1. [Anthropic's public frontend-design guidance](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md).
   Practitioner guidance, **not a controlled user study**. It identifies recurring
   generated-page defaults: cream/terracotta palettes, oversized display type,
   unnecessary uppercase labels, numbered section markers, repeated card kits,
   and generic decorative copy. Its important point is to ground design in the
   actual subject rather than replace one template with another.
2. [Morkes & Nielsen, *Concise, Scannable, and Objective*](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/)
   (1997). Usability research supporting short, factual, scannable writing rather
   than promotional language. This predates generative AI; it supports the
   writing changes, not an “AI detector” claim.
3. [Kate Moran, *How to Present Scientific Findings Online*](https://www.nngroup.com/articles/scientific-findings-online/)
   (2017). Findings from expert interviews and usability tests: clear headings,
   short summaries, useful charts, layered detail, and restrained visual design.
4. [Kate Moran, *The Aesthetic-Usability Effect*](https://www.nngroup.com/articles/aesthetic-usability-effect/).
   Attractive visuals affect perceived ease of use, but can also conceal real
   usability problems. Functional testing is still necessary.

The search integration returned no results for several broader AI-design queries;
the sources above were read directly. No invented survey or claimed detection
accuracy is used.

## What changed

- Removed the invented “Field Notes” branding, numbered uppercase section labels,
  large serif treatment, slogan headings, and three dashboard-like metric blocks.
- Kept the actual family context without inventing anecdotes, quotations, or photos.
- Used a pale winter-blue background, dark readable text, and a restrained blue
  accent. System fonts avoid a remote font dependency and rendering shifts.
- Made the answer a short paragraph, with the uncertainty caveat immediately
  visible, rather than a promotional hero banner.
- Added an annual-data slider and a graph of the existing uncertainty intervals.
  These serve the report rather than decorate it. The underlying analysis is unchanged.
- Reworked charts to their actual container width so labels remain legible on
  phones, rather than scaling an 800px chart down to unreadable type.
- Added a desktop contents list, keyboard focus styles, a skip link, plain-language
  headings, and print styles. Detailed methods and downloadable evidence remain.

The goal is a specific, usable personal research page, not a claim that it was
made without AI assistance.
