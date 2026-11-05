---
name: analyst
description: "Answer a business question about the user's data end to end: frame, profile, analyse, validate, deliver."
user-invocable: true
argument-hint: "<the business question>"
---

Answer this question about the user's data end to end: $ARGUMENTS

If the question above is empty, ask for the question and stop. Never invent one.

## The method

Every step below follows these rules.

1. **Frame the decision before touching data.** If the question does not say what decision it informs and who decides, ask; never reconstruct it.
2. **Never answer a table question from the schema alone.** Profile first; a table without a note in `knowledge/` gets one before it is used.
3. **A naked number is not a finding.** Every number carries a comparison (prior period, segment or benchmark) or says none is available; percentage points and relative percent are named.
4. **Cite the table, the filter and the code.** Every number in a brief traces to `analysis.py` and a result table in the run folder.
5. **Parts sum to totals and joins do not fan out.** The checks in `helpers/checks.py` run in code, not in prose.
6. **Say what was not checked.** Open periods, unfinished items (trials, orders, the current month) and untested assumptions are part of the answer.
7. **Read the knowledge folder before writing code, and write back what you learn.** Read `knowledge/` (table notes, `quirks.md`, `corrections.md`) first; when the user corrects you, append the correction to `corrections.md` as one dated line and continue.

## The steps

0. If `knowledge/context.md` does not exist, the data has not been set up. Tell the user to run `/setup` first and stop.
1. Run the `frame` skill with the question above: read `.claude/skills/frame/SKILL.md` and follow it. Note the run folder it created.
2. For each table named under "Tables likely involved" in the frame note that has no `knowledge/tables/<table>.md`, run the `profile` skill on it (`.claude/skills/profile/SKILL.md`).
3. Run the `analyse` skill on the run folder (`.claude/skills/analyse/SKILL.md`).
4. Run the `validate` skill on the run folder (`.claude/skills/validate/SKILL.md`) **in a fresh subagent** (Agent tool). Give it only the run folder path and tell it to follow that skill file. A reviewer that saw the author's reasoning is not a fresh pair of eyes, and a subagent also keeps the skill's tool limits (`disallowed-tools`) that do not apply when a skill is only read inline. If its verdict is **Fix first**, you (the caller, not the validator) fix `analysis.py` according to the findings, rerun it, and run `validate` again. At most two rounds. If it is still **Fix first**, stop and report the findings; do not write a brief. If its verdict is **Think on it**, apply any finding that is a small change to `analysis.py` (a filter, a baseline, a label) and rerun the script once, and carry every remaining finding into the brief's Checks section as not verified; do not run `validate` again.
5. Run the `deliver` skill on the run folder (`.claude/skills/deliver/SKILL.md`), also in a fresh subagent, with the same instruction.
6. Finish with the path of the run folder, the verdict from `review.md`, and the Key Takeaways from `brief.md` copied verbatim. Nothing else on the CLI.
