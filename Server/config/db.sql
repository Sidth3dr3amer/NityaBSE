CREATE TABLE announcements (
  id TEXT PRIMARY KEY,                 -- hash
  company_code TEXT,                   -- optional BSE code
  company_name TEXT NOT NULL,

  title TEXT,                          -- cleaned headline for UI/email
  subject TEXT NOT NULL,               -- raw BSE subject
  summary TEXT,                        -- short extracted description

  category TEXT,                       -- board_meeting, results, compliance, etc.

  filed_at TIMESTAMP NOT NULL,          -- exchange filing time
  scraped_at TIMESTAMP DEFAULT NOW(),   -- when your system saw it

  pdf_url TEXT NOT NULL,
  screenshot_url TEXT,

  source_page TEXT,                    -- BSE page URL
  exchange TEXT DEFAULT 'BSE',
  index_name TEXT DEFAULT 'BANKEX',

  uploaded BOOLEAN DEFAULT FALSE,       -- if sent to feeds/emails
  created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE subscribers (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  companies TEXT[],                    -- watchlist
  categories TEXT[],                   -- optional
  digest_mode TEXT DEFAULT 'daily',    -- instant / daily / weekly
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
