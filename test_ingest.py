from decimal import Decimal
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ingest import EURO_TO_USD, build_database, load_ruby_style_json, price_to_usd_cents


class IngestionTests(unittest.TestCase):
    def test_currency_conversion_rounds_to_cents(self):
        self.assertEqual(EURO_TO_USD, Decimal("1.2"))
        self.assertEqual(price_to_usd_cents("€5.99"), ("EUR", 719))
        self.assertEqual(price_to_usd_cents("$31.99"), ("USD", 3199))

    def test_supplied_file_loads_and_builds(self):
        project = Path(__file__).resolve().parent
        source = project / "data" / "task1_d.json"
        records = load_ruby_style_json(source)
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "books.sqlite3"
            build_database(source, database)
            with closing(sqlite3.connect(database)) as connection:
                book_count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
                summary_count = connection.execute(
                    "SELECT COUNT(*) FROM yearly_book_summary"
                ).fetchone()[0]
            self.assertEqual(book_count, len(records))
            self.assertGreater(summary_count, 0)


if __name__ == "__main__":
    unittest.main()
