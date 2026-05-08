# ============================================================
# load_db.py  —  Phase 4
# Loads clean CSVs into SQLite, filtered to years 2006-2025
# ============================================================

import os
import sqlite3
import pandas as pd

CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'clean')
DB_PATH   = os.path.join(os.path.dirname(__file__), '..', 'database', 'patents.db')
SCHEMA    = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')

YEAR_FROM = 2006
YEAR_TO   = 2025


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA foreign_keys=OFF")
    return conn


def apply_schema(conn):
    print("  Applying schema ...")
    with open(SCHEMA, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    print("  Schema applied.")


def load_patents(conn):
    path = os.path.join(CLEAN_DIR, 'clean_patents.csv')
    print(f"  Loading patents ({YEAR_FROM}–{YEAR_TO}) ...")
    total = 0
    for chunk in pd.read_csv(path, dtype=str, chunksize=50_000):
        chunk = chunk[chunk['year'].isin([str(y) for y in range(YEAR_FROM, YEAR_TO + 1)])]
        if len(chunk) == 0:
            continue
        chunk.to_sql('patents', conn, if_exists='append', index=False)
        total += len(chunk)
        print(f"    {total:,} rows loaded ...", end='\r')
    conn.commit()
    print(f"  Done: {total:,} rows into [patents]          ")
    return set(pd.read_sql("SELECT patent_id FROM patents", conn)['patent_id'])


def load_inventors(conn):
    path = os.path.join(CLEAN_DIR, 'clean_inventors.csv')
    print(f"  Loading inventors ...")
    total = 0
    for chunk in pd.read_csv(path, dtype=str, chunksize=50_000):
        chunk.to_sql('inventors', conn, if_exists='append', index=False)
        total += len(chunk)
        print(f"    {total:,} rows loaded ...", end='\r')
    conn.commit()
    print(f"  Done: {total:,} rows into [inventors]          ")


def load_companies(conn):
    path = os.path.join(CLEAN_DIR, 'clean_companies.csv')
    print(f"  Loading companies ...")
    df = pd.read_csv(path, dtype=str)
    df.to_sql('companies', conn, if_exists='append', index=False)
    conn.commit()
    print(f"  Done: {len(df):,} rows into [companies]")


def load_relationship(conn, filename, table, valid_patents):
    path = os.path.join(CLEAN_DIR, filename)
    print(f"  Loading {filename} -> [{table}] (filtered to {YEAR_FROM}–{YEAR_TO} patents) ...")
    total = 0
    for chunk in pd.read_csv(path, dtype=str, chunksize=50_000):
        chunk = chunk[chunk['patent_id'].isin(valid_patents)]
        if len(chunk) == 0:
            continue
        chunk.to_sql(table, conn, if_exists='append', index=False)
        total += len(chunk)
        print(f"    {total:,} rows loaded ...", end='\r')
    conn.commit()
    print(f"  Done: {total:,} rows into [{table}]          ")


def load_term_of_grant(conn, valid_patents):
    path = os.path.join(CLEAN_DIR, 'clean_term_of_grant.csv')
    print(f"  Loading term_of_grant (filtered to {YEAR_FROM}–{YEAR_TO} patents) ...")
    total = 0
    for chunk in pd.read_csv(path, dtype=str, chunksize=50_000):
        chunk = chunk[chunk['patent_id'].isin(valid_patents)]
        if len(chunk) == 0:
            continue
        chunk.to_sql('term_of_grant', conn, if_exists='append', index=False)
        total += len(chunk)
        print(f"    {total:,} rows loaded ...", end='\r')
    conn.commit()
    print(f"  Done: {total:,} rows into [term_of_grant]          ")


def main():
    print("=" * 55)
    print("  Patent Database Loader  —  2006 to 2025")
    print("=" * 55)
    print(f"  Database: {os.path.abspath(DB_PATH)}\n")

    conn = get_conn()
    apply_schema(conn)

    # Load patents first and get the valid patent IDs
    load_patents(conn)
    print("  Reading valid patent IDs for filtering ...")
    valid_patents = set(pd.read_sql("SELECT patent_id FROM patents", conn)['patent_id'])
    print(f"  {len(valid_patents):,} valid patent IDs loaded into memory.\n")

    load_inventors(conn)
    load_companies(conn)
    load_relationship(conn, 'clean_patent_inventor.csv', 'patent_inventor', valid_patents)
    load_relationship(conn, 'clean_patent_assignee.csv', 'patent_assignee', valid_patents)
    load_term_of_grant(conn, valid_patents)

    # Summary
    print("\n  Summary:")
    for t in ['patents','inventors','companies',
              'patent_inventor','patent_assignee','term_of_grant']:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"    {t:<25} {count:>10,} rows")

    conn.close()
    print(f"\n  Database ready — {YEAR_FROM} to {YEAR_TO}.")
    print("  Next step: python scripts/report.py")


if __name__ == "__main__":
    main()
