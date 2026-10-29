# Task 3.5 — books ingestion

This project ingests the supplied `task1_d.json` into SQLite and builds a yearly
summary table in SQL. Despite its filename, the supplied source uses Ruby hash
syntax (`:key=>value`); `ingest.py` normalizes that syntax before validation.

Prices are stored as integer USD cents. Euro prices use the required fixed
conversion rate, `€1 = $1.20`, and decimal half-up rounding to cents.

```powershell
python ingest.py
python -m unittest -v
```

Outputs include the database, the full summary as CSV, and a ready-to-paste
email body containing both table row counts and every calculated summary row.
