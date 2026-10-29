INSERT INTO yearly_book_summary (publication_year, book_count, average_price_usd)
SELECT
    publication_year,
    COUNT(*) AS book_count,
    ROUND(AVG(price_usd_cents) / 100.0, 2) AS average_price_usd
FROM books
GROUP BY publication_year
ORDER BY publication_year;
