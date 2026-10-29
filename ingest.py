from __future__ import annotations

import argparse
import csv
from contextlib import closing
import json
import re
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

EURO_TO_USD = Decimal("1.2")
MONEY = Decimal("0.01")
RUBY_KEY = re.compile(r"([,{]\s*):([A-Za-z_]\w*)\s*=>")


def load_ruby_style_json(path: Path) -> list[dict]:
    """Read the supplied Ruby-hash-like file and return ordinary dictionaries."""
    raw = path.read_text(encoding="utf-8-sig")
    normalized = RUBY_KEY.sub(r'\1"\2":', raw)
    normalized = re.sub(r"\bnil\b", "null", normalized)
    normalized = re.sub(r"\btrue\b", "true", normalized)
    normalized = re.sub(r"\bfalse\b", "false", normalized)
    data = json.loads(normalized)
    if not isinstance(data, list):
        raise ValueError("Expected a top-level array")
    return data


def price_to_usd_cents(value: str) -> tuple[str, int]:
    if not isinstance(value, str) or len(value) < 2:
        raise ValueError(f"Malformed price: {value!r}")
    symbol, amount_text = value[0], value[1:]
    if symbol not in {"$", "€"}:
        raise ValueError(f"Unsupported currency: {value!r}")
    amount = Decimal(amount_text)
    if amount < 0:
        raise ValueError(f"Negative price: {value!r}")
    currency = "USD" if symbol == "$" else "EUR"
    usd = amount if currency == "USD" else amount * EURO_TO_USD
    cents = int((usd.quantize(MONEY, rounding=ROUND_HALF_UP) * 100).to_integral_exact())
    return currency, cents


def transform(record: dict) -> tuple:
    required = {"id", "title", "author", "year", "price"}
    missing = required.difference(record)
    if missing:
        raise ValueError(f"Missing fields {sorted(missing)} in record {record!r}")
    currency, cents = price_to_usd_cents(record["price"])
    year = int(record["year"])
    if year < 0:
        raise ValueError(f"Invalid publication year: {year}")
    return (
        str(record["id"]),
        str(record["title"]),
        str(record["author"]),
        record.get("genre"),
        record.get("publisher"),
        year,
        currency,
        record["price"],
        cents,
    )


def build_database(source: Path, database: Path) -> None:
    project = Path(__file__).resolve().parent
    records = load_ruby_style_json(source)
    rows = [transform(record) for record in records]

    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript((project / "schema.sql").read_text(encoding="utf-8"))
        connection.executemany(
            """
            INSERT INTO books (
                id, title, author, genre, publisher, publication_year,
                original_currency, original_price, price_usd_cents
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.executescript((project / "summary.sql").read_text(encoding="utf-8"))
        connection.commit()


def export_results(database: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        counts = dict(
            connection.execute(
                """
                SELECT 'books' AS table_name, COUNT(*) AS row_count FROM books
                UNION ALL
                SELECT 'yearly_book_summary', COUNT(*) FROM yearly_book_summary
                """
            ).fetchall()
        )
        summary = connection.execute(
            """
            SELECT publication_year, book_count, average_price_usd
            FROM yearly_book_summary
            ORDER BY publication_year
            """
        ).fetchall()

    with (output_dir / "yearly_book_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["publication_year", "book_count", "average_price_usd"])
        writer.writerows(summary)

    lines = [
        "Subject: Task 3.5 submission — Devyanshu Agrawal",
        "",
        "Hello Pavel,",
        "",
        "Please find attached my Task 3.5 video demonstration.",
        "",
        f"Source table row count (books): {counts['books']}",
        f"Summary table row count (yearly_book_summary): {counts['yearly_book_summary']}",
        "",
        "Complete summary table:",
        "",
        "| publication_year | book_count | average_price_usd |",
        "|---:|---:|---:|",
    ]
    lines.extend(f"| {row[0]} | {row[1]} | {row[2]:.2f} |" for row in summary)
    lines.extend(["", "Best regards,", "Devyanshu Agrawal", ""])
    (output_dir / "submission_email.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    project = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Ingest Task 3.5 book data into SQLite")
    parser.add_argument("--source", type=Path, default=project / "data" / "task1_d.json")
    parser.add_argument("--database", type=Path, default=project / "outputs" / "task35.sqlite3")
    parser.add_argument("--output-dir", type=Path, default=project / "outputs")
    args = parser.parse_args()
    build_database(args.source, args.database)
    export_results(args.database, args.output_dir)
    print(f"Created {args.database}")


if __name__ == "__main__":
    main()
