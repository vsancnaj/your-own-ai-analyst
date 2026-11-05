---
name: setup
description: Connects a user's own data to the analyst. Asks what the data is, audits the files in data/, confirms what it cannot know, checks protections, and writes the knowledge folder. Use first in a new copy of this repo, or when the data changes. Run it before any business question.
user-invocable: true
allowed-tools: Read Bash Write Edit Glob AskUserQuestion
argument-hint: "[nothing needed]"
---

You set up the analyst for one person's data. Many users know little about their data, so you ask simple multiple choice questions, you measure what you can, and you say plainly what you are guessing.

The failure you exist to prevent: an analysis built on a wrong "today", a table read as the wrong thing, or a file that never opened. Each question below says what it protects. Tell the user that in one short line when you ask.

## Rules for every question

- Use AskUserQuestion. Offer 2 to 3 real answers with the one you recommend first, and "I don't know" as the last option. Never block on "I don't know": use the audit's guess and mark it inferred.
- Explain in plain words, as to a beginner. One line on why the question matters and what gets worse without it.
- Never print raw rows. Counts, names and date ranges only.
- Never modify anything in `data/`.
- A **measured** fact comes from the audit code. A **guess** is yours. Say which is which every time.
- Only the user can confirm a quirk. Never write one into `knowledge/quirks.md` on your own.

## Phase 0: Where are we

1. If `knowledge/context.md` exists, a setup was done. Show its `today` and source line and ask: re-run the whole setup, add or refresh tables only, or stop.
2. Otherwise continue.

## Phase 1: Context (before looking at any file)

Ask these, up to four questions per call:

1. **Where does the data come from?** A public dataset (for example Kaggle) / my company or work / a database or BI export / I don't know. Why: it tells me how much to trust it. Public data is often already cleaned, company exports often are not.
2. **What is the data about?** Sales or orders / customers or subscriptions / marketing or web traffic / other (user types it) / I don't know. Why: it tells me what a "row" and a "month" probably mean.
3. **What decision will answers feed?** Grow revenue / reduce losses or cost / understand customers / just exploring / I don't know. Why: `frame` stops without a decision, so I need your usual kind.
4. **Who reads the results?** Only me / my manager or team / executives or stakeholders / I don't know. Why: it sets how plainly the brief is written.

## Phase 2: Hand-over

1. Tell the user to copy (not move) their files into `data/`, and to keep the originals somewhere else too. Why: the analyst never edits `data/`, but a copy is your safety net.
2. Only `.csv` files are read. If the user has Excel or other files, say they are ignored and ask them to export CSV.
3. Ask: files are in `data/` / I need help with this / not yet. On "need help", explain where the folder is and wait. On "not yet", stop here and say how to restart.

## Phase 3: Audit

1. Run `poetry run python helpers/audit.py data` from the repo root and read the JSON.
2. Report in plain words, in this order:
   - **Found:** each table, its rows and columns. List other files that were ignored.
   - **Dates:** each date column's range.
   - **Flags:** each one with its `affects:` line, ordered by how much it could damage the analysis. Say the top three first.
   - **Likely links between tables:** the shared column names. Say it is a name match, not proof.
   - **Guess for today:** the latest date found, and whether the last month looks partial.
3. If a file is unreadable or a table is empty, say so first and ask whether to continue without it.
4. If no date column was found, say plainly that charts over time and period comparisons will not work until the user says which column holds dates.

## Phase 4: Confirm what only a human knows

Ask, up to four questions per call. For each, say what gets worse on "I don't know".

1. **Today.** Use the guess / a different date (user types it) / I don't know (use the guess, marked inferred). Why: unfinished months and orders would count as results.
2. **What one row stands for in each table**, using the audit's grain guess. Confirm all / fix some (user says which) / I don't know. Why: every count and rate depends on it. If many tables, ask for the most important four and mark the rest inferred.
3. **What empty means** for the worst flagged column: not applicable / not happened yet / missing data / I don't know. Why: a filter or rate on that column is wrong if empty is misread.
4. **Does someone know this data well?** Yes, I can state things that are true about it / someone else does (name who, for the notes) / nobody. Why: only a person who knows the data can confirm a quirk. If yes, ask them to type them, then write only their words into `quirks.md`. If not, leave `quirks.md` empty and say that analysis will flag its assumptions instead.

If the audit flagged an ambiguous or mixed date order, ask this first, before anything that uses dates: **Are dates written day first (31/12/2024) or month first (12/31/2024)?** Day first / month first / I don't know (read as month first, mark inferred and say that months may be off). Why: the wrong order puts days in the wrong months and nothing looks broken. Save the answer as `date_order: day-first` or `date_order: month-first` in `knowledge/context.md`, then rerun the audit so the dates and the "today" guess are reread.

## Phase 5: Protections

1. Read `.claude/settings.json` in the repo. Confirm the deny rules for `data/` are there. If missing, say so.
2. Check whether the sandbox is on: look for `"sandbox"` with `"enabled": true` in `.claude/settings.json`, `.claude/settings.local.json` and `~/.claude/settings.json`. You cannot see the live state, so say "set to on" or "not set", and tell the user to type `/sandbox` to check.
3. Explain like to a five year old: without the sandbox the helper can go into every room and the rule "do not touch the toys" is only advice; with it the helper plays in a playpen whose walls hold even when a script runs.
4. Ask: turn it on (type `/sandbox`) / explain again / skip, I accept the risk / I don't know. Record the answer, never hide a skip.

## Phase 6: Write the knowledge folder

Create `knowledge/` files from the answers, only these:

- `knowledge/context.md`: a line `today: YYYY-MM-DD` (exact format, other code reads it), then `today_status: confirmed | inferred`, `date_order: day-first | month-first` only if the user answered that question (other code reads it), source, what the data is about, the decision type, the audience, the sandbox answer, and the setup date from `date +%F`.
- `knowledge/quirks.md`: a header and a note "only a person who knows the data confirms a quirk", then only what the user typed in Phase 4. Otherwise just the header.
- `knowledge/corrections.md`: a header and "dated one-line corrections from the user".
- `knowledge/tables/<table>.md` for each table: generate the base with `profile_to_markdown(profile_csv(path))` from `helpers.profile`. Add `## Observed` with the audit flags, each marked "measured, not confirmed". Fill `## Meaning` with one line per column, each marked "(inferred)" unless the user stated it.

## Phase 7: Summary

Show, in under twenty lines:
- What was set up and where (paths).
- A short table: measured / confirmed by you / guessed.
- Sandbox: on / not set / skipped.
- What is still unknown and what it may affect.
- Two or three example questions the data seems able to answer, labelled as suggestions, and the next command: `/analyst <your question>`.

## What this is NOT

- Not an analysis. Do not answer a business question here.
- Not cleaning. Do not change, filter or rewrite any file in `data/`.
- Not a source of confirmed quirks. Only the user supplies those.
