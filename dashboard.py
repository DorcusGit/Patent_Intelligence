# ============================================================
# dashboard.py  —  Streamlit Dashboard
# Run with: streamlit run scripts/dashboard.py
# ============================================================

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="🔬",
    layout="wide"
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'patents.db')

COLORS = ['#2563EB','#16A34A','#7C3AED','#EA580C',
          '#0891B2','#DC2626','#D97706','#059669','#BE185D','#1D4ED8']


# ── DB helper ─────────────────────────────────────────────
@st.cache_data
def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


# ── Header ────────────────────────────────────────────────
st.title("🔬 Global Patent Intelligence Dashboard")
st.markdown("**Data Source:** USPTO PatentsView — Granted Patents 2006–2025")
st.divider()


# ── KPI Row ───────────────────────────────────────────────
total_patents   = run_query("SELECT COUNT(*) AS n FROM patents").iloc[0]['n']
total_inventors = run_query("SELECT COUNT(*) AS n FROM inventors").iloc[0]['n']
total_companies = run_query("SELECT COUNT(*) AS n FROM companies").iloc[0]['n']
total_relations = run_query("SELECT COUNT(*) AS n FROM patent_inventor").iloc[0]['n']

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patents",    f"{int(total_patents):,}")
col2.metric("Total Inventors",  f"{int(total_inventors):,}")
col3.metric("Total Companies",  f"{int(total_companies):,}")
col4.metric("Patent-Inventor Links", f"{int(total_relations):,}")

st.divider()


# ── Sidebar filters ───────────────────────────────────────
st.sidebar.title("🔧 Filters")
year_data = run_query("SELECT DISTINCT CAST(year AS INTEGER) AS year FROM patents WHERE year IS NOT NULL ORDER BY year")
years = sorted(year_data['year'].dropna().astype(int).tolist())

if years:
    year_min, year_max = st.sidebar.slider(
        "Year Range", min_value=min(years), max_value=max(years),
        value=(min(years), max(years))
    )
else:
    year_min, year_max = 2006, 2025

top_n = st.sidebar.slider("Top N results", min_value=5, max_value=20, value=10)

st.sidebar.divider()
st.sidebar.markdown("**About**")
st.sidebar.markdown("Built with Python, SQLite, pandas, and Streamlit.")


# ── Tab layout ────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends", "👤 Inventors", "🏢 Companies", "🔗 SQL Queries", "📋 Data Table"
])


