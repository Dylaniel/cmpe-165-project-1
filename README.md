# Club Expense Tracker

A small Streamlit web app for a club treasurer to track spending. The treasurer records
expenses as members submit them, follows each one through approval to reimbursement, and
sees at a glance how much the club has spent and how much it still owes people.

Built for **CMPE-165 Project 1** at San José State University.

Expenses are stored in a plain CSV file (`expenses.csv`) and read and written with pandas.
There is no database, no login, and no server setup — the whole application is one file,
`app.py`.

- **Organization:** Campus Coders Club
- **Team members:** Dylan Shanaghy

## Major features

**1. Add, edit, and delete expenses.**
Each expense records a date, description, amount, category, who submitted it, and its
status. The add and edit forms both validate their input: the amount must be greater
than zero and the description cannot be empty, and the app reports which rule failed
rather than silently saving a bad row. Deleting takes a second confirmation click,
because a CSV file has no undo.

**2. Filter by category, status, and text search.**
Category and status filters can be combined, and the search box matches text in either
the description or the submitted-by field. Leaving a filter empty means "no filter", not
"match nothing". The filters also drive the edit/delete picker, so they double as a way
to find a particular expense in a long list.

**3. Dashboard.**
Shows total spend, total still unreimbursed, and a bar chart of spend by category. The
dashboard always reflects every expense on file and is deliberately not changed by the
filters below it.

### What "unreimbursed" means

An expense has one of three statuses: **Submitted → Approved → Reimbursed.**

**Unreimbursed = Submitted + Approved.** An expense counts as unreimbursed until the
money has actually gone out the door, so a claim the treasurer has approved but not yet
paid still counts as money the club owes. Only `Reimbursed` is excluded. This definition
was a team decision; the alternatives considered are recorded in
[DEVLOG.md](DEVLOG.md).

## Required packages

| Package | Purpose | Version this project was built and tested against |
|---|---|---|
| `streamlit` | Web interface | 1.64.0 |
| `pandas` | Reading and writing the CSV | 3.0.6 |

Both are listed unpinned in `requirements.txt`. Python **3.10 or newer** is required;
development used Python 3.12.10.

## How to run it

From the project folder.

**1. Create a virtual environment.**

Windows (PowerShell):

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

**2. Install the required packages.**

```bash
pip install -r requirements.txt
```

**3. Start the app.**

```bash
streamlit run app.py
```

