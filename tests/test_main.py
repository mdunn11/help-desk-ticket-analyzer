import contextlib
import csv
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import main


class TicketAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "tickets.csv"

    def load(self, content):
        self.source.write_text(content, encoding="utf-8")
        self.output = io.StringIO()
        with contextlib.redirect_stdout(self.output):
            return main.load_tickets(self.source)

    def run_menu(self, inputs, tickets=None):
        output = io.StringIO()
        with patch("main.load_tickets", return_value=tickets or []), \
                patch("builtins.input", side_effect=inputs), \
                contextlib.redirect_stdout(output):
            main.main()
        return output.getvalue()

    def test_sample_analysis_and_search(self):
        tickets = main.load_tickets()
        self.assertEqual(main.analyze_tickets(tickets),
                         (2, 0, 1, 2, 3, 2,
                          {"Password Reset": 1, "Software": 1, "Network": 1}))
        self.assertEqual(main.search_ticket(tickets, 1002), tickets[1])
        self.assertIsNone(main.search_ticket(tickets, 9999))

    def test_bom_reordered_header_normalization_and_quoted_category(self):
        tickets = self.load('\ufeffstatus,priority,category,id\n OPEN , high ," network, access ", 7 \n')
        self.assertEqual(tickets, [{"id": 7, "category": "Network, Access",
                                    "priority": "High", "status": "open"}])

    def test_invalid_rows_are_reported_and_valid_rows_survive(self):
        tickets = self.load("id,category,priority,status\n"
                            "bad,Network,High,open\n"
                            "1,Network,High\n"
                            "2,Network,High,open,extra\n"
                            "3,Network,High,unknown\n"
                            "4,Network,Urgent,open\n"
                            "5, ,High,open\n"
                            "6,Network,High,open\n"
                            "6,Software,Low,closed\n"
                            "7,Software,Low,closed\n")
        self.assertEqual([ticket["id"] for ticket in tickets], [6, 7])
        for line in (2, 3, 4, 5, 6, 7, 9):
            self.assertIn(f"Skipping CSV line {line}:", self.output.getvalue())

    def test_invalid_row_does_not_reserve_id(self):
        tickets = self.load("id,category,priority,status\n1,X,High,bad\n1,X,High,open\n")
        self.assertEqual(len(tickets), 1)

    def test_invalid_headers(self):
        for header in ("", "id,category,priority", "id,id,priority,status",
                       "id,category,priority,status,extra"):
            with self.subTest(header=header), self.assertRaisesRegex(ValueError, "CSV header"):
                self.load(header + "\n")

    def test_header_only_and_blank_lines(self):
        self.assertEqual(self.load("id,category,priority,status\n\n"), [])

    def test_missing_unreadable_invalid_encoding_and_malformed_files(self):
        with self.assertRaisesRegex(ValueError, "Could not load"):
            main.load_tickets(self.source)
        with patch("builtins.open", side_effect=PermissionError("denied")), \
                self.assertRaisesRegex(ValueError, "denied"):
            main.load_tickets(self.source)
        self.source.write_bytes(b"id,category,priority,status\n1,\xff,High,open")
        with self.assertRaisesRegex(ValueError, "Could not load"):
            main.load_tickets(self.source)
        with self.assertRaisesRegex(ValueError, "Could not load"):
            self.load('id,category,priority,status\n1,"unterminated,High,open\n')

    def test_analysis_includes_closed_high_and_pending_low(self):
        tickets = self.load("id,category,priority,status\n1,X,High,closed\n"
                            "2,X,Low,pending\n3,Y,Medium,open\n")
        self.assertEqual(main.analyze_tickets(tickets), (1, 1, 1, 1, 2, 0, {"X": 2, "Y": 1}))
        self.assertEqual(main.analyze_tickets([]), (0, 0, 0, 0, 0, 0, {}))

    def test_export_counts_and_csv_quoting(self):
        tickets = self.load('id,category,priority,status\n1,"Network, Access",High,pending\n')
        target = Path(self.temp.name) / "summary.csv"
        main.export_summary(tickets, target, self.source)
        with target.open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        self.assertEqual(rows, [["section", "name", "count"],
                               ["summary", "total", "1"],
                               ["summary", "open", "0"],
                               ["summary", "closed", "0"],
                               ["summary", "pending", "1"],
                               ["summary", "high_priority", "1"],
                               ["summary", "unresolved", "1"],
                               ["summary", "high_priority_unresolved", "1"],
                               ["category", "Network, Access", "1"]])

    def test_empty_export(self):
        target = Path(self.temp.name) / "summary.csv"
        main.export_summary([], target)
        with target.open(newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["count"] == "0" for row in rows))

    def test_export_protects_source_and_aliases(self):
        self.source.write_text("original")
        alias = self.source.with_name("alias.csv")
        alias.symlink_to(self.source)
        hardlink = self.source.with_name("hardlink.csv")
        hardlink.hardlink_to(self.source)
        for target in (self.source, alias, hardlink):
            with self.subTest(target=target), self.assertRaises(ValueError):
                main.export_summary([], target, self.source)
        self.assertEqual(self.source.read_text(), "original")

    def test_failed_export_preserves_existing_file_and_cleans_temporary(self):
        target = self.source.with_name("summary.csv")
        target.write_text("previous report")
        with patch("main.os.replace", side_effect=PermissionError("denied")), \
                self.assertRaises(PermissionError):
            main.export_summary([], target)
        self.assertEqual(target.read_text(), "previous report")
        self.assertEqual(list(target.parent.glob(".ticket-summary-*.tmp")), [])
        with self.assertRaises(OSError):
            main.export_summary([], target.parent / "missing" / "summary.csv")

    def test_menu_actions_do_not_trigger_invalid_option(self):
        tickets = main.load_tickets()
        output = self.run_menu(["1", "2", "1002", "3", "4"], tickets)
        self.assertNotIn("Invalid option", output)
        self.assertIn("Ticket Found:", output)
        self.assertIn("Total Open Tickets: 2", output)

    def test_menu_invalid_search_and_option_recover(self):
        output = self.run_menu(["2", "bad", "2", "9999", "bogus", "4"])
        self.assertIn("valid numeric Ticket ID", output)
        self.assertIn("Ticket not found", output)
        self.assertEqual(output.count("Invalid option"), 1)

    def test_menu_export_success_and_failure_recover(self):
        target = self.source.with_name("summary.csv")
        output = self.run_menu(["5", str(target), "5", str(target / "bad.csv"), "4"])
        self.assertTrue(target.exists())
        self.assertIn("Summary exported", output)
        self.assertIn("Could not export summary", output)
        self.assertIn("Exiting program", output)

    def test_default_export_path(self):
        with patch("main.export_summary") as export:
            self.run_menu(["5", "", "4"])
        export.assert_called_once_with([], "ticket_summary.csv")

    def test_menu_handles_load_failure_and_interruption(self):
        output = io.StringIO()
        with patch("main.load_tickets", side_effect=ValueError("bad CSV")), \
                patch("builtins.input") as prompt, contextlib.redirect_stdout(output):
            main.main()
        prompt.assert_not_called()
        self.assertIn("bad CSV", output.getvalue())
        for inputs in ([EOFError()], [KeyboardInterrupt()], ["2", EOFError()],
                       ["5", KeyboardInterrupt()]):
            with self.subTest(inputs=inputs):
                self.assertIn("Exiting program", self.run_menu(inputs))

    def test_import_has_no_output_or_interactive_side_effects(self):
        result = subprocess.run([sys.executable, "-c", "import main"],
                                cwd=Path(main.__file__).parent, capture_output=True,
                                text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_cli_loads_bundled_csv_from_another_directory(self):
        result = subprocess.run([sys.executable, main.__file__], cwd=self.temp.name,
                                input="3\n4\n", capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Total Open Tickets: 2", result.stdout)


if __name__ == "__main__":
    unittest.main()
