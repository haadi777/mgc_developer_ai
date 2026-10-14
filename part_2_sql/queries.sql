-- queries.sql

-- ============================================================================
-- QUERY 1: Conversion rate by lead source (200+ leads only, best first)
-- ============================================================================

SELECT 
    COALESCE(NULLIF(TRIM(lead_source), ''), 'Unknown/Missing') AS lead_source,
    COUNT(*) AS total_leads,
    SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) AS converted_leads,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) / COUNT(*), 
        2
    ) AS conversion_rate_pct
FROM leads
GROUP BY 1
HAVING COUNT(*) >= 200
ORDER BY conversion_rate_pct DESC;


-- ============================================================================
-- QUERY 2: Find duplicates & retain 1 canonical row per duplicate pair
-- ============================================================================
/*
 PREVENTING DUPLICATES AT SCHEMA LEVEL:
 1. Lowercase Unique Index: 
    CREATE UNIQUE INDEX uq_leads_email_lower ON leads (LOWER(email)) WHERE email IS NOT NULL AND email != '';
 2. Generated Column / Expression Index: 
    Store normalized identity keys (e.g., standard phone numbers) with UNIQUE constraints.
 3. Upsert Logic: 
    In application code, use `INSERT INTO leads (...) VALUES (...) ON CONFLICT (email) DO UPDATE ...`.
*/

WITH RankedDuplicates AS (
    SELECT 
        lead_id,
        first_name,
        last_name,
        email,
        phone,
        status,
        created_at,
        -- Deterministic winner rule:
        -- 1. 'CONVERTED' status takes highest priority
        -- 2. Most recent creation date (`created_at` DESC)
        -- 3. Highest `lead_id` as a final tiebreaker for absolute determinism
        ROW_NUMBER() OVER (
            PARTITION BY 
                CASE 
                    WHEN email IS NOT NULL AND TRIM(email) != '' THEN LOWER(TRIM(email))
                    ELSE LOWER(TRIM(phone))
                END
            ORDER BY 
                CASE WHEN status = 'CONVERTED' THEN 1 ELSE 2 END ASC,
                created_at DESC,
                lead_id DESC
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY 
                CASE 
                    WHEN email IS NOT NULL AND TRIM(email) != '' THEN LOWER(TRIM(email))
                    ELSE LOWER(TRIM(phone))
                END
        ) AS group_count
    FROM leads
    WHERE 
        (email IS NOT NULL AND TRIM(email) != '') 
        OR (phone IS NOT NULL AND TRIM(phone) != '')
)
SELECT 
    lead_id,
    first_name,
    last_name,
    email,
    phone,
    status,
    created_at
FROM RankedDuplicates
WHERE group_count > 1  -- Filters to only duplicate groups
  AND rn = 1;          -- Retains the single canonical winner per pair/group


-- ============================================================================
-- QUERY 3: Conversion rate by city after normalizing messy spellings
-- ============================================================================

WITH NormalizedLeads AS (
    SELECT 
        lead_id,
        status,
        CASE 
            WHEN UPPER(TRIM(city)) IN ('ISB', 'ISLAMABAD') THEN 'Islamabad'
            WHEN UPPER(TRIM(city)) IN ('RWP', 'RAWALPINDI') THEN 'Rawalpindi'
            WHEN UPPER(TRIM(city)) IN ('KHI', 'KARACHI') THEN 'Karachi'
            WHEN UPPER(TRIM(city)) IN ('LHR', 'LAHORE') THEN 'Lahore'
            WHEN TRIM(city) IS NULL OR TRIM(city) = '' THEN 'Unknown'
            ELSE UPPER(SUBSTR(TRIM(city), 1, 1)) || LOWER(SUBSTR(TRIM(city), 2))
        END AS normalized_city
    FROM leads
)
SELECT 
    normalized_city,
    COUNT(*) AS total_leads,
    SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) AS converted_leads,
    ROUND(
        100.0 * SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) / COUNT(*), 
        2
    ) AS conversion_rate_pct
FROM NormalizedLeads
GROUP BY normalized_city
ORDER BY total_leads DESC;