Streamlit prints a local URL (by default <http://localhost:8501>) and opens it in your
browser. Press `Ctrl+C` in the terminal to stop the app.

### If activating the virtual environment fails on Windows

PowerShell may refuse step 1 with `UnauthorizedAccess — running scripts is disabled on
this system`. That is a Windows execution-policy default and has nothing to do with this
project. You do not need to change any system settings: skip activation and call the
virtual environment's Streamlit directly instead, which does the same thing in one
command.

```bash
.venv\Scripts\streamlit.exe run app.py
```

Install the requirements the same way if `pip` is not on your path after skipping
activation:

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**First run:** `expenses.csv` does not exist yet, so the app creates it by copying
`sample_expenses.csv`, which holds 20 realistic sample expenses. Everything you add,
edit, or delete afterwards is written to `expenses.csv`; `sample_expenses.csv` is never
modified. To reset the app to the sample data, delete `expenses.csv` and restart.

`expenses.csv` is intentionally excluded from git — it is local working data, not source
code, and committing it would mean every team member's edits collided.

## AI-Assisted Development

### 1. Which AI tools were used

**Claude Code** (Anthropic), running the **Claude Opus 5** model, used as an interactive
coding agent in the terminal. It had direct access to the filesystem, a shell, git, and a
browser it could drive against the running app. No other AI tool was used.

### 2. What the AI helped build

The AI wrote essentially all of the code in this repository: `app.py` in its entirety,
`sample_expenses.csv`, `requirements.txt`, `.gitignore`, this README, and `DEVLOG.md`. It
also ran the build: it created the virtual environment, installed the dependencies,
started the app, drove a browser against it to check each feature actually worked, and
made the three feature commits.

What the AI did **not** do was decide what to build. The feature list, the constraint to
keep the app to a single file with no database, the choice of status model, and the
choice of which directory and repository to build in were all set by the team. On two
occasions the AI stopped and asked rather than guessing — see below.

### 3. A real example where AI code did not work and had to be modified

**The spend-by-category bar chart silently ignored the ordering the AI's code claimed to
apply.**

Writing the dashboard, the AI wanted the chart's bars in the app's own category order
(Food, Supplies, Travel, Equipment, Marketing, Other) rather than alphabetically, and
wrote this:

```python
by_category = expenses.groupby("category")["amount"].sum()
# Keep the fixed category order rather than alphabetical, and drop categories
# with nothing in them.
by_category = by_category.reindex(
    [category for category in CATEGORIES if category in by_category.index]
)
st.bar_chart(by_category)
```

The code ran without any error, and the totals it produced were correct. But when the
running app was checked in a browser, the chart's x-axis read **Equipment, Food,
Marketing, Other, Supplies, Travel** — straight alphabetical order. `st.bar_chart` sorts
the axis itself and ignores the order of the Series it is given, so the `reindex` call
had no effect on the output at all. The comment was wrong in its second half too:
`groupby` already drops categories with no expenses, so that part of the code was never
doing anything either.

This is worth noting for the management analysis because of *how* it was caught. The code
was syntactically fine, raised no exception, and produced correct numbers; only reading
the rendered axis labels off the live app exposed it. A unit test asserting the category
totals would have passed while the chart remained wrong.

The fix was to delete the dead `reindex` and replace the misleading comment with an
accurate one, then make a deliberate decision to accept alphabetical ordering — forcing a
custom bar order in Streamlit requires dropping to a hand-built Altair chart, which was
not worth the added complexity for six categories in a project explicitly scoped to stay
minimal. Full entry in [DEVLOG.md](DEVLOG.md) under *AI Issues*.

### 4. An important decision the humans made

**The team chose the three-status model, and chose it on maintainability grounds rather
than on realism.**

The AI presented three options for how an expense's status should work and explicitly did
not choose between them:

- **A — `Pending` / `Reimbursed`:** simplest, unambiguous unreimbursed total, but no way
  to record that the treasurer approved something without paying it yet.
- **B — `Submitted` / `Approved` / `Reimbursed`:** models the real treasurer workflow and
  gives a genuine approval step, at the cost of having to define "unreimbursed" as two
  statuses combined.
- **C — `Submitted` / `Approved` / `Rejected` / `Reimbursed`:** most realistic, keeps
  rejected claims on the record, but `Rejected` has to be excluded from the unreimbursed
  total or the dashboard reports a number that is simply wrong.

The team chose **Option B**, in their own words:

> "I'm fine with option B as long as it's the easiest option that fits the requirements."

That reasoning drove the outcome directly. Option C is the more realistic model of how a
club actually handles expenses, and a team optimizing for realism would have taken it —
but it carries the one genuinely error-prone calculation in the whole app, since a
`Rejected` expense that leaks into the unreimbursed total makes the dashboard lie about
what the club owes. Choosing B took that failure mode off the table entirely at the cost
of not being able to record rejections. The consequence is carried through the code as a
single constant, `UNREIMBURSED_STATUSES`, and stated on screen next to the number so the
definition is never ambiguous to a user.

Full entry, including the options as they were presented, in [DEVLOG.md](DEVLOG.md) under
*Human Decisions*.

## Development record

[DEVLOG.md](DEVLOG.md) is the running record of the build: time estimates, decisions and
who made them, AI mistakes and their fixes, scope changes, and the risks that actually
materialized (including a missing toolchain and a build pointed at the wrong directory).
It logs only what actually happened.
