import csv
import os
from pathlib import Path
import tempfile


DEFAULT_TICKETS_PATH = Path(__file__).with_name("tickets.csv")
REQUIRED_FIELDS = ("id", "category", "priority", "status")
SUMMARY_METRICS = (
    "open", "closed", "pending", "high_priority", "unresolved",
    "high_priority_unresolved",
)


def load_tickets(filename=DEFAULT_TICKETS_PATH):
    """Load valid rows; report rejected rows and raise ValueError for bad files."""
    tickets = []
    seen_ids = set()
    try:
        with open(filename, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            if (reader.fieldnames is None
                    or len(reader.fieldnames) != len(REQUIRED_FIELDS)
                    or set(reader.fieldnames) != set(REQUIRED_FIELDS)):
                raise ValueError("CSV header must contain exactly id, category, priority, status.")
            for row in reader:
                line = reader.line_num
                if None in row or any(row[field] is None for field in REQUIRED_FIELDS):
                    print(f"Skipping CSV line {line}: expected four fields.")
                    continue
                try:
                    ticket_id = int(row["id"].strip())
                except ValueError:
                    print(f"Skipping CSV line {line}: ID must be an integer.")
                    continue
                if ticket_id in seen_ids:
                    print(f"Skipping CSV line {line}: duplicate ticket ID {ticket_id}.")
                    continue
                status = row["status"].strip().lower()
                priority = row["priority"].strip().title()
                category = row["category"].strip().title()
                if status not in ("open", "closed", "pending"):
                    print(f"Skipping CSV line {line}: invalid status {status!r}.")
                    continue
                if priority not in ("Low", "Medium", "High"):
                    print(f"Skipping CSV line {line}: invalid priority {priority!r}.")
                    continue
                if not category:
                    print(f"Skipping CSV line {line}: category cannot be blank.")
                    continue
                tickets.append({"id": ticket_id, "category": category,
                                "priority": priority, "status": status})
                seen_ids.add(ticket_id)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"Could not load tickets from {filename}: {error}") from error
    return tickets


def export_summary(tickets, filename="ticket_summary.csv", source_path=DEFAULT_TICKETS_PATH):
    """Write counts atomically, without overwriting the input CSV."""
    target = Path(filename)
    source = Path(source_path)
    if (target.resolve() == source.resolve()
            or (target.exists() and source.exists() and os.path.samefile(target, source))):
        raise ValueError("Summary destination cannot be the input ticket CSV.")
    *counts, category_counts = analyze_tickets(tickets)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=target.parent,
                prefix=".ticket-summary-", suffix=".tmp", delete=False) as file:
            temporary_path = Path(file.name)
            writer = csv.writer(file)
            writer.writerow(("section", "name", "count"))
            writer.writerow(("summary", "total", len(tickets)))
            writer.writerows(("summary", name, count)
                            for name, count in zip(SUMMARY_METRICS, counts))
            writer.writerows(("category", category, count)
                            for category, count in sorted(category_counts.items()))
        os.replace(temporary_path, target)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def display_tickets(tickets):
    for ticket in tickets:
        print("Ticket ID:", ticket["id"])
        print("Category:", ticket["category"])
        print("Priority:", ticket["priority"])
        print("Status:", ticket["status"])
        print("--------------------")


def analyze_tickets(tickets):
    open_count = 0
    closed_count = 0
    pending_count = 0
    high_priority_count = 0
    unresolved_count = 0
    high_priority_unresolved_count = 0
    category_counts = {}
    for ticket in tickets:
        category = ticket["category"]
        if category not in category_counts:
            category_counts[category] = 1
        else:
            category_counts[category] += 1
        if ticket["status"] == "open":
            open_count += 1
        elif ticket["status"] == "closed":
            closed_count += 1
        elif ticket["status"] == "pending":
            pending_count += 1
        if ticket["priority"] == "High":
            high_priority_count += 1
        if ticket["status"] == "open" or ticket["status"] == "pending":
            unresolved_count += 1
        if ticket["priority"] == "High" and (ticket["status"] == "open" or ticket["status"] == "pending"):
            high_priority_unresolved_count += 1
    return open_count, closed_count, pending_count, high_priority_count, unresolved_count, high_priority_unresolved_count, category_counts


def search_ticket(tickets, search_id):
    for ticket in tickets:
        if ticket["id"] == search_id:
            return ticket
    return None


def main():
    print("IT Help Desk Ticket Analyzer")
    try:
        tickets = load_tickets()
    except ValueError as error:
        print(error)
        return
    if not tickets:
        print("No valid tickets were loaded.")
    while True:
        print("\nMenu")
        print("1. View all tickets")
        print("2. Search for a ticket")
        print("3. View ticket summary")
        print("4. Exit")
        print("5. Export summary CSV")
        try:
            choice = input("Choose an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting program.")
            break
        if choice == "1":
            display_tickets(tickets)
        elif choice == "2":
            try:
                search_id = int(input("Enter Ticket ID: "))
            except ValueError:
                print("Please enter a valid numeric Ticket ID.")
                continue
            except (EOFError, KeyboardInterrupt):
                print("\nExiting program.")
                break
            found_ticket = search_ticket(tickets, search_id)
            if found_ticket is not None:
                print("Ticket Found:")
                print("Ticket ID:", found_ticket["id"])
                print("Category:", found_ticket["category"])
                print("Priority:", found_ticket["priority"])
                print("Status:", found_ticket["status"])
            else:
                print("Ticket not found.")
        elif choice == "3":
            open_count, closed_count, pending_count, high_priority_count, unresolved_count, high_priority_unresolved_count, category_counts = analyze_tickets(tickets)
            print("Total Open Tickets:", open_count)
            print("Total Closed Tickets:", closed_count)
            print("Total Pending Tickets:", pending_count)
            print("Total High Priority Tickets:", high_priority_count)
            print("Total Unresolved Tickets:", unresolved_count)
            print("High Priority Unresolved Tickets:", high_priority_unresolved_count)
            print("Tickets by Category:")
            for category, count in category_counts.items():
                print(f"  {category}: {count}")
        elif choice == "4":
            print("Exiting program.")
            break
        elif choice == "5":
            try:
                filename = input("Summary CSV path [ticket_summary.csv]: ").strip()
                export_summary(tickets, filename or "ticket_summary.csv")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting program.")
                break
            except (OSError, ValueError, csv.Error) as error:
                print(f"Could not export summary: {error}")
            else:
                print(f"Summary exported to {filename or 'ticket_summary.csv'}.")
        else:
            print("Invalid option. Please choose 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()