# ══════════════════════════════════════════════════════════
# TAB 1 — TRENDS
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Patents Granted Per Year")

    yearly = run_query(f"""
        SELECT CAST(year AS INTEGER) AS year, COUNT(*) AS patents
        FROM patents
        WHERE year IS NOT NULL
          AND CAST(year AS INTEGER) BETWEEN {year_min} AND {year_max}
        GROUP BY year ORDER BY year
    """)

    if not yearly.empty:
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.fill_between(yearly['year'], yearly['patents'], alpha=0.15, color='#2563EB')
        ax.plot(yearly['year'], yearly['patents'], color='#2563EB', linewidth=2.5,
                marker='o', markersize=5)
        ax.set_xlabel("Year")
        ax.set_ylabel("Patents")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.markdown("#### Year-by-Year Breakdown")
        yearly['year'] = yearly['year'].astype(int)
        yearly['patents'] = yearly['patents'].apply(lambda x: f"{x:,}")
        st.dataframe(yearly, use_container_width=True, hide_index=True)
    else:
        st.warning("No data for selected year range.")

    st.divider()
    st.subheader("Patent Types")
    types = run_query(f"""
        SELECT patent_type, COUNT(*) AS patents
        FROM patents
        WHERE CAST(year AS INTEGER) BETWEEN {year_min} AND {year_max}
          AND patent_type IS NOT NULL
        GROUP BY patent_type ORDER BY patents DESC
    """)
    if not types.empty:
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.barh(types['patent_type'], types['patents'], color=COLORS[:len(types)])
        ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax2.spines[['top','right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()


# ══════════════════════════════════════════════════════════
# TAB 2 — INVENTORS
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader(f"Top {top_n} Inventors by Patent Count")

    inventors = run_query(f"""
        SELECT i.name, COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
        JOIN patents p ON pi.patent_id = p.patent_id
        WHERE CAST(p.year AS INTEGER) BETWEEN {year_min} AND {year_max}
        GROUP BY i.inventor_id
        ORDER BY patents DESC
        LIMIT {top_n}
    """)

    if not inventors.empty:
        col_a, col_b = st.columns([3, 2])
        with col_a:
            fig, ax = plt.subplots(figsize=(8, 5))
            df_plot = inventors.sort_values('patents')
            bars = ax.barh(df_plot['name'], df_plot['patents'], color='#2563EB')
            ax.bar_label(bars, fmt='%,.0f', padding=3, fontsize=8)
            ax.set_xlabel("Patents")
            ax.spines[['top','right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col_b:
            st.markdown("#### Rankings")
            inventors.index = range(1, len(inventors) + 1)
            inventors.index.name = "Rank"
            inventors['patents'] = inventors['patents'].apply(lambda x: f"{x:,}")
            st.dataframe(inventors, use_container_width=True)


# ══════════════════════════════════════════════════════════
# TAB 3 — COMPANIES
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader(f"Top {top_n} Companies by Patent Count")

    companies = run_query(f"""
        SELECT c.name, c.assignee_type, COUNT(DISTINCT pa.patent_id) AS patents
        FROM companies c
        JOIN patent_assignee pa ON c.company_id = pa.company_id
        JOIN patents p ON pa.patent_id = p.patent_id
        WHERE CAST(p.year AS INTEGER) BETWEEN {year_min} AND {year_max}
        GROUP BY c.company_id
        ORDER BY patents DESC
        LIMIT {top_n}
    """)

    if not companies.empty:
        col_a, col_b = st.columns([3, 2])
        with col_a:
            fig, ax = plt.subplots(figsize=(8, 5))
            df_plot = companies.sort_values('patents')
            df_plot['short_name'] = df_plot['name'].str.slice(0, 30)
            bars = ax.barh(df_plot['short_name'], df_plot['patents'], color='#16A34A')
            ax.bar_label(bars, fmt='%,.0f', padding=3, fontsize=8)
            ax.set_xlabel("Patents")
            ax.spines[['top','right']].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with col_b:
            st.markdown("#### Rankings")
            companies.index = range(1, len(companies) + 1)
            companies.index.name = "Rank"
            companies['patents'] = companies['patents'].apply(lambda x: f"{x:,}")
            st.dataframe(companies[['name','patents']], use_container_width=True)

        st.divider()
        st.subheader("Company Share — Pie Chart")
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        companies_raw = run_query(f"""
            SELECT c.name, COUNT(DISTINCT pa.patent_id) AS patents
            FROM companies c
            JOIN patent_assignee pa ON c.company_id = pa.company_id
            JOIN patents p ON pa.patent_id = p.patent_id
            WHERE CAST(p.year AS INTEGER) BETWEEN {year_min} AND {year_max}
            GROUP BY c.company_id ORDER BY patents DESC LIMIT {top_n}
        """)
        companies_raw['short'] = companies_raw['name'].str.slice(0, 20)
        ax2.pie(companies_raw['patents'], labels=companies_raw['short'],
                autopct='%1.1f%%', colors=COLORS[:len(companies_raw)],
                startangle=140, textprops={'fontsize': 8})
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()


# ══════════════════════════════════════════════════════════
# TAB 4 — SQL QUERIES
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("All 7 SQL Queries with Live Results")

    queries = {
        "Q1: Top Inventors": f"""
            SELECT i.name, COUNT(DISTINCT pi.patent_id) AS patent_count
            FROM inventors i
            JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
            GROUP BY i.inventor_id ORDER BY patent_count DESC LIMIT 10
        """,
        "Q2: Top Companies": f"""
            SELECT c.name, COUNT(DISTINCT pa.patent_id) AS patent_count
            FROM companies c
            JOIN patent_assignee pa ON c.company_id = pa.company_id
            GROUP BY c.company_id ORDER BY patent_count DESC LIMIT 10
        """,
        "Q3: Patent Types": """
            SELECT patent_type, COUNT(*) AS patent_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM patents), 2) AS share_pct
            FROM patents WHERE patent_type IS NOT NULL
            GROUP BY patent_type ORDER BY patent_count DESC
        """,
        "Q4: Trends Over Time": """
            SELECT year, COUNT(*) AS patent_count
            FROM patents WHERE year IS NOT NULL
            GROUP BY year ORDER BY year
        """,
        "Q5: JOIN — Patents + Inventors + Companies": """
            SELECT p.patent_id, p.title, p.year, i.name AS inventor,
                   c.name AS company
            FROM patents p
            JOIN patent_inventor pi ON p.patent_id = pi.patent_id
            JOIN inventors i ON pi.inventor_id = i.inventor_id
            LEFT JOIN patent_assignee pa ON p.patent_id = pa.patent_id
            LEFT JOIN companies c ON pa.company_id = c.company_id
            LIMIT 20
        """,
        "Q6: CTE — Top Inventors per Patent Type": """
            WITH inventor_counts AS (
                SELECT i.inventor_id, i.name, p.patent_type,
                       COUNT(DISTINCT pi.patent_id) AS patent_count
                FROM inventors i
                JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
                JOIN patents p ON pi.patent_id = p.patent_id
                GROUP BY i.inventor_id, p.patent_type
            ),
            type_totals AS (
                SELECT patent_type, SUM(patent_count) AS type_total
                FROM inventor_counts GROUP BY patent_type
            )
            SELECT ic.patent_type, ic.name, ic.patent_count,
                   ROUND(100.0 * ic.patent_count / tt.type_total, 3) AS pct_of_type
            FROM inventor_counts ic
            JOIN type_totals tt ON ic.patent_type = tt.patent_type
            ORDER BY ic.patent_count DESC LIMIT 20
        """,
        "Q7: Ranking — Window Functions": """
            SELECT name, patent_type, patent_count,
                   RANK() OVER (ORDER BY patent_count DESC) AS global_rank,
                   RANK() OVER (PARTITION BY patent_type ORDER BY patent_count DESC) AS rank_in_type,
                   ROUND(100.0 * patent_count / SUM(patent_count) OVER (), 4) AS global_share_pct
            FROM (
                SELECT i.inventor_id, i.name, p.patent_type,
                       COUNT(DISTINCT pi.patent_id) AS patent_count
                FROM inventors i
                JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
                JOIN patents p ON pi.patent_id = p.patent_id
                GROUP BY i.inventor_id, p.patent_type
            ) sub
            ORDER BY global_rank LIMIT 20
        """,
    }

    for title, sql in queries.items():
        with st.expander(f"**{title}**", expanded=False):
            st.code(sql.strip(), language='sql')
            try:
                result = run_query(sql)
                st.dataframe(result, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Query error: {e}")


# ══════════════════════════════════════════════════════════
# TAB 5 — DATA TABLE
# ══════════════════════════════════════════════════════════
with tab5:
    st.subheader("Browse Patent Records")

    search = st.text_input("Search by patent title (optional):")

    where = f"WHERE CAST(year AS INTEGER) BETWEEN {year_min} AND {year_max}"
    if search:
        where += f" AND LOWER(title) LIKE LOWER('%{search}%')"

    sample = run_query(f"""
        SELECT patent_id, patent_type, title, filing_date, year
        FROM patents {where}
        ORDER BY year DESC
        LIMIT 500
    """)

    st.markdown(f"Showing **{len(sample):,}** records (max 500)")
    st.dataframe(sample, use_container_width=True, hide_index=True)