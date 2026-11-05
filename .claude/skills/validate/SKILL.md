---
name: validate
description: Reviews an analysis script as a peer reviewer would, with fresh eyes and on the lookout for bias, and writes review.md with a verdict (Ship it, Think on it or Fix first). Use after analysis.py has run and before any brief is written, or when the user hands over a script, notebook or run folder to check.
user-invocable: true
allowed-tools: Read Bash Write Glob
disallowed-tools: Edit
argument-hint: "[path to the run folder under outputs/]"
---

Review the script in the run folder as a peer reviewer would. Remove bias and look at it with fresh eyes.

You review. You never edit `analysis.py`. If it needs changing, the verdict says so and the caller fixes it; reviewing your own fixes defeats the point.

## Steps

1. Find the run folder. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds an `analysis.py`.
2. Read `frame.md` (question, decision, audience), `analysis.py`, the result tables in `data/` and the charts in `charts/`. Read `knowledge/` for the table notes, `quirks.md` and `corrections.md`.
   If a `review.md` from an earlier round already exists, this is a repeat review. Do not trust its findings: review the current script with fresh eyes, as if you had never seen it. Then check each earlier finding against the current script and note whether it is now resolved.
3. Run the mechanics checks, then the reasoning checks below.
4. Write `review.md` in the run folder.
5. Finish with the run folder path and the verdict. Nothing else.

Never print raw rows into the conversation. Aggregates only.

## Mechanics first

- [ ] **Joins that duplicate rows:** after each join, does the row count still make sense? A join on a non-unique key silently multiplies rows.
- [ ] **Grain:** what does one row stand for (a user, an order, a payment)? Does every count use the same grain?
- [ ] **Denominators:** is every rate divided by the right group, and is that group stated? Parts should sum to totals.
- [ ] **Date boundaries:** are periods inclusive or exclusive on purpose? Is the analysis date in `knowledge/context.md` respected (not the computer's date), and are unfinished periods or unmatured trials kept out of the comparison?
- [ ] **Raw rows:** does any printed output, result table or chart expose individual records instead of aggregates?
- [ ] **Filters:** which rows does each filter remove, and is that what the question needs?

## Then reasoning

- [ ] **Is it the right question?** Does the script answer `frame.md`, and can it inform the decision named there?
- [ ] **What is outside the frame?** What could also explain the result (seasonality, a different cohort mix, other changes at the same time) and is it handled or at least named?
- [ ] **Does the "so what" hold up?** Does the conclusion follow from the numbers? Does every number carry a comparison? Are percentage points and relative percent kept apart?
- [ ] **Timing:** when a split or sensitivity shows a surprise, is it shown by period? A claim about when something happened needs a table by month, not two totals.
- [ ] **Bias:** could a choice in the script tilt the result? For example a comparison window that is too short, a baseline picked after seeing the result, or a split that puts different kinds of users on each side.
- [ ] **Method:** does the script follow the method rules in `analyst/SKILL.md`, including the checks in `helpers/checks.py`?

## Verdict

Give one verdict, with **at most three findings**. Report only the findings that matter most.

| Verdict | Meaning | Findings |
|---|---|---|
| **Ship it** | Nothing blocks delivery | None needed |
| **Think on it** | Reconsider; the script may change after the review | Up to three |
| **Fix first** | Correct before anything else | Up to three |

## Write review.md

Save it as `review.md` in the run folder, in this order:

1. **Verdict** on the first line, exactly one of the three names above.
2. **Findings**, up to three. Each has:
   - **What is wrong** in one sentence.
   - **Where**: the line or block in `analysis.py`, or the result table affected.
   - **Why it matters** for the decision in `frame.md`.
   - **Size of change**: small (a filter, a baseline, a label) or large (a different approach).
3. **Resolved since last round** (only on a repeat review): one line per earlier finding, saying resolved or still open.
4. **Not checked**: what you could not verify, in one or two lines.

## What this is NOT

- Not a fix. Do not edit `analysis.py`, result tables or charts.
- Not a rewrite of the analysis or a second opinion on style. Only what could change the answer.
- Not the brief. Do not write `brief.md`.
