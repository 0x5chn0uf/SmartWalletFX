-- Large Dataset SQL Fixture for Performance Testing
-- This script creates a realistic database with substantial data volume
-- for testing backup/restore performance against the < 30s for 1GB requirement

-- Create test tables with realistic schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(42) UNIQUE NOT NULL,
    name VARCHAR(100),
    wallet_type VARCHAR(20) DEFAULT 'ethereum',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    hash VARCHAR(66) UNIQUE NOT NULL,
    block_number BIGINT NOT NULL,
    value DECIMAL(36, 18) NOT NULL,
    gas_used BIGINT,
    gas_price BIGINT,
    status VARCHAR(20) DEFAULT 'confirmed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE token_balances (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    token_address VARCHAR(42) NOT NULL,
    balance DECIMAL(36, 18) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    total_value DECIMAL(36, 18) NOT NULL,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_token_balances_wallet_id ON token_balances(wallet_id);
CREATE INDEX idx_portfolio_snapshots_user_id ON portfolio_snapshots(user_id);
CREATE INDEX idx_portfolio_snapshots_created_at ON portfolio_snapshots(created_at);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Create a function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_token_balances_updated_at BEFORE UPDATE ON token_balances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a function to generate random Ethereum addresses
CREATE OR REPLACE FUNCTION generate_ethereum_address()
RETURNS VARCHAR(42) AS $$
BEGIN
    RETURN '0x' || lpad(to_hex(floor(random() * 9223372036854775807)::bigint), 40, '0');
END;
$$ LANGUAGE plpgsql;

-- Create a function to generate random transaction hashes
CREATE OR REPLACE FUNCTION generate_transaction_hash()
RETURNS VARCHAR(66) AS $$
BEGIN
    RETURN '0x' || lpad(to_hex(floor(random() * 9223372036854775807)::bigint), 64, '0');
END;
$$ LANGUAGE plpgsql;

-- Insert large amounts of test data
-- Users (10,000 users)
INSERT INTO users (username, email, password_hash)
SELECT 
    'user_' || i,
    'user' || i || '@example.com',
    '$2b$12$' || encode(gen_random_bytes(22), 'base64')
FROM generate_series(1, 10000) AS i;

-- Wallets (30,000 wallets - 3 per user on average)
INSERT INTO wallets (user_id, address, name, wallet_type)
SELECT 
    (i % 10000) + 1,
    generate_ethereum_address(),
    CASE (i % 3)
        WHEN 0 THEN 'Main Wallet'
        WHEN 1 THEN 'Trading Wallet'
        ELSE 'Savings Wallet'
    END,
    CASE (i % 4)
        WHEN 0 THEN 'ethereum'
        WHEN 1 THEN 'polygon'
        WHEN 2 THEN 'arbitrum'
        ELSE 'optimism'
    END
FROM generate_series(1, 30000) AS i;

-- Transactions (500,000 transactions)
INSERT INTO transactions (wallet_id, hash, block_number, value, gas_used, gas_price, status)
SELECT 
    (i % 30000) + 1,
    generate_transaction_hash(),
    1000000 + (i % 1000000),
    (random() * 1000)::decimal(36, 18),
    21000 + (random() * 100000)::bigint,
    20000000000 + (random() * 50000000000)::bigint,
    CASE (i % 100)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'failed'
        ELSE 'confirmed'
    END
FROM generate_series(1, 500000) AS i;

-- Token balances (150,000 token balances)
INSERT INTO token_balances (wallet_id, token_address, balance)
SELECT 
    (i % 30000) + 1,
    generate_ethereum_address(),
    (random() * 10000)::decimal(36, 18)
FROM generate_series(1, 150000) AS i;

-- Portfolio snapshots (50,000 snapshots)
INSERT INTO portfolio_snapshots (user_id, total_value, snapshot_data)
SELECT 
    (i % 10000) + 1,
    (random() * 100000)::decimal(36, 18),
    jsonb_build_object(
        'tokens', jsonb_build_array(
            jsonb_build_object('address', generate_ethereum_address(), 'balance', random() * 1000),
            jsonb_build_object('address', generate_ethereum_address(), 'balance', random() * 1000),
            jsonb_build_object('address', generate_ethereum_address(), 'balance', random() * 1000)
        ),
        'last_updated', now()::text
    )
FROM generate_series(1, 50000) AS i;

-- Audit logs (200,000 audit entries)
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address)
SELECT 
    (i % 10000) + 1,
    CASE (i % 10)
        WHEN 0 THEN 'login'
        WHEN 1 THEN 'logout'
        WHEN 2 THEN 'create_wallet'
        WHEN 3 THEN 'update_wallet'
        WHEN 4 THEN 'delete_wallet'
        WHEN 5 THEN 'view_portfolio'
        WHEN 6 THEN 'export_data'
        WHEN 7 THEN 'change_password'
        WHEN 8 THEN 'update_profile'
        ELSE 'view_transactions'
    END,
    CASE (i % 5)
        WHEN 0 THEN 'wallet'
        WHEN 1 THEN 'user'
        WHEN 2 THEN 'transaction'
        WHEN 3 THEN 'portfolio'
        ELSE 'token'
    END,
    (i % 100000)::text,
    jsonb_build_object('ip', '192.168.1.' || (i % 255), 'user_agent', 'Mozilla/5.0'),
    inet '192.168.1.' || (i % 255)
FROM generate_series(1, 200000) AS i;

-- Create a view for testing
CREATE VIEW wallet_summary AS
SELECT 
    w.id,
    w.address,
    w.name,
    u.username,
    COUNT(t.id) as transaction_count,
    SUM(t.value) as total_value,
    COUNT(tb.id) as token_count
FROM wallets w
JOIN users u ON w.user_id = u.id
LEFT JOIN transactions t ON w.id = t.wallet_id
LEFT JOIN token_balances tb ON w.id = tb.wallet_id
GROUP BY w.id, w.address, w.name, u.username;

-- Create a materialized view for performance testing
CREATE MATERIALIZED VIEW user_portfolio_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT w.id) as wallet_count,
    COUNT(t.id) as transaction_count,
    SUM(t.value) as total_transaction_value,
    COUNT(tb.id) as token_balance_count,
    AVG(ps.total_value) as avg_portfolio_value
FROM users u
LEFT JOIN wallets w ON u.id = w.user_id
LEFT JOIN transactions t ON w.id = t.wallet_id
LEFT JOIN token_balances tb ON w.id = tb.wallet_id
LEFT JOIN portfolio_snapshots ps ON u.id = ps.user_id
GROUP BY u.id, u.username;

-- Create index on materialized view
CREATE INDEX idx_user_portfolio_summary_user_id ON user_portfolio_summary(user_id);

-- Grant permissions for testing
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA public TO testuser;

-- Analyze tables for better query planning
ANALYZE; 