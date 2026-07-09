CREATE TABLE IF NOT EXISTS bids (
        "MaterialTicker" TEXT,
        "ExchangeCode" TEXT,
        "CompanyId" TEXT,
        "CompanyName" TEXT,
        "CompanyCode" TEXT,
        "ItemCount" BIGINT,
        "ItemCost" FLOAT,
        "CXTicker" TEXT,
        rank BIGINT,
        timestamp DATETIME
);
CREATE TABLE IF NOT EXISTS orders (
        "MaterialTicker" TEXT,
        "ExchangeCode" TEXT,
        "CompanyId" TEXT,
        "CompanyName" TEXT,
        "CompanyCode" TEXT,
        "ItemCount" BIGINT,
        "ItemCost" FLOAT,
        "CXTicker" TEXT,
        rank BIGINT,
        timestamp DATETIME
);
CREATE TABLE IF NOT EXISTS cxpc (
        "Open" FLOAT,
        "Close" FLOAT,
        "Volume" FLOAT,
        "Traded" BIGINT,
        ts DATETIME,
        "Ticker" TEXT,
        "CX" TEXT
);
CREATE INDEX IF NOT EXISTS idx_timestamp_orders on orders(timestamp);
CREATE INDEX IF NOT EXISTS idx_timestamp_bids on bids(timestamp);