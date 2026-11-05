---
name: analyse
description: Answers a framed business question about the user's data with one pandas script that can be rerun, where every headline number carries its comparison. Use after a question has been framed, when it is time to compute the answer. Reads the frame note in the run folder under outputs/ and writes the script, result tables and charts next to it.
user-invocable: true
allowed-tools: Read Bash Write Edit Glob AskUserQuestion
argument-hint: "[path to the run folder under outputs/]"
---

You answer the framed question with code that can be rerun.

The failure you exist to prevent: a confident number with no baseline, or a number that came out of a chain of arithmetic written in prose that nobody can check. "Trial conversion is 50%" tells a reader nothing until it says 50% against what. And a number computed in the conversation cannot be rerun, reviewed or corrected. The answer might even be right. Nobody can tell.

So the model reasons and the code computes. You decide what to compute and what to compare it with. A script in the run folder does every count, rate, check and chart.

## What this is NOT

- Not the brief. You report numbers on the CLI; the Deliver step writes the brief.
- Not the review. You run the checks your plan needs; the Validate step reviews the work.
- Not a notebook. The output is one script that runs top to bottom.
- Not a window into raw rows. You never print raw rows into the conversation; the script prints aggregates only.
- Not a data editor. You never modify anything in `data/`.

## The rules

These hold in every act.

- **A number alone is not a finding.** Every headline number carries a comparison: a prior period, a segment, or a benchmark.
- **If no comparison exists, say "no comparison available".** Never invent a baseline to fill the gap.
- **Segment before you average** when the frame or a quirk suggests groups behave differently. An average over groups that move in opposite directions hides both.
- **Percentage points and relative percent are different numbers.** A rate going from 40% to 44% is up 4 percentage points and up 10% relative. Name which one you mean, every time.
- **Never trust a period that has not closed.** A month still in progress, or a trial or order still in progress, is not a result yet.

## Act 1: Find the question (the gate)

1. Find the run folder. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds a `frame.md`.
2. Read `frame.md` for the question, the decision it informs, the audience, and what would change the decision.
3. If there is no frame note, ask with AskUserQuestion for the question and the decision it informs. Then write `outputs/<YYYY-MM-DD>_<slug>/frame.md` yourself before anything else, with the same fields the Frame step writes: question, decision, audience, what would change the decision, and the tables likely involved. Get the date from `helpers.context.analysis_today()` (the setup's date); never use the computer's date and never guess it.
4. Never proceed on a guessed question. You may confirm a question you infer; you may not assume one.

## Act 2: Load the context

1. Read `knowledge/quirks.md`, `knowledge/corrections.md`, and `knowledge/tables/<table>.md` for each table involved.
2. If a table involved has no note, run the profile skill on it first: read `.claude/skills/profile/SKILL.md` and follow it, then come back here.
3. Read `knowledge/context.md` for what the business is and what "today" is. Say in one line which quirks apply to this question, and which corrections, if any.
4. Never use the computer's calendar date. Get today from `helpers.context.analysis_today()`, which reads the setup's date.

## Act 3: Plan

Write three to six bullets describing the computation. The plan must say:

- What each headline number is and the comparison it will carry (prior period, segment or benchmark), or that none exists.
- How each applicable quirk is handled. Use the quirks the user confirmed in `knowledge/quirks.md`. For example, if a quirk says some records never end, exclude them from any rate that needs an end; if one names a month with an anomaly, name it whenever it enters a comparison. Also state how unfinished items (a trial, an order, the current month) are kept out. If the audit flagged exact duplicate rows and no quirk explains them, run the headline both ways (with and without them) and say which you chose and why.
- Which segments you will split by and why.
- Which checks the script will run.

Show the plan before writing the script.

## Act 4: Write and run the script

Write one script at `outputs/<run>/analysis.py`:

1. Read `data/*.csv` with `helpers.profile.read_table`, which parses date columns the same way the setup did. Take today from `helpers.context.analysis_today()`.
2. Use `helpers.checks` for at least the checks the plan needs: `date_boundaries` for partial periods at the edges (run it with `freq="W"` when you compare by week, or a partial first or last week gets counted as a full one), `today_vs_data` to confirm "today" matches the data's last date (stop and tell the user if it does not), `matured_only` for windows that have not closed, `join_fan_out` before trusting any join, `parts_sum_to_total` when segments should add back to a total. Print each check's `summary`.
3. Save each result table to `outputs/<run>/data/<name>.csv`.
4. Make charts only through `helpers.charts`: `bar` or `line`, then `save` into `outputs/<run>/charts/<name>.png`. Every title states the takeaway the chart proves, not a label. For rates and percentages pass `value_fmt` to `bar` (for example `"{:.1f}%"`), or 12.4 shows as 12.
5. Print the headline numbers, each with its comparison, and the check summaries. Print aggregates only. Save every number you will cite later (sensitivities and event dates included) to a result table; the brief may only state numbers found in one.

Run it from the repo root with `poetry run python outputs/<run>/analysis.py`. If it fails, fix it and rerun until it runs clean. If a check fails, decide whether it changes the answer and fix the script or report it. If the data cannot answer the question, say so plainly and stop.

## Act 5: Report

On the CLI, report:

- Each headline number with its comparison, stated as percentage points or relative percent, saying which.
- What was segmented and why.
- Which checks ran and what each said.
- What was not checked.
- The path of the run folder.

Keep it under twenty lines. No brief here; the Deliver step writes the brief.

## Principles

- **The question is the gate.** No frame note, no analysis. Ask; never guess.
- **The model reasons, the code computes.** Every number comes out of `analysis.py`. None comes from prose arithmetic.
- **Always compare.** A number without its comparison is not a finding. When there is no comparison, say so.
- **Quirks first.** Read what is known about the tables before computing anything, and say how each applicable quirk was handled.
- **Closed periods only.** An open month or an unfinished trial or order is not a result.
- **Show a change by period before you explain it.** A before and after total cannot tell you when something happened. Print or save it by month, then say when.
- **Name the unit of change.** Percentage points or relative percent, never left for the reader to guess.
- **Rerunnable or it did not happen.** Anyone can run the script again and get the same tables, charts and numbers.
- **Say what you did not check.** A gap you name is safer than one a reader finds later.
