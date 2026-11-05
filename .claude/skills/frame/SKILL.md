---
name: frame
description: Turns a business question into a short note with the question, the decision behind it and the audience, and creates the run folder under outputs/. Use first, before any data work. If no decision is named, it asks and stops.
user-invocable: true
allowed-tools: Read Bash Write Glob AskUserQuestion
disallowed-tools: Edit
argument-hint: "<the business question>"
---

Frame this question: $ARGUMENTS

If the question above is empty, ask for it and stop. Never invent one.

Get the business question, the decision behind it and the audience into one note that every later step reads.

## Steps

1. Check the parts below against what the user wrote.
2. **Gate:** if no decision is named, ask the user and stop. Do not continue without one. Never reconstruct a decision yourself. Ask the same way if what would change the decision is missing.
3. **Pin down vague words.** Find any word in the question that could reasonably mean more than one thing (for example retention, churn, cost, active, at-risk). For each one, ask the user with AskUserQuestion, offering 2 or 3 meanings with the one you recommend first. Never pick a meaning yourself. If every word is already clear, ask nothing.
4. Create the run folder `outputs/<date>_<slug>/`. The date is today's date from `knowledge/context.md` (the line `today:`, which is the data's end date, not the real calendar date). If `knowledge/context.md` does not exist, tell the user to run `/setup` first and stop. The slug is 2 to 4 words in kebab-case describing the question.
5. Read what exists: list the files in `data/` and read the notes in `knowledge/`. Use file names and notes only. Never print raw rows.
6. Write `frame.md` in the run folder with the sections below.
7. Finish with the run folder path and the one-sentence question. Nothing else.

## What frame.md contains

- **Question:** one sentence.
- **Decision:** the choice someone will make with the answer, and who makes it.
- **Audience:** who reads the brief.
- **What would change the decision:** the result that would push the decision one way and the result that would push it the other, agreed before looking at any data. For example: "if monthly churn rises by more than 3 points, roll back; if it barely moves, keep." Never reconstruct it yourself.
- **Terms:** one sentence for each word that had more than one meaning, saying which meaning is used. Leave this out if no word needed pinning down.
- **Tables likely involved:** the tables from `data/` that the question needs, one line each saying why. Mark any table that has no note in `knowledge/`, because `profile` will have to write one.

## Checks before you stop

- [ ] Question is stated in one sentence
- [ ] A decision is named
- [ ] Audience is named
- [ ] What would change the decision is named
- [ ] No word with more than one meaning is left unresolved
- [ ] Run folder exists and `frame.md` is inside it
- [ ] Every table listed exists in `data/`

## What this is NOT

- Not the analysis. Do not compute anything.
- Not the profile. Do not describe columns or quality; only say which tables are needed.
