import os
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
 
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'outputs')
 
COLORS = ['#2563EB','#16A34A','#7C3AED','#EA580C',
          '#0891B2','#DC2626','#D97706','#059669','#BE185D','#1D4ED8']
 
 
# ── Load CSVs ─────────────────────────────────────────────
@st.cache_data
def load_data():
    def read(filename):
        path = os.path.join(REPORTS_DIR, filename)
        if os.path.exists(path):
            return pd.read_csv(path)
        return pd.DataFrame()
 
    return {
        "inventors":  read("top_inventors.csv"),
        "companies":  read("top_companies.csv"),
        "yearly":     read("yearly_trends.csv"),
        "types":      read("patent_types.csv"),
    }
 
data = load_data()
 
 
# ── Header ────────────────────────────────────────────────
st.title("🔬 Global Patent Intelligence Dashboard")
st.markdown("**Data Source:** USPTO PatentsView — Granted Patents 2006–2025")
st.divider()
 
 
# ── KPI Row ───────────────────────────────────────────────
yearly = data["inventors"]
total_patents = data["yearly"]["patents"].sum() if not data["yearly"].empty else 0
total_inventors = len(data["inventors"]) if not data["inventors"].empty else 0
total_companies = len(data["companies"]) if not data["companies"].empty else 0
year_range = f"{int(data['yearly']['year'].min())}–{int(data['yearly']['year'].max())}" \
    if not data["yearly"].empty else "N/A"
 
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Patents (in outputs)", f"{int(total_patents):,}")
col2.metric("Top Inventors Tracked",      f"{total_inventors}")
col3.metric("Top Companies Tracked",      f"{total_companies}")
col4.metric("Year Range",                 year_range)
 
st.divider()
 
 
# ── Sidebar ───────────────────────────────────────────────
st.sidebar.title("🔧 Filters")
top_n = st.sidebar.slider("Top N results", min_value=5, max_value=20, value=10)
 
if not data["yearly"].empty:
    years = sorted(data["yearly"]["year"].dropna().astype(int).tolist())
    year_min, year_max = st.sidebar.slider(
        "Year Range", min_value=min(years), max_value=max(years),
        value=(min(years), max(years))
    )
else:
    year_min, year_max = 2006, 2025
 
st.sidebar.divider()
st.sidebar.markdown("**About**")
st.sidebar.markdown("Built with Python, SQLite, pandas, and Streamlit.")
st.sidebar.markdown("Data from USPTO PatentsView.")
 
 
# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Trends", "👤 Inventors", "🏢 Companies", "📋 Raw Data"
])
 
 
# ══════════════════════════════════════════════════════════
# TAB 1 — TRENDS
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Patents Granted Per Year (2006–2025)")
 
    if not data["yearly"].empty:
        df = data["yearly"].copy()
        df["year"] = df["year"].astype(int)
        df = df[(df["year"] >= year_min) & (df["year"] <= year_max)]
 
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.fill_between(df["year"], df["patents"], alpha=0.15, color="#2563EB")
        ax.plot(df["year"], df["patents"], color="#2563EB",
                linewidth=2.5, marker="o", markersize=5)
        ax.set_xlabel("Year")
        ax.set_ylabel("Patents Granted")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
 
        # Stats row
        c1, c2, c3 = st.columns(3)
        c1.metric("Peak Year",
                  str(int(df.loc[df["patents"].idxmax(), "year"])),
                  f"{int(df['patents'].max()):,} patents")
        c2.metric("Lowest Year",
                  str(int(df.loc[df["patents"].idxmin(), "year"])),
                  f"{int(df['patents'].min()):,} patents")
        growth = int(df.iloc[-1]["patents"]) - int(df.iloc[0]["patents"])
        c3.metric("Growth (first vs last year)", f"{growth:+,} patents")
 
        st.divider()
        st.subheader("Year-by-Year Breakdown")
        df_show = df.copy()
        df_show["patents"] = df_show["patents"].apply(lambda x: f"{int(x):,}")
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.warning("yearly_trends.csv not found in outputs/. Run report.py first and ensure files are in outputs/ folder.")
 
    # Patent types
    if not data["types"].empty:
        st.divider()
        st.subheader("Patents by Type")
        fig2, ax2 = plt.subplots(figsize=(7, 3))
        df_t = data["types"]
        ax2.barh(df_t["patent_type"], df_t["patents"], color=COLORS[:len(df_t)])
        ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax2.spines[["top","right"]].set_visible(False)
        ax2.set_xlabel("Patents")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
 
 
