# ============================================================
# clean_data.py  —  Phase 3
# Reads raw TSV files and produces clean CSVs using pandas
# Columns confirmed from inspect_columns.py output
# ============================================================

import os
import pandas as pd

RAW_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
CLEAN_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'clean')
os.makedirs(CLEAN_DIR, exist_ok=True)


def read_tsv(filename, usecols=None):
    """Read a TSV file (plain or zip) from data/raw/."""
    for name in [filename, filename + '.zip']:
        path = os.path.join(RAW_DIR, name)
        if os.path.exists(path):
            print(f"  Reading: {name}")
            return pd.read_csv(
                path, sep='\t', dtype=str,
                usecols=usecols, low_memory=False
            )
    raise FileNotFoundError(
        f"Could not find {filename} or {filename}.zip in {RAW_DIR}"
    )


def clean_patents():
    print("\n[1/4] Cleaning patents ...")
    df = read_tsv('g_patent.tsv', usecols=[
        'patent_id', 'patent_type', 'patent_date', 'patent_title'
    ])
    df.rename(columns={'patent_date': 'filing_date', 'patent_title': 'title'}, inplace=True)
    df['year'] = pd.to_datetime(df['filing_date'], errors='coerce').dt.year.astype('Int64')
    df.dropna(subset=['patent_id'], inplace=True)
    df.drop_duplicates(subset=['patent_id'], inplace=True)
    df['title'] = df['title'].fillna('Unknown')
    df['filing_date'] = df['filing_date'].fillna('')
    df = df[['patent_id', 'patent_type', 'title', 'filing_date', 'year']]
    out = os.path.join(CLEAN_DIR, 'clean_patents.csv')
    df.to_csv(out, index=False)
    print(f"  Done: {len(df):,} patents -> {out}")


def clean_inventors():
    print("\n[2/4] Cleaning inventors ...")
    df = read_tsv('g_inventor_disambiguated.tsv', usecols=[
        'patent_id', 'inventor_id',
        'disambig_inventor_name_first',
        'disambig_inventor_name_last',
        'location_id'
    ])
    first = df['disambig_inventor_name_first'].fillna('')
    last  = df['disambig_inventor_name_last'].fillna('')
    df['name'] = (first + ' ' + last).str.strip()
    df['name'].replace('', 'Unknown', inplace=True)
    df.dropna(subset=['inventor_id'], inplace=True)
    df.drop_duplicates(subset=['inventor_id', 'patent_id'], inplace=True)

    inventors = df[['inventor_id', 'name', 'location_id']].drop_duplicates(subset=['inventor_id']).copy()
    links     = df[['patent_id', 'inventor_id']].drop_duplicates()

    inventors.to_csv(os.path.join(CLEAN_DIR, 'clean_inventors.csv'), index=False)
    links.to_csv(os.path.join(CLEAN_DIR, 'clean_patent_inventor.csv'), index=False)
    print(f"  Done: {len(inventors):,} inventors, {len(links):,} links")


def clean_companies():
    print("\n[3/4] Cleaning companies ...")
    df = read_tsv('g_assignee_disambiguated.tsv', usecols=[
        'patent_id', 'assignee_id',
        'disambig_assignee_organization',
        'disambig_assignee_individual_name_first',
        'disambig_assignee_individual_name_last',
        'assignee_type'
    ])
    org        = df['disambig_assignee_organization'].fillna('')
    first      = df['disambig_assignee_individual_name_first'].fillna('')
    last       = df['disambig_assignee_individual_name_last'].fillna('')
    individual = (first + ' ' + last).str.strip()
    df['name'] = org.where(org != '', individual)
    df['name'].replace('', 'Unknown', inplace=True)
    df.dropna(subset=['assignee_id'], inplace=True)
    df.drop_duplicates(subset=['assignee_id', 'patent_id'], inplace=True)

    companies = df[['assignee_id', 'name', 'assignee_type']].drop_duplicates(subset=['assignee_id']).copy()
    companies.rename(columns={'assignee_id': 'company_id'}, inplace=True)
    links = df[['patent_id', 'assignee_id']].drop_duplicates()
    links = links.rename(columns={'assignee_id': 'company_id'})

    companies.to_csv(os.path.join(CLEAN_DIR, 'clean_companies.csv'), index=False)
    links.to_csv(os.path.join(CLEAN_DIR, 'clean_patent_assignee.csv'), index=False)
    print(f"  Done: {len(companies):,} companies, {len(links):,} links")


def clean_term_of_grant():
    print("\n[4/4] Cleaning term of grant ...")
    df = read_tsv('g_us_term_of_grant.tsv', usecols=[
        'patent_id', 'term_grant', 'term_extension', 'term_disclaimer'
    ])
    df.dropna(subset=['patent_id'], inplace=True)
    df.drop_duplicates(subset=['patent_id'], inplace=True)
    df['term_grant']     = pd.to_numeric(df['term_grant'],     errors='coerce')
    df['term_extension'] = pd.to_numeric(df['term_extension'], errors='coerce')
    df['has_disclaimer'] = df['term_disclaimer'].notna() & (df['term_disclaimer'] != '')
    df = df[['patent_id', 'term_grant', 'term_extension', 'has_disclaimer']]
    out = os.path.join(CLEAN_DIR, 'clean_term_of_grant.csv')
    df.to_csv(out, index=False)
    print(f"  Done: {len(df):,} rows -> {out}")


def main():
    print("=" * 60)
    print("  Patent Data Cleaner")
    print("=" * 60)
    print(f"  Reading from : {os.path.abspath(RAW_DIR)}")
    print(f"  Writing to   : {os.path.abspath(CLEAN_DIR)}")

    clean_patents()
    clean_inventors()
    clean_companies()
    clean_term_of_grant()

    print("\n" + "=" * 60)
    print("  All cleaning complete!")
    print("  Files in data/clean/:")
    for f in sorted(os.listdir(CLEAN_DIR)):
        size = os.path.getsize(os.path.join(CLEAN_DIR, f)) / (1024 * 1024)
        print(f"    {f}  ({size:.1f} MB)")
    print("\n  Next step: python scripts/load_db.py")
    print("=" * 60)


if __name__ == "__main__":
    main()