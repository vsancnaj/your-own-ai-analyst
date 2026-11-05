---
name: deliver
description: Writes the brief for a finished analysis, but only after reading review.md. The brief opens with the objective, key takeaways and recommendations, then gives the analysis, with each chart under a heading that states its takeaway as a full sentence, and a Checks section on what was and was not verified. Use after validate has written review.md.
user-invocable: true
allowed-tools: Read Write Glob
disallowed-tools: Edit
argument-hint: "[path to the run folder under outputs/]"
---

Write the brief for the run folder. You explain results that already exist. You compute nothing new.

## Steps

1. Find the run folder. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds a `review.md`.
2. **Read `review.md` first, before anything else.** It decides what happens next:

   | Verdict in review.md | What you do |
   |---|---|
   | **Fix first** | Do not write a brief. Report the findings and stop. |
   | **Think on it** | Write the brief. Every finding in `review.md` goes into Checks, fixed or not. |
   | **Ship it** | Write the brief. |
   | No `review.md` | Do not write a brief. Say that `validate` has not run and stop. |

3. Read `frame.md` (question, decision, audience), `analysis.py`, the result tables in `data/` and the charts in `charts/`.
4. Write `brief.md` in the run folder, with the sections below.
5. Finish with the run folder path. Nothing else.

## Structure of brief.md

1. **Objective:** the question and the decision it informs, from `frame.md`, in two sentences.
2. **Key takeaways:** at most three. Each is one full sentence with a number and what it is compared with. Keep this a separate section: the caller copies it word for word.
3. **Recommendations:** what the audience should do, tied to the decision in `frame.md`. Say what you are less sure of.
4. **Analysis:** each chart from `charts/` sits under a heading that states its takeaway as a full sentence. Embed the chart with a relative path. Add a short result table from `data/` only where it helps; aggregates only, never raw rows.
5. **Checks:** what was verified and what was not. Include the open periods and any unfinished items (trials, orders, the current month). Then list **every finding from `review.md`**, one line each, even if it was fixed, so the reader sees what was found and what was done:
   - **Fixed:** say what changed, but only if you can see it in `analysis.py` or its results. If the finding still affects how far to trust the result (for example a baseline choice), say so.
   - **Not fixed, or cannot tell:** say "not verified as fixed" and why it matters. Never claim a fix you cannot see.

## Rules for every number

- It carries a comparison (prior period, segment or benchmark), or says none is available.
- Changes say whether they are percentage points or relative percent.
- It traces to `analysis.py` and a result table in the run folder. Name the table and the filter next to it.
- Never state a number that is not in a result table.

Write for the audience in `frame.md`. No em dashes.

## What this is NOT

- Not the analysis. Do not compute, re-cut or re-run anything.
- Not the review. Do not argue with `review.md`; report it.
- Not a copy of the script. Say what it found, not how it works.
