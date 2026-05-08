# ============================================================
# report.py  —  Phase 5
# Runs SQL queries and generates console, CSV, and JSON reports
# ============================================================

import os
import json
import sqlite3
import pandas as pd

DB_PATH     = os.path.join(os.path.dirname(__file__), '..', 'database', 'patents.db')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


def get_conn():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}\nRun load_db.py first.")
    return sqlite3.connect(DB_PATH)


def q(conn, sql):
    return pd.read_sql_query(sql, conn)


def main():
    conn = get_conn()

    # ── Run all queries ───────────────────────────────────
    print("  Running queries ...")

    total_patents = q(conn, "SELECT COUNT(*) AS n FROM patents").iloc[0]['n']
    total_inventors = q(conn, "SELECT COUNT(*) AS n FROM inventors").iloc[0]['n']
    total_companies = q(conn, "SELECT COUNT(*) AS n FROM companies").iloc[0]['n']

    top_inventors = q(conn, """
        SELECT i.name, COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
        GROUP BY i.inventor_id ORDER BY patents DESC LIMIT 10
    """)

    top_companies = q(conn, """
        SELECT c.name, c.assignee_type, COUNT(DISTINCT pa.patent_id) AS patents
        FROM companies c
        JOIN patent_assignee pa ON c.company_id = pa.company_id
        GROUP BY c.company_id ORDER BY patents DESC LIMIT 10
    """)

    patent_types = q(conn, """
        SELECT patent_type, COUNT(*) AS patents
        FROM patents WHERE patent_type IS NOT NULL
        GROUP BY patent_type ORDER BY patents DESC
    """)

    yearly = q(conn, """
        SELECT year, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)

    term_stats = q(conn, """
        SELECT
            ROUND(AVG(CAST(term_extension AS REAL)), 1) AS avg_extension_days,
            COUNT(CASE WHEN has_disclaimer = '1' THEN 1 END) AS disclaimer_count,
            COUNT(*) AS total
        FROM term_of_grant
    """)

    conn.close()

    # ── Console Report ────────────────────────────────────
    print()
    print("=" * 55)
    print("       PATENT INTELLIGENCE REPORT")
    print("=" * 55)
    print(f"  Total Patents  : {int(total_patents):,}")
    print(f"  Total Inventors: {int(total_inventors):,}")
    print(f"  Total Companies: {int(total_companies):,}")

    print("\n  Patent Types:")
    for _, row in patent_types.iterrows():
        print(f"    {row['patent_type']:20s} {int(row['patents']):>10,}")

    print("\n  Top 10 Inventors:")
    for i, row in top_inventors.iterrows():
        print(f"    {i+1:>2}. {str(row['name']):<35} {int(row['patents']):>6,} patents")

    print("\n  Top 10 Companies:")
    for i, row in top_companies.iterrows():
        print(f"    {i+1:>2}. {str(row['name']):<35} {int(row['patents']):>6,} patents")

    print("\n  Patents per Year (last 10 years):")
    recent = yearly.tail(10)
    max_count = int(recent['patents'].max()) if len(recent) > 0 else 1
    for _, row in recent.iterrows():
        bar_len = int(int(row['patents']) / max_count * 35)
        bar = '█' * bar_len
        print(f"    {int(row['year'])}  {bar:<35} {int(row['patents']):,}")

    if len(term_stats) > 0:
        row = term_stats.iloc[0]
        print(f"\n  Term of Grant Stats:")
        print(f"    Avg extension  : {row['avg_extension_days']} days")
        print(f"    Disclaimers    : {int(row['disclaimer_count']):,}")

    print("=" * 55)

    # ── CSV Exports ───────────────────────────────────────
    paths = {
        'top_inventors.csv':  top_inventors,
        'top_companies.csv':  top_companies,
        'patent_types.csv':   patent_types,
        'yearly_trends.csv':  yearly,
    }
    print()
    for fname, df in paths.items():
        out = os.path.join(REPORTS_DIR, fname)
        df.to_csv(out, index=False)
        print(f"  Saved: {out}")

    # ── JSON Report ───────────────────────────────────────
    report = {
        "summary": {
            "total_patents":   int(total_patents),
            "total_inventors": int(total_inventors),
            "total_companies": int(total_companies),
        },
        "top_inventors": [
            {"rank": i+1, "name": str(r['name']), "patents": int(r['patents'])}
            for i, r in top_inventors.iterrows()
        ],
        "top_companies": [
            {"rank": i+1, "name": str(r['name']),
             "type": str(r['assignee_type']), "patents": int(r['patents'])}
            for i, r in top_companies.iterrows()
        ],
        "patent_types": [
            {"type": str(r['patent_type']), "patents": int(r['patents'])}
            for _, r in patent_types.iterrows()
        ],
        "yearly_trends": [
            {"year": int(r['year']), "patents": int(r['patents'])}
            for _, r in yearly.iterrows()
        ],
    }

    json_out = os.path.join(REPORTS_DIR, 'report.json')
    with open(json_out, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Saved: {json_out}")

    print("\n  All reports generated successfully.")
    print("  Check the reports/ folder for your output files.")


if __name__ == "__main__":
    main()
