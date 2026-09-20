"""Club Expense Tracker — a single-file Streamlit app for a club treasurer.

Expenses live in expenses.csv, read and written with pandas. On first run the file
is created by copying sample_expenses.csv.
"""

import datetime
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path("expenses.csv")
SAMPLE_FILE = Path("sample_expenses.csv")

COLUMNS = ["id", "date", "description", "amount", "category", "submitted_by", "status"]
CATEGORIES = ["Food", "Supplies", "Travel", "Equipment", "Marketing", "Other"]
STATUSES = ["Submitted", "Approved", "Reimbursed"]

# An expense counts as unreimbursed until the money has actually gone out, so both
# Submitted and Approved are unreimbursed. Decided by the team; see DEVLOG.md.
UNREIMBURSED_STATUSES = ["Submitted", "Approved"]


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------

def load_expenses():
    """Read expenses.csv, creating it from the sample file on first run."""
    if not DATA_FILE.exists():
        shutil.copy(SAMPLE_FILE, DATA_FILE)
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # A blank cell reads back as NaN, which would show up as the text "nan" in the
    # edit form and break the text search, so normalise it to an empty string.
    df["submitted_by"] = df["submitted_by"].fillna("")
    df["description"] = df["description"].fillna("")
    return df


def save_expenses(df):
    """Write expenses back to expenses.csv, ordered by id."""
    out = df[COLUMNS].copy()
    out["amount"] = out["amount"].round(2)
    out.sort_values("id").to_csv(DATA_FILE, index=False)


def next_id(df):
    """Next unused id. Rows are identified by id, never by position."""
    return 1 if df.empty else int(df["id"].max()) + 1


def validate(description, amount):
    """Return a list of validation error messages (empty means valid)."""
    errors = []
    if not description.strip():
        errors.append("Description cannot be empty.")
    if amount <= 0:
        errors.append("Amount must be greater than 0.")
    return errors


def money(value):
    return f"${value:,.2f}"


def apply_filters(df, categories, statuses, search):
    """Filter by category, status, and a text search over description/submitted_by."""
    result = df
    if categories:
        result = result.loc[result["category"].isin(categories)]
    if statuses:
        result = result.loc[result["status"].isin(statuses)]
    needle = search.strip().lower()
    if needle:
        # regex=False keeps punctuation in the search box (e.g. "(" or "+") from
        # being treated as a regular expression and raising.
        in_description = result["description"].str.lower().str.contains(
            needle, na=False, regex=False
        )
        in_submitted_by = result["submitted_by"].str.lower().str.contains(
            needle, na=False, regex=False
        )
        result = result.loc[in_description | in_submitted_by]
    return result


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

st.set_page_config(page_title="Club Expense Tracker", layout="wide")
st.title("Club Expense Tracker")
st.caption("[ORGANIZATION] — expense tracking for the club treasurer")

expenses = load_expenses()

# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

st.header("Dashboard")

if expenses.empty:
    st.info("No expenses yet — the dashboard fills in once you add one.")
else:
    total_spend = expenses["amount"].sum()
    unreimbursed = expenses.loc[
        expenses["status"].isin(UNREIMBURSED_STATUSES), "amount"
    ].sum()

    total_column, unreimbursed_column = st.columns(2)
    total_column.metric("Total spend", money(total_spend))
    unreimbursed_column.metric("Still unreimbursed", money(unreimbursed))
    st.caption(
        "Unreimbursed = Submitted + Approved. An expense counts as unreimbursed "
        "until the money has actually gone out."
    )

    st.subheader("Spend by category")
    # Categories with no expenses are left out by groupby. st.bar_chart sorts the
    # axis alphabetically itself, so no ordering is imposed here.
    by_category = expenses.groupby("category")["amount"].sum()
    st.bar_chart(by_category)

    st.caption("The dashboard covers all expenses; the filters below do not change it.")

# --------------------------------------------------------------------------
# Add an expense
# --------------------------------------------------------------------------

st.header("Add an expense")

with st.form("add_expense", clear_on_submit=True):
    left, right = st.columns(2)
    with left:
        add_date = st.date_input("Date", value=datetime.date.today())
        add_description = st.text_input("Description")
        add_amount = st.number_input("Amount ($)", min_value=0.0, step=1.0, format="%.2f")
    with right:
        add_category = st.selectbox("Category", CATEGORIES)
        add_submitted_by = st.text_input("Submitted by")
        add_status = st.selectbox("Status", STATUSES)
    add_clicked = st.form_submit_button("Add expense")

