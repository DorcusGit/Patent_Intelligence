-- ============================================================
-- schema.sql  —  Patent Intelligence Database
-- ============================================================

DROP TABLE IF EXISTS patent_assignee;
DROP TABLE IF EXISTS patent_inventor;
DROP TABLE IF EXISTS term_of_grant;
DROP TABLE IF EXISTS inventors;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS patents;

CREATE TABLE patents (
    patent_id   TEXT PRIMARY KEY,
    patent_type TEXT,
    title       TEXT,
    filing_date TEXT,
    year        INTEGER
);

CREATE TABLE inventors (
    inventor_id TEXT PRIMARY KEY,
    name        TEXT,
    location_id TEXT
);

CREATE TABLE companies (
    company_id    TEXT PRIMARY KEY,
    name          TEXT,
    assignee_type TEXT
);

CREATE TABLE patent_inventor (
    patent_id   TEXT,
    inventor_id TEXT,
    FOREIGN KEY (patent_id)   REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id)
);

CREATE TABLE patent_assignee (
    patent_id  TEXT,
    company_id TEXT,
    FOREIGN KEY (patent_id)  REFERENCES patents(patent_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

CREATE TABLE term_of_grant (
    patent_id      TEXT PRIMARY KEY,
    term_grant     TEXT,
    term_extension TEXT,
    has_disclaimer TEXT,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id)
);
