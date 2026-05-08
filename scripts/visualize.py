# ============================================================
# visualize.py  —  Extra Marks: Data Visualizations
# Generates charts from the database and saves to reports/
# ============================================================

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DB_PATH     = os.path.join(os.path.dirname(__file__), '..', 'database', 'patents.db')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

BLUE   = '#2563EB'
GREEN  = '#16A34A'
PURPLE = '#7C3AED'
ORANGE = '#EA580C'
COLORS = [BLUE, GREEN, PURPLE, ORANGE,
          '#0891B2','#DC2626','#D97706','#059669','#7C3AED','#BE185D']


def get_conn():
    return sqlite3.connect(DB_PATH)


def q(conn, sql):
    return pd.read_sql_query(sql, conn)


# ── Chart 1: Top 10 Inventors ────────────────────────────
def chart_top_inventors(conn):
    df = q(conn, """
        SELECT i.name, COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
        GROUP BY i.inventor_id ORDER BY patents DESC LIMIT 10
    """)
    df = df.sort_values('patents')

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df['name'], df['patents'], color=BLUE, edgecolor='white')
    ax.bar_label(bars, fmt='%,.0f', padding=4, fontsize=9)
    ax.set_xlabel('Number of Patents')
    ax.set_title('Top 10 Inventors by Patent Count', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    out = os.path.join(REPORTS_DIR, 'chart_top_inventors.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


# ── Chart 2: Top 10 Companies ────────────────────────────
def chart_top_companies(conn):
    df = q(conn, """
        SELECT c.name, COUNT(DISTINCT pa.patent_id) AS patents
        FROM companies c
        JOIN patent_assignee pa ON c.company_id = pa.company_id
        GROUP BY c.company_id ORDER BY patents DESC LIMIT 10
    """)
    df = df.sort_values('patents')
    # Shorten long names
    df['name'] = df['name'].str.slice(0, 35)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df['name'], df['patents'], color=GREEN, edgecolor='white')
    ax.bar_label(bars, fmt='%,.0f', padding=4, fontsize=9)
    ax.set_xlabel('Number of Patents')
    ax.set_title('Top 10 Companies by Patent Count', fontsize=14, fontweight='bold', pad=15)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    out = os.path.join(REPORTS_DIR, 'chart_top_companies.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


# ── Chart 3: Patents Per Year ────────────────────────────
def chart_yearly_trends(conn):
    df = q(conn, """
        SELECT year, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    df['year'] = df['year'].astype(int)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.fill_between(df['year'], df['patents'], alpha=0.2, color=PURPLE)
    ax.plot(df['year'], df['patents'], color=PURPLE, linewidth=2.5, marker='o', markersize=4)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Patents')
    ax.set_title('Patents Granted Per Year', fontsize=14, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    out = os.path.join(REPORTS_DIR, 'chart_yearly_trends.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


# ── Chart 4: Term Extension Distribution ─────────────────
def chart_term_extension(conn):
    df = q(conn, """
        SELECT CAST(term_extension AS INTEGER) AS days
        FROM term_of_grant
        WHERE term_extension IS NOT NULL
        AND term_extension != ''
        AND CAST(term_extension AS INTEGER) > 0
        AND CAST(term_extension AS INTEGER) < 2000
    """)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(df['days'], bins=50, color=ORANGE, edgecolor='white', linewidth=0.5)
    ax.set_xlabel('Extension Days')
    ax.set_ylabel('Number of Patents')
    ax.set_title('Distribution of Patent Term Extensions', fontsize=14, fontweight='bold', pad=15)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()
    out = os.path.join(REPORTS_DIR, 'chart_term_extension.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


# ── Chart 5: Top 10 Companies — Pie Chart ────────────────
def chart_companies_pie(conn):
    df = q(conn, """
        SELECT c.name, COUNT(DISTINCT pa.patent_id) AS patents
        FROM companies c
        JOIN patent_assignee pa ON c.company_id = pa.company_id
        GROUP BY c.company_id ORDER BY patents DESC LIMIT 10
    """)
    df['name'] = df['name'].str.slice(0, 25)

    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, autotexts = ax.pie(
        df['patents'], labels=df['name'], autopct='%1.1f%%',
        colors=COLORS, startangle=140,
        pctdistance=0.82, textprops={'fontsize': 8}
    )
    for at in autotexts:
        at.set_fontsize(7)
    ax.set_title('Top 10 Companies — Share of Patents', fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    out = os.path.join(REPORTS_DIR, 'chart_companies_pie.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out}")


def main():
    print("=" * 55)
    print("  Patent Intelligence — Visualizations")
    print("=" * 55)

    conn = get_conn()

    chart_top_inventors(conn)
    chart_top_companies(conn)
    chart_yearly_trends(conn)
    chart_term_extension(conn)
    chart_companies_pie(conn)

    conn.close()

    print("\n  All charts saved to reports/")
    print("  Files:")
    for f in sorted(os.listdir(REPORTS_DIR)):
        if f.endswith('.png'):
            size = os.path.getsize(os.path.join(REPORTS_DIR, f)) / 1024
            print(f"    {f}  ({size:.0f} KB)")


if __name__ == "__main__":
    main()