# ══════════════════════════════════════════════════════════
# TAB 2 — INVENTORS
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader(f"Top {top_n} Inventors by Patent Count")
 
    if not data["inventors"].empty:
        df = data["inventors"].head(top_n).copy()
 
        col_a, col_b = st.columns([3, 2])
        with col_a:
            df_plot = df.sort_values("patents")
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.barh(df_plot["name"], df_plot["patents"], color="#2563EB")
            ax.bar_label(bars, fmt="%,.0f", padding=3, fontsize=8)
            ax.set_xlabel("Patents")
            ax.spines[["top","right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
 
        with col_b:
            st.markdown("#### Rankings")
            df_show = df[["name","patents"]].copy()
            df_show.index = range(1, len(df_show) + 1)
            df_show.index.name = "Rank"
            df_show["patents"] = df_show["patents"].apply(lambda x: f"{int(x):,}")
            st.dataframe(df_show, use_container_width=True)
 
        st.divider()
        st.subheader("Inventor Share — Pie Chart")
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        df["short"] = df["name"].str.split().str[-1]  # last name only for pie
        ax2.pie(df["patents"], labels=df["short"], autopct="%1.1f%%",
                colors=COLORS[:len(df)], startangle=140,
                textprops={"fontsize": 8})
        ax2.set_title(f"Top {top_n} Inventors — Patent Share")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
    else:
        st.warning("top_inventors.csv not found in outputs/. Run report.py first and ensure files are in outputs/ folder.")
 
 
# ══════════════════════════════════════════════════════════
# TAB 3 — COMPANIES
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader(f"Top {top_n} Companies by Patent Count")
 
    if not data["companies"].empty:
        df = data["companies"].head(top_n).copy()
 
        col_a, col_b = st.columns([3, 2])
        with col_a:
            df_plot = df.sort_values("patents")
            df_plot["short_name"] = df_plot["name"].str.slice(0, 30)
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.barh(df_plot["short_name"], df_plot["patents"], color="#16A34A")
            ax.bar_label(bars, fmt="%,.0f", padding=3, fontsize=8)
            ax.set_xlabel("Patents")
            ax.spines[["top","right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
 
        with col_b:
            st.markdown("#### Rankings")
            df_show = df[["name","patents"]].copy()
            df_show.index = range(1, len(df_show) + 1)
            df_show.index.name = "Rank"
            df_show["patents"] = df_show["patents"].apply(lambda x: f"{int(x):,}")
            st.dataframe(df_show, use_container_width=True)
 
        st.divider()
        st.subheader("Company Share — Pie Chart")
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        df["short"] = df["name"].str.slice(0, 20)
        ax2.pie(df["patents"], labels=df["short"], autopct="%1.1f%%",
                colors=COLORS[:len(df)], startangle=140,
                textprops={"fontsize": 8})
        ax2.set_title(f"Top {top_n} Companies — Patent Share")
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
    else:
        st.warning("top_companies.csv not found in outputs/. Run report.py first and ensure files are in outputs/ folder.")
 
 
# ══════════════════════════════════════════════════════════
# TAB 4 — RAW DATA
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("Raw Report Data")
 
    sections = {
        "Top Inventors":    data["inventors"],
        "Top Companies":    data["companies"],
        "Yearly Trends":    data["yearly"],
        "Patent Types":     data["types"],
    }
 
    for title, df in sections.items():
        if not df.empty:
            with st.expander(f"**{title}** ({len(df)} rows)"):
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"{title} — no data found.")