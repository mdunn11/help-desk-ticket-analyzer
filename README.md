
# Help Desk Ticket Analyzer

A Python learning and portfolio project for analyzing basic IT help desk ticket data. V1 provides a working CSV-to-summary workflow using only the Python standard library.

## Run

Use Python 3.10 or newer. No packages need to be installed.

```bash
python main.py
```

The program loads `tickets.csv` beside `main.py`, even when launched from another working directory. The menu supports:

1. View all tickets
2. Search by numeric ticket ID
3. View the ticket summary
4. Exit
5. Export the summary to CSV

Invalid menu choices and search input return to the menu. End-of-input or Ctrl+C at a prompt exits cleanly. Importing `main` does not start the menu.

## Ticket CSV format

The existing input format is preserved:

```csv
id,category,priority,status
1001,Password Reset,Medium,open
1002,Software,High,pending
1003,Network,High,open
```

- The header must contain exactly these four unique column names; column order may vary. Header names are case-sensitive.
- IDs must be integers and unique among accepted rows. The first valid row for an ID is retained; later duplicates are skipped.
- Categories must be nonblank. Surrounding whitespace is removed and categories are converted to title case, matching the original behavior.
- Priorities accept Low, Medium, or High, ignoring case and surrounding whitespace.
- Statuses accept open, closed, or pending, ignoring case and surrounding whitespace.
- Files must use UTF-8; a UTF-8 byte-order mark is accepted. Standard CSV quoting supports commas inside categories. Blank lines are ignored.

Invalid rows (including missing or extra fields) are skipped with a message identifying the CSV line and reason. Missing/unreadable files, invalid encoding, invalid headers, and malformed CSV quoting stop loading with an error message; partial data from a malformed file is not analyzed. A header-only file or a file with no valid rows produces an empty dataset with zero summary counts.

## Summary and export

The summary counts open, closed, pending, high-priority, unresolved, and high-priority unresolved tickets, plus tickets by category. **Unresolved means open or pending.** High-priority totals include closed tickets as well.

Choose option 5 and enter an output path, or press Enter to use `ticket_summary.csv` in the current working directory. Exported counts reflect only accepted rows. The output format is separate from the ticket input format:

```csv
section,name,count
summary,total,3
summary,open,2
summary,closed,0
summary,pending,1
summary,high_priority,2
summary,unresolved,3
summary,high_priority_unresolved,2
category,Network,1
category,Password Reset,1
category,Software,1
```

Category rows are sorted by name. An existing summary file at the chosen path is replaced after writing succeeds. The destination directory must already exist. Export rejects the input CSV path, including symlink and hard-link aliases, to protect ticket data. Write failures are reported and return to the menu; a failed write does not replace an existing report.

The input has no creation dates, resolution dates, due dates, or SLA information. V1 therefore does not calculate resolution time or overdue tickets.

## Automated tests

From the repository directory:

```bash
python -m unittest discover -s tests -v
```

Tests cover the sample analysis, search, menu control flow, input recovery, CSV validation and normalization, empty data, file errors, export contents, source protection, failed-write cleanup, and command-line startup.

## Project structure

- `main.py`: CSV loading, display, search, analysis, export, and interactive menu.
- `tickets.csv`: original sample ticket data.
- `tests/test_main.py`: standard-library automated tests.
- `.gitignore`: Python caches, virtual environments, and the default generated report.

## Learning focus

This project demonstrates functions, lists and dictionaries, loops, conditional logic, exception handling, file processing, CSV validation, and automated testing. It is part of my continued technical training in Python, IT support, and systems administration, and is developed incrementally so that the functionality reflects concepts I can explain, troubleshoot, and apply.

---

**Author:** Marquita L. Dunn

### Copyright

© 2026 Marquita L. Dunn. All rights reserved.

This repository is shared publicly for educational and professional portfolio purposes. No permission is granted to reproduce, distribute, or represent this work as your own.
