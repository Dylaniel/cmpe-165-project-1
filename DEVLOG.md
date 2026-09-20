# DEVLOG — Club Expense Tracker

Development record for CMPE-165 Project 1. Entries are added as things happen, not
reconstructed afterwards. Timestamps come from the `date` command on the build machine
(PDT). Anything not actually observed is marked as such rather than filled in.

---

## Estimates

**[2026-09-19 22:17 PDT] Team estimate: 2 hours.**
Recorded in the team's own words:

> This number came from an AI suggestion that I reviewed, and altered from 1 hour to 2,
> as our estimate upon evaluation. This is in the context of a build being considered
> roughly finished give or take, and the time being time spent by agents working plus
> testing.

**[2026-09-19 22:18 PDT] AI estimate (Claude Opus 5): ~40 minutes.**
Clearly labeled as the AI's own estimate, not the team's. Scope of this estimate: agent
wall-clock time from the first DEVLOG entry through the final `git push`, covering the
three features, README/DEVLOG, and the fresh-venv sanity check. It excludes human review
time and excludes the preflight/environment troubleshooting that happened before this
timestamp.

**Actual elapsed time:** recorded at the bottom of this file after the final push.

---

## Human Decisions

### Expense status model — decided by the team

The AI offered three options with tradeoffs and did not choose:

| Option | Statuses | For | Against |
|---|---|---|---|
| A | `Pending` / `Reimbursed` | Simplest possible; "unreimbursed" is unambiguous; least code and least chance of bugs. | No way to record that the treasurer approved something but hasn't paid yet; no way to record a rejection. Thin for a management write-up. |
| B | `Submitted` / `Approved` / `Reimbursed` | Models the real treasurer workflow (member submits → treasurer approves → money goes out). Gives a genuine approval step to discuss in the analysis. | "Unreimbursed" now means `Submitted` + `Approved` combined, a definition that must be stated explicitly. Still nowhere to put a rejected claim. |
| C | `Submitted` / `Approved` / `Rejected` / `Reimbursed` | Most realistic; rejected claims stay on the record instead of being deleted. | `Rejected` must be excluded from the unreimbursed total or the dashboard lies — the easiest thing in this app to get wrong. Most statuses to pick from for a 20-row demo. |

**Team chose Option B.** Reasoning, quoted verbatim:

> I'm fine with option B as long as it's the easiest option that fits the requirements.

Consequence carried into the build: **Unreimbursed = Submitted + Approved.** This
definition is stated in the README and implemented in the dashboard.

### Repository location — decided by the team

**[2026-09-19 22:15 PDT]** The AI found that the directory it had been pointed at
(`CMPE 165\Project 1`) was empty and not a git repository, while a GitHub Desktop clone
of `cmpe-165-project-1` existed in the sibling directory `CMPE 165\cmpe-165-project-1`.
The AI stopped and presented the options rather than initializing a repo or inventing a
remote URL. The team chose to build inside the existing clone. See *Risks That Occurred*.

### Decisions the team explicitly delegated to the AI

The team instructed the AI to make reasonable simple choices in these areas itself and
log them. **These are AI decisions, not team decisions** — recorded here only to keep the
"who decided what" record in one place.

| Choice | What the AI picked | Why |
|---|---|---|
| Category list | Fixed list: Food, Supplies, Travel, Equipment, Marketing, Other | A free-text category field produces typo variants ("food" vs "Food") that split the dashboard's bar chart into meaningless duplicates. A fixed list makes grouping reliable. |
| Row identity | Integer `id` column, unique per expense | Identifying rows by position breaks as soon as a filter is applied — the user would edit or delete whichever row happened to be at that index in the *filtered* view, not the one they clicked. An `id` survives filtering and sorting. |
| Delete safety | Two-step confirm before a delete is written | Deletes are irreversible and there is no undo in a CSV-backed app. |
| Money handling | Amounts rounded to 2 decimals on write | Keeps the CSV readable and avoids float display noise like `86.42000000000001`. |

---

## AI Issues

Issues where AI-written code did not work and had to be fixed. Logged as they happen.

### [2026-09-19 22:27 PDT] Bar chart ignored the category ordering the code claimed to apply

