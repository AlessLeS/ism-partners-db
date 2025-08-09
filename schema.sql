
-- Simplified schema for ISM partners (v3)
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
