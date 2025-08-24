-- CRM-style schema for ISM partners (v4)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS partners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    address TEXT,
    number TEXT,
    postal_code TEXT,
    city TEXT,
    phone TEXT,
    employees_count INTEGER,
    website TEXT,
    responsible TEXT,
    role TEXT,
    email TEXT,
    activity TEXT,
    sector_class TEXT,
    tags TEXT, -- optional free tags, comma-separated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One-to-many table for partner contacts
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    function TEXT,
    email TEXT,
    phone TEXT,
    mobile TEXT,
    is_jury INTEGER DEFAULT 0, -- 0/1
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE
);

-- Helper indexes
CREATE INDEX IF NOT EXISTS idx_partners_company ON partners(company_name);
CREATE INDEX IF NOT EXISTS idx_contacts_partner ON contacts(partner_id);
