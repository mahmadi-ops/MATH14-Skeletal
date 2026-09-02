---
name: skeletonize
description: Turn a section of the MATH 14 notes into a skeletal (fill-in) section, in place. Use when asked to make skeletal notes, fill-in notes, or a student workbook version of a section — e.g. "skeletonize the new section", "re-hollow Green's theorem after the notes changed".
---

# Skeletonize a section, in place

This book's sections **are** the skeletal versions: each file in
`source/` was the completed section and was hollowed out under the same
file name and the same `xml:id`s. So skeletonizing means *editing the
section file itself*, and the completed text is what the file held before
(git history, or the completed-notes repository).

## 1. Read the whole section first

Print it with the figure internals collapsed, so the prose, the examples
and the solutions are visible with their line numbers:

```bash
python3 .claude/skills/skeletonize/view.py source/<file>.ptx | less
```

Then list which of its ids are cited from elsewhere, because those must
survive (restated in an `<assemblage>` if the derivation that produced
them is being hollowed):

```bash
python3 .claude/skills/skeletonize/xrefs.py source/<file>.ptx
```

## 2. What survives, what is hollowed out

| Keep verbatim | Replace with a workspace box |
| --- | --- |
| `<objectives>`, `<introduction>` | Every worked computation |
| Definitions, theorem **statements**, `<assemblage>` summaries | Every `<proof>` |
| Example / exercise / task **statements** | Every `<solution>` and `<answer>` |
| Setup prose that poses the question | The derivation that answers it |
| `<video>`, `<interactive>`, figures that illustrate a statement or check a box | Figures that *are* the answer (a plotted table, a region of integration the student has to find) → empty grid, same id |

Numbered results that a later section or an assignment cites stay in
full: put them in an `<assemblage>` immediately after the box that
derives them, under their original `xml:id`.

Captions that state the answer ("its volume is 3π/2") are trimmed to
"compare with what you found"; the figure itself stays.

## 3. The workspace box

```xml
<sidebyside width="97%">
<image>
<latex-image>
\begin{tikzpicture}
\draw[rounded corners=8pt, draw=gray!55, thick] (0,0) rectangle (15,13);
\draw[gray!35] (0,8.5) -- (15,8.5);
\node[anchor=north west, font=\small\itshape] at (0.35,12.7) {first step:};
\node[anchor=north west, font=\small\itshape] at (0.35,8.2) {result:};
\end{tikzpicture}
</latex-image>
<shortdescription>Blank box in two rows, for … and for … .</shortdescription>
</image>
</sidebyside>
```

- Width is always `15`. Height is the judgement call: 4–6 for one line,
  13–20 for a multi-part computation. Row labels name what goes on each
  line (`$\mathbf v(t) =$`, `the limit:`), never the answer.
- A box with nothing to label is a plain rectangle with a grey
  `workspace` note at the top left.
- `<shortdescription>` is required. Describe the rows, never the answer.
- Empty grids for sketches are tikz `grid` pictures inside `CDATA` (the
  `>=stealth` option contains a `>`); see `section-parametrization.ptx`.

## 4. The instruction line

Immediately before the box, in the paragraph that held the solution:

```xml
<p>
<em>Solution.</em>
(Apply <xref ref="eq-mass-speed"/> with the density written in terms of
<m>t</m>; the double-angle identity makes the integral elementary. Say
why the solution for <m>b</m> is the only one.)
</p>
```

Calibration — the part that is easy to get wrong:

- **One to three sentences, parenthesised.** Name the tool and the form
  of the answer. Do not walk through the steps.
- Point at the numbered result to use by `<xref>`; do not restate it.
- Flag the one thing that trips students up, and nothing else.
- Ask for the conclusion explicitly when there is one ("state the range
  of <m>t</m>", "say what the sign means").
- Never give away a value the student is meant to produce.
- End with "compare with <xref ref="fig-…"/>" when a video or figure is
  the check.

`source/section-parametrization.ptx` is the reference for this level of
detail; it mirrors the MATH 13 book's `sec-skel-geom-parametrization.ptx`.

## 5. Structure to watch

- In many files the `<solution>` sits *after* `</example>` rather than
  inside it. The replacement goes inside the `<statement>`: replace from
  the line **`</statement>`** through the solution's `</solution>` with
  instruction + box + `</statement>` + `</example>`. Getting the start
  line one off (leaving a stray `</statement>` or eating a `</p>`) is the
  usual cause of a "mismatched tag" failure.
- A figure that lived inside a solution but is a check, not an answer,
  stays inside the `<statement>` after the box (or moves to section level
  after `</example>`).
- Concept Check `<exercise>`s keep their `<hint>`; `<answer>` and
  `<solution>` go. The eight cylindrical-coordinates tasks keep a
  `<solution>` holding only the GeoGebra solid, by design.

## 6. Mechanics: line-range patching

Edit by line ranges of the *original* file, applied bottom-up in one
pass, so the numbers you read off `view.py` stay valid:

```bash
# spec.py defines EDITS = [(start, end, replacement_text), ...]
python3 .claude/skills/skeletonize/patch.py source/<file>.ptx spec.py
python3 .claude/skills/skeletonize/xrefs.py --check
```

`patch.py` refuses to write a file that is not well-formed (it leaves a
`.failed` copy for inspection), so a bad range costs nothing. Then build:

```bash
scripts/build-site.sh          # web + PDF, with the truncated-PDF guard
```

and read the log for `PTX:ERROR`, `PTX:WARNING` and LaTeX `!` lines.

## 7. Traps that each cost a build

- A comment may not contain `--`.
- A bare `<` or `>` inside a `latex-image` not wrapped in `CDATA` must be
  `&lt;` / `&gt;`.
- `\$` inside a `latex-image` is a literal dollar; the math after it
  compiles in text mode and fails.
- Never touch the fourth chapter (`hw*-online.ptx`, `review*-practice.ptx`
  and what they include): it is the auto-graded problem chapter, not
  lecture notes.
