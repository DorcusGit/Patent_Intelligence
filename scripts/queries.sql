-- ============================================================
-- queries.sql  —  All 7 Required SQL Queries
-- ============================================================


-- Q1: Top Inventors — who has the most patents?
SELECT
    i.name,
    COUNT(DISTINCT pi.patent_id) AS patent_count
FROM inventors i
JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
GROUP BY i.inventor_id
ORDER BY patent_count DESC
LIMIT 20;


-- Q2: Top Companies — which companies own the most patents?
SELECT
    c.name,
    c.assignee_type,
    COUNT(DISTINCT pa.patent_id) AS patent_count
FROM companies c
JOIN patent_assignee pa ON c.company_id = pa.company_id
GROUP BY c.company_id
ORDER BY patent_count DESC
LIMIT 20;


-- Q3: Countries — patents by patent type (utility vs design)
SELECT
    patent_type,
    COUNT(*) AS patent_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM patents), 2) AS share_pct
FROM patents
WHERE patent_type IS NOT NULL
GROUP BY patent_type
ORDER BY patent_count DESC;


-- Q4: Trends Over Time — how many patents per year?
SELECT
    year,
    COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year ASC;


-- Q5: JOIN Query — patents with inventor and company names
SELECT
    p.patent_id,
    p.title,
    p.patent_type,
    p.year,
    i.name   AS inventor_name,
    c.name   AS company_name
FROM patents p
JOIN patent_inventor pi  ON p.patent_id  = pi.patent_id
JOIN inventors i         ON pi.inventor_id = i.inventor_id
LEFT JOIN patent_assignee pa ON p.patent_id = pa.patent_id
LEFT JOIN companies c    ON pa.company_id = c.company_id
LIMIT 100;


-- Q6: CTE Query — top inventors per patent type
WITH inventor_counts AS (
    SELECT
        i.inventor_id,
        i.name,
        p.patent_type,
        COUNT(DISTINCT pi.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
    JOIN patents p          ON pi.patent_id  = p.patent_id
    GROUP BY i.inventor_id, p.patent_type
),
type_totals AS (
    SELECT
        patent_type,
        SUM(patent_count) AS type_total
    FROM inventor_counts
    GROUP BY patent_type
)
SELECT
    ic.patent_type,
    ic.name,
    ic.patent_count,
    tt.type_total,
    ROUND(100.0 * ic.patent_count / tt.type_total, 4) AS pct_of_type
FROM inventor_counts ic
JOIN type_totals tt ON ic.patent_type = tt.patent_type
ORDER BY ic.patent_count DESC
LIMIT 50;


-- Q7: Ranking Query — rank inventors by patent count using window functions
SELECT
    name,
    patent_type,
    patent_count,
    RANK() OVER (ORDER BY patent_count DESC)                              AS global_rank,
    RANK() OVER (PARTITION BY patent_type ORDER BY patent_count DESC)    AS rank_in_type,
    ROUND(100.0 * patent_count / SUM(patent_count) OVER (), 4)           AS global_share_pct
FROM (
    SELECT
        i.inventor_id,
        i.name,
        p.patent_type,
        COUNT(DISTINCT pi.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_inventor pi ON i.inventor_id = pi.inventor_id
    JOIN patents p          ON pi.patent_id  = p.patent_id
    GROUP BY i.inventor_id, p.patent_type
) sub
ORDER BY global_rank
LIMIT 50;
