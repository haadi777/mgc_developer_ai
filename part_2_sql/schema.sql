-- schema.sql

CREATE TABLE IF NOT EXISTS leads (
    lead_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT,
    last_name     TEXT,
    email         TEXT,
    phone         TEXT,
    city          TEXT,
    lead_source   TEXT,
    status        TEXT NOT NULL CHECK (status IN ('NEW', 'CONTACTED', 'QUALIFIED', 'CONVERTED', 'LOST')),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for source-level conversion analytics
CREATE INDEX IF NOT EXISTS idx_leads_source_status 
ON leads (lead_source, status);

-- Index for deduplication lookups by key identity fields
CREATE INDEX IF NOT EXISTS idx_leads_email 
ON leads (email) 
WHERE email IS NOT NULL AND email != '';

CREATE INDEX IF NOT EXISTS idx_leads_phone 
ON leads (phone) 
WHERE phone IS NOT NULL AND phone != '';