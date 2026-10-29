DROP TABLE IF EXISTS yearly_book_summary;
DROP TABLE IF EXISTS books;

CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT,
    publisher TEXT,
    publication_year INTEGER NOT NULL,
    original_currency TEXT NOT NULL CHECK (original_currency IN ('USD', 'EUR')),
    original_price TEXT NOT NULL,
    price_usd_cents INTEGER NOT NULL CHECK (price_usd_cents >= 0)
);

CREATE TABLE yearly_book_summary (
    publication_year INTEGER PRIMARY KEY,
    book_count INTEGER NOT NULL,
    average_price_usd NUMERIC NOT NULL
);
