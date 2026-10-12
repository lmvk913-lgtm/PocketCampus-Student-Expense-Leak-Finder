"""
PocketCampus — Student Expense Leak Finder
A beginner-friendly command-line expense tracker.

Run with:
    python main.py

Uses only Python's standard library.
"""

import json
import csv
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

DATA_FILE = Path(__file__).with_name("expenses.json")
BUDGET_FILE = Path(__file__).with_name("budget.json")

CATEGORIES = [
    "Food",
    "Transport",
    "College Supplies",
    "Shopping",
    "Subscriptions",
    "Entertainment",
    "Health",
    "Other",
]


def load_json(path, default):
    """Read JSON data safely. Return default if the file does not exist."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        print(f"Warning: could not read {path.name}. Using empty/default data.")
        return default


def save_json(path, data):
    """Write data to a JSON file."""
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return True
    except OSError as error:
        print(f"Could not save {path.name}: {error}")
        return False


def load_expenses():
    data = load_json(DATA_FILE, [])
    return data if isinstance(data, list) else []


def load_budget():
    data = load_json(BUDGET_FILE, {"monthly_budget": 0.0})
    if not isinstance(data, dict):
        return {"monthly_budget": 0.0}
    return data


def ask_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be blank.")


def ask_amount(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            amount = float(raw)
            if amount <= 0:
                print("Enter an amount greater than zero.")
                continue
            if not amount < float("inf"):
                print("Enter a valid finite amount.")
                continue
            return round(amount, 2)
        except ValueError:
            print("Enter a valid amount, for example 45 or 125.50.")


def ask_date(prompt="Date (YYYY-MM-DD, press Enter for today): "):
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return date.today().isoformat()
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d").date()
            if parsed > date.today():
                confirm = input("This date is in the future. Use it anyway? (y/n): ").strip().lower()
                if confirm != "y":
                    continue
            return parsed.isoformat()
        except ValueError:
            print("Use the date format YYYY-MM-DD, for example 2026-10-12.")


def choose_category():
    print("\nChoose a category:")
    for index, category in enumerate(CATEGORIES, start=1):
        print(f"{index}. {category}")

    while True:
        raw = input(f"Category number (1-{len(CATEGORIES)}): ").strip()
        try:
            index = int(raw)
            if 1 <= index <= len(CATEGORIES):
                return CATEGORIES[index - 1]
        except ValueError:
            pass
        print("Choose a valid category number.")


def add_expense(expenses):
    print("\n--- Add an Expense ---")
    description = ask_non_empty("What did you spend on? ")
    amount = ask_amount("Amount (₹): ")
    category = choose_category()
    expense_date = ask_date()

    expense = {
        "id": max((item.get("id", 0) for item in expenses), default=0) + 1,
        "description": description,
        "amount": amount,
        "category": category,
        "date": expense_date,
    }
    expenses.append(expense)

    if save_json(DATA_FILE, expenses):
        print(f"Saved: ₹{amount:.2f} for {description} ({category}) on {expense_date}.")


def print_expenses(expenses):
    if not expenses:
        print("\nNo expenses recorded yet.")
        return

    print("\n" + "-" * 78)
    print(f"{'ID':<5}{'DATE':<13}{'CATEGORY':<21}{'DESCRIPTION':<25}{'AMOUNT (₹)':>14}")
    print("-" * 78)

    for item in sorted(expenses, key=lambda entry: (entry.get("date", ""), entry.get("id", 0)), reverse=True):
        description = item.get("description", "")[:24]
        category = item.get("category", "")[:20]
        print(
            f"{item.get('id', ''):<5}"
            f"{item.get('date', ''):<13}"
            f"{category:<21}"
            f"{description:<25}"
            f"{item.get('amount', 0):>14.2f}"
        )
    print("-" * 78)


def ask_month():
    while True:
        raw = input("Month to analyze (YYYY-MM, press Enter for current month): ").strip()
        if raw == "":
            return date.today().strftime("%Y-%m")
        try:
            datetime.strptime(raw, "%Y-%m")
            return raw
        except ValueError:
            print("Use YYYY-MM format, for example 2026-10.")


def expenses_for_month(expenses, month):
    return [
        item for item in expenses
        if isinstance(item.get("date"), str) and item["date"].startswith(month)
    ]


def set_monthly_budget(budget_data):
    print("\n--- Set Monthly Budget ---")
    while True:
        raw = input("Monthly budget in rupees (enter 0 to clear the budget): ").strip()
        try:
            amount = float(raw)
            if amount < 0 or amount == float("inf"):
                print("Budget cannot be negative. Enter a valid amount.")
                continue
            budget_data["monthly_budget"] = round(amount, 2)
            if save_json(BUDGET_FILE, budget_data):
                if amount == 0:
                    print("Monthly budget cleared.")
                else:
                    print(f"Monthly budget set to ₹{amount:.2f}.")
            return
        except ValueError:
            print("Enter a valid number, such as 5000 or 7500.50.")


def monthly_summary(expenses, budget_data):
    month = ask_month()
    monthly = expenses_for_month(expenses, month)
    total_spent = sum(item.get("amount", 0) for item in monthly)
    budget = float(budget_data.get("monthly_budget", 0) or 0)

    print(f"\n--- Spending Summary: {month} ---")
    print(f"Number of recorded expenses: {len(monthly)}")
    print(f"Total spent: ₹{total_spent:.2f}")

    if not monthly:
        print("No expenses recorded for this month.")
    else:
        category_totals = defaultdict(float)
        for item in monthly:
            category_totals[item.get("category", "Other")] += item.get("amount", 0)

        print("\nSpending by category:")
        for category, amount in sorted(category_totals.items(), key=lambda pair: pair[1], reverse=True):
            share = (amount / total_spent * 100) if total_spent else 0
            print(f"  {category:<22} ₹{amount:>9.2f}  ({share:5.1f}%)")

        top_category, top_amount = max(category_totals.items(), key=lambda pair: pair[1])
        print(f"\nLargest spending category: {top_category} (₹{top_amount:.2f})")
        possible_saving = top_amount * 0.10
        print(
            f"If you reduce spending in {top_category} by 10%, "
            f"you would save about ₹{possible_saving:.2f} this month."
        )

    if budget > 0:
        remaining = budget - total_spent
        print(f"\nMonthly budget: ₹{budget:.2f}")
        if remaining >= 0:
            print(f"Budget remaining: ₹{remaining:.2f}")
        else:
            print(f"Over budget by: ₹{abs(remaining):.2f}")
    else:
        print("\nNo monthly budget set. Choose option 4 to set one.")


def find_expense_by_id(expenses, expense_id):
    for item in expenses:
        if item.get("id") == expense_id:
            return item
    return None


def delete_expense(expenses):
    if not expenses:
        print("\nNo expenses to delete.")
        return

    print_expenses(expenses)
    while True:
        raw = input("Enter the ID of the expense to delete (or 0 to cancel): ").strip()
        try:
            expense_id = int(raw)
            if expense_id == 0:
                print("Deletion cancelled.")
                return
            expense = find_expense_by_id(expenses, expense_id)
            if expense is None:
                print("No expense found with that ID.")
                continue
            confirmation = input(
                f"Delete '{expense['description']}' for ₹{expense['amount']:.2f}? (y/n): "
            ).strip().lower()
            if confirmation == "y":
                expenses.remove(expense)
                if save_json(DATA_FILE, expenses):
                    print("Expense deleted.")
            else:
                print("Deletion cancelled.")
            return
        except ValueError:
            print("Enter a valid whole-number ID.")


def export_csv(expenses):
    if not expenses:
        print("\nNo expenses to export.")
        return

    output_path = Path(__file__).with_name("expenses_export.csv")
    fields = ["id", "date", "description", "category", "amount"]
    try:
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for item in sorted(expenses, key=lambda entry: entry.get("date", "")):
                writer.writerow({field: item.get(field, "") for field in fields})
        print(f"Exported {len(expenses)} expenses to {output_path.name}.")
    except OSError as error:
        print(f"Could not export CSV: {error}")


def show_menu():
    print("\n" + "=" * 44)
    print("       POCKETCAMPUS EXPENSE FINDER")
    print("=" * 44)
    print("1. Add an expense")
    print("2. View all expenses")
    print("3. Analyze monthly spending")
    print("4. Set monthly budget")
    print("5. Delete an expense")
    print("6. Export expenses to CSV")
    print("7. Exit")
    print("-" * 44)


def main():
    expenses = load_expenses()
    budget_data = load_budget()

    print("Welcome to PocketCampus!")
    print("Track your spending, spot expense leaks, and plan your budget.")
    print("Your data is stored locally on this computer.")

    while True:
        show_menu()
        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            print_expenses(expenses)
        elif choice == "3":
            monthly_summary(expenses, budget_data)
        elif choice == "4":
            set_monthly_budget(budget_data)
        elif choice == "5":
            delete_expense(expenses)
        elif choice == "6":
            export_csv(expenses)
        elif choice == "7":
            print("Thanks for using PocketCampus. Spend mindfully!")
            break
        else:
            print("Invalid option. Choose a number from 1 to 7.")


if __name__ == "__main__":
    main()