if add_clicked:
    errors = validate(add_description, add_amount)
    if errors:
        for error in errors:
            st.error(error)
    else:
        new_row = {
            "id": next_id(expenses),
            "date": add_date,
            "description": add_description.strip(),
            "amount": add_amount,
            "category": add_category,
            "submitted_by": add_submitted_by.strip(),
            "status": add_status,
        }
        expenses = pd.concat([expenses, pd.DataFrame([new_row])], ignore_index=True)
        save_expenses(expenses)
        st.success(f"Added: {new_row['description']} ({money(new_row['amount'])})")
        st.rerun()

# --------------------------------------------------------------------------
# Expense list
# --------------------------------------------------------------------------

st.header("Expenses")

filter_left, filter_middle, filter_right = st.columns(3)
with filter_left:
    category_filter = st.multiselect("Filter by category", CATEGORIES)
with filter_middle:
    status_filter = st.multiselect("Filter by status", STATUSES)
with filter_right:
    search_text = st.text_input("Search description or submitted by")

visible = apply_filters(expenses, category_filter, status_filter, search_text)

if expenses.empty:
    st.info("No expenses recorded yet. Add one above.")
elif visible.empty:
    st.warning("No expenses match these filters.")
else:
    st.caption(
        f"Showing {len(visible)} of {len(expenses)} expenses "
        f"— {money(visible['amount'].sum())} in view"
    )
    st.dataframe(visible, hide_index=True, width="stretch")

# --------------------------------------------------------------------------
# Edit or delete
# --------------------------------------------------------------------------

st.header("Edit or delete an expense")

if visible.empty:
    st.caption("Nothing to edit — no expenses match the filters above.")
else:
    # The picker lists the filtered rows, so the filters double as a way to find an
    # expense. Selection is by id, so the row edited is always the row chosen even
    # though its position in the filtered table differs from the full table.
    options = {
        int(row.id): f"#{int(row.id)} — {row.description} ({money(row.amount)})"
        for row in visible.itertuples()
    }
    selected_id = st.selectbox(
        "Expense",
        options=list(options.keys()),
        format_func=lambda key: options[key],
    )

    current = expenses.loc[expenses["id"] == selected_id].iloc[0]

    with st.form("edit_expense"):
        left, right = st.columns(2)
        with left:
            edit_date = st.date_input("Date", value=current["date"])
            edit_description = st.text_input("Description", value=current["description"])
            edit_amount = st.number_input(
                "Amount ($)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                value=float(current["amount"]),
            )
        with right:
            edit_category = st.selectbox(
                "Category", CATEGORIES, index=CATEGORIES.index(current["category"])
            )
            edit_submitted_by = st.text_input(
                "Submitted by", value=current["submitted_by"]
            )
            edit_status = st.selectbox(
                "Status", STATUSES, index=STATUSES.index(current["status"])
            )
        save_clicked = st.form_submit_button("Save changes")

    if save_clicked:
        errors = validate(edit_description, edit_amount)
        if errors:
            for error in errors:
                st.error(error)
        else:
            target = expenses["id"] == selected_id
            expenses.loc[target, "date"] = edit_date
            expenses.loc[target, "description"] = edit_description.strip()
            expenses.loc[target, "amount"] = edit_amount
            expenses.loc[target, "category"] = edit_category
            expenses.loc[target, "submitted_by"] = edit_submitted_by.strip()
            expenses.loc[target, "status"] = edit_status
            save_expenses(expenses)
            st.success(f"Saved changes to #{selected_id}.")
            st.rerun()

    # Deleting a row cannot be undone, so it takes two clicks.
    st.subheader("Delete")

    if st.session_state.get("pending_delete") == selected_id:
        st.warning(f"Delete #{selected_id} — {current['description']}? This cannot be undone.")
        confirm, cancel = st.columns(2)
        if confirm.button("Yes, delete it"):
            expenses = expenses.loc[expenses["id"] != selected_id]
            save_expenses(expenses)
            st.session_state["pending_delete"] = None
            st.success(f"Deleted #{selected_id}.")
            st.rerun()
        if cancel.button("Cancel"):
            st.session_state["pending_delete"] = None
            st.rerun()
    else:
        if st.button(f"Delete #{selected_id}"):
            st.session_state["pending_delete"] = selected_id
            st.rerun()
