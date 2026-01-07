-- Supabase Database Schema for Portfolio Analytics
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_files_count INTEGER DEFAULT 0,
    has_report BOOLEAN DEFAULT false,
    report_generated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(50) NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    broker VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'Buy' or 'Sell'
    trade_date DATE NOT NULL,
    qty DECIMAL(20, 4) NOT NULL,
    price DECIMAL(20, 4) NOT NULL,
    amount DECIMAL(20, 4) NOT NULL,
    fees DECIMAL(20, 4) DEFAULT 0,
    file_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Capital gains table
CREATE TABLE IF NOT EXISTS capital_gains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(50) NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    broker VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    buy_date DATE,
    sell_date DATE NOT NULL,
    qty DECIMAL(20, 4) NOT NULL,
    buy_price DECIMAL(20, 4),
    sell_price DECIMAL(20, 4) NOT NULL,
    cost_basis DECIMAL(20, 4),
    proceeds DECIMAL(20, 4) NOT NULL,
    gain_loss DECIMAL(20, 4),
    holding_period VARCHAR(20), -- 'Short-term' or 'Long-term'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Reports metadata table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(50) NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL DEFAULT 'portfolio',
    file_path TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Job queue table (for RQ job tracking)
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(100) UNIQUE NOT NULL,
    client_id VARCHAR(50),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    result JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX idx_trades_client_id ON trades(client_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_trade_date ON trades(trade_date);
CREATE INDEX idx_capital_gains_client_id ON capital_gains(client_id);
CREATE INDEX idx_capital_gains_symbol ON capital_gains(symbol);
CREATE INDEX idx_reports_client_id ON reports(client_id);
CREATE INDEX idx_job_queue_job_id ON job_queue(job_id);
CREATE INDEX idx_job_queue_status ON job_queue(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to clients table
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE capital_gains ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all operations for authenticated users)
-- You can modify these based on your security requirements
CREATE POLICY "Enable all for authenticated users" ON clients FOR ALL USING (true);
CREATE POLICY "Enable all for authenticated users" ON trades FOR ALL USING (true);
CREATE POLICY "Enable all for authenticated users" ON capital_gains FOR ALL USING (true);
CREATE POLICY "Enable all for authenticated users" ON reports FOR ALL USING (true);
CREATE POLICY "Enable all for authenticated users" ON job_queue FOR ALL USING (true);

-- Optional: Create a view for client summary
CREATE OR REPLACE VIEW client_summary AS
SELECT 
    c.client_id,
    c.created_at,
    c.updated_at,
    c.has_report,
    c.report_generated_at,
    COUNT(DISTINCT t.broker) as broker_count,
    COUNT(DISTINCT t.symbol) as stock_count,
    COUNT(t.id) as trade_count,
    COUNT(cg.id) as capital_gains_count
FROM clients c
LEFT JOIN trades t ON c.client_id = t.client_id
LEFT JOIN capital_gains cg ON c.client_id = cg.client_id
GROUP BY c.client_id, c.created_at, c.updated_at, c.has_report, c.report_generated_at;