**What the AI wrote.** In the feature 3 dashboard, to control the order of the bars in
the spend-by-category chart:

```python
by_category = expenses.groupby("category")["amount"].sum()
# Keep the fixed category order rather than alphabetical, and drop categories
# with nothing in them.
by_category = by_category.reindex(
    [category for category in CATEGORIES if category in by_category.index]
)
st.bar_chart(by_category)
```

The intent was to plot the bars in the app's own category order —
Food, Supplies, Travel, Equipment, Marketing, Other.

**What went wrong.** The rendered chart's x-axis read **Equipment, Food, Marketing,
Other, Supplies, Travel** — plain alphabetical order, not the order the code set up.
`st.bar_chart` sorts the axis itself and ignores the order of the Series index it is
handed, so the `reindex` call changed nothing on screen. The second half of the comment
was also wrong: `groupby` already omits categories that have no expenses, so the
filtering in the list comprehension was never doing anything either.

This was caught by reading the axis labels off the running app, not by reasoning about
the code — the code looked correct and ran without error. A test that only asserted the
totals would have passed while the chart stayed wrong.

**How it was fixed.** The `reindex` was removed as dead code and the misleading comment
replaced with one that states what actually happens:

```python
# Categories with no expenses are left out by groupby. st.bar_chart sorts the
# axis alphabetically itself, so no ordering is imposed here.
by_category = expenses.groupby("category")["amount"].sum()
st.bar_chart(by_category)
```

Forcing a custom bar order in Streamlit means dropping down to an Altair chart with an
explicit axis sort. That was judged not worth the extra dependency surface and code for
this project: alphabetical is a perfectly readable order for six categories, and the
project brief says to keep the app minimal. **Accepting the default was a deliberate
choice, not an oversight** — recorded here so the ordering is not mistaken for a bug
later.

---

## Scope Changes

**[2026-09-19 22:16 PDT] GitHub CLI (`gh`) dropped from the plan.**
The original plan called for creating the repo with `gh repo create ... --push`. Preflight
found `gh` was not installed. The team directed the AI not to install it, because the repo
had already been created through GitHub Desktop. Publishing changed to a plain
`git push` to the existing `origin`. Net effect: one fewer tool to install, and the repo
is private as already configured on GitHub rather than public as originally suggested.

**[2026-09-19 22:15 PDT] Working directory moved.**
Build moved from `CMPE 165\Project 1` to `CMPE 165\cmpe-165-project-1` (the existing
clone). See *Human Decisions* and *Risks That Occurred*.

**[2026-09-19 22:18 PDT] Team member and organization names deferred.**
The team chose not to supply these during the build. `[TEAM MEMBERS]` and
`[ORGANIZATION]` placeholders are used in the README and in the app header, and both are
listed as remaining TODOs.

---

## Risks That Occurred

**[2026-09-19 21:40 PDT] Toolchain missing at project start — cost one full round trip.**
Preflight found no `git`-adjacent tooling beyond git itself: no `gh`, and no `python`,
`py`, or `python3` on PATH or in any standard install location. The build could not start.
Resolution: the team installed Python and directed that `gh` be skipped entirely. See
*Scope Changes*.

**[2026-09-19 22:17 PDT] False alarm: Python reported missing when it was actually installed.**
After the team installed Python, both `py --version` and `python --version` still failed in
the AI's shell. Taken at face value this looked like a failed install, and the AI's first
instinct was to report it as still missing and stop a second time. Checking further showed
Python 3.12.10 *was* correctly installed:

- `winget list` reported `Python.Python.3.12  3.12.10` and `Python.Launcher`
- `...\AppData\Local\Programs\Python\Python312\python.exe` existed on disk
- the **user PATH in the registry** already contained the Python directories

The cause was a stale environment: the agent's shell process had been started *before* the
install, so it held an out-of-date copy of PATH. The install was never the problem.
Resolution: invoke `python.exe` by absolute path once to create `.venv`, then use
`.venv\Scripts\python.exe` for everything afterwards, so PATH never matters again and no
application restart is needed. **Lesson recorded below** — "command not found" is evidence
about the shell, not proof about the machine.

**[2026-09-19 22:32 PDT] Windows path-length limit broke `pip install` during the sanity check.**
The final sanity check installs the requirements into a throwaway virtual environment
inside a fresh clone, to prove the README instructions work for someone starting from
nothing. The first attempt put that clone in the agent's deeply-nested scratchpad
directory and `pip install` failed:

```
ERROR: Could not install packages due to an OSError: [WinError 206]
The filename or extension is too long:
'...\scratchpad\freshcheck\clone\.venv\Lib\site-packages\streamlit\.agents\skills\
developing-with-streamlit\assets\templates\apps\dashboard-companies'
```

Streamlit ships asset files nested many directories deep, and added to an already-long
parent path this crossed the Windows 260-character `MAX_PATH` limit. **This was a fault
of the test location, not of the project** — the same install had already succeeded in
the project directory itself, whose path is short. Resolution: re-ran the check from a
short temp path, where it passed. Worth knowing for the team: cloning this repo into a
deeply nested folder can make `pip install streamlit` fail on Windows for reasons that
have nothing to do with the code.

**[2026-09-19 22:15 PDT] Target directory was not the repository.**
The directory the build was pointed at was empty with no `.git` in it or any parent, so
`git remote -v`, `git status`, and `git log` all failed with *"fatal: not a git
repository."* The actual clone was in a sibling directory whose name matched the repo. Had
the AI guessed — run `git init` and invent a remote URL — the result would have been a
second, disconnected working copy of the same project and a confusing push. Resolution: the
AI stopped, reported the mismatch, and the team chose the target. Verified before any
writes: `origin` = `https://github.com/Dylaniel/cmpe-165-project-1.git`, branch `main`,
clean tree, one commit (`Initial commit`), containing only `.gitattributes`.

---

## Lessons

- **"Command not found" describes the shell, not the machine.** A long-running agent
  process holds the PATH it was launched with. After any install, verify against the
  registry/filesystem/package manager before concluding software is missing — this build
  came within one message of telling the team to reinstall Python that was already there.
- **Absolute paths beat environment repair.** Creating the venv with a full path to
  `python.exe`, then using `.venv\Scripts\python.exe` from then on, removed the PATH
  problem permanently instead of working around it each time.
- **Verify the repo before writing to it.** Two directories with plausible names sat side
  by side and only one was the clone. `git remote -v` took one second and prevented a
  wrong-directory build.
- **Code that runs without error is not code that works.** The bar-chart ordering bug
  raised no exception and produced correct totals; it was only visible by reading the
  rendered axis in a browser. For UI work, "it ran" and "it did the right thing" are
  different claims, and only the second one matters.
- **Verify in a fresh clone, not in the directory you built in.** The build directory
  already had a working `.venv` and an `expenses.csv`, so it could not prove the README
  instructions work for a teammate starting from nothing. Cloning to a temp directory
  tested the real path — including the first-run copy of `sample_expenses.csv`, which
  never executes in a directory that already has data.
- **Distinguish a broken project from a broken test environment.** The `WinError 206`
  failure looked like a dependency problem and was actually an artifact of where the test
  was run. Re-running it somewhere else was the difference between a real bug report and
  a wasted fix.

---

## Time actually taken

- **First DEVLOG timestamp:** 2026-09-19 22:17 PDT (team estimate recorded)
- **Final commit:** 2026-09-19 22:36 PDT
- **Elapsed: about 19 minutes.**

Measured from the first DEVLOG entry to the last commit; the push to GitHub followed
within roughly a minute of that. This window covers the three features, the README and
this log, browser verification of every feature, and the fresh-clone sanity check.

It does **not** include the environment troubleshooting that came before the first
timestamp — installing Python, discovering `gh` was missing, and locating the correct
repository directory — which took longer than the build itself.

**Against the estimates:** the team estimated 2 hours and the AI estimated ~40 minutes.
The actual build came in under both. The honest reading is not that the app was easier
than anyone thought, but that **the estimates and the measurement are not measuring the
same thing.** The team's 2 hours was framed as "agents working plus testing" for a build
considered roughly finished, which reasonably includes the human review time and the
setup friction that this 19-minute figure explicitly excludes. Treat the 19 minutes as
agent execution time only, not as the cost of producing the project.
