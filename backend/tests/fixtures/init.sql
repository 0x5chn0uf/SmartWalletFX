-- Test Database Initialization Script
-- This script sets up a realistic database schema and test data for backup/restore testing
-- It includes various PostgreSQL features to ensure comprehensive testing

-- Create test tables with realistic schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(42) UNIQUE NOT NULL,
    name VARCHAR(100),
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE token_balances (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    token_address VARCHAR(42) NOT NULL,
    balance DECIMAL(36, 18) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance testing
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);
CREATE INDEX idx_token_balances_wallet_id ON token_balances(wallet_id);

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

-- Insert test data
INSERT INTO users (username, email) VALUES
    ('testuser1', 'user1@example.com'),
    ('testuser2', 'user2@example.com'),
    ('testuser3', 'user3@example.com');

INSERT INTO wallets (user_id, address, name) VALUES
    (1, '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6', 'Main Wallet'),
    (1, '0x1234567890123456789012345678901234567890', 'Secondary Wallet'),
    (2, '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd', 'User 2 Wallet'),
    (3, '0x9876543210987654321098765432109876543210', 'User 3 Wallet');

INSERT INTO transactions (wallet_id, hash, block_number, value, gas_used, gas_price) VALUES
    (1, '0x1111111111111111111111111111111111111111111111111111111111111111', 1000000, 1.5, 21000, 20000000000),
    (1, '0x2222222222222222222222222222222222222222222222222222222222222222', 1000001, 0.5, 65000, 25000000000),
    (2, '0x3333333333333333333333333333333333333333333333333333333333333333', 1000002, 2.0, 21000, 18000000000),
    (3, '0x4444444444444444444444444444444444444444444444444444444444444444', 1000003, 0.1, 45000, 22000000000);

INSERT INTO token_balances (wallet_id, token_address, balance) VALUES
    (1, '0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8C', 1000.0),
    (1, '0xB1c97b44E6442b9c5C9C9C9C9C9C9C9C9C9C9C9C', 500.5),
    (2, '0xC2d08c55E6443b0c6C6C6C6C6C6C6C6C6C6C6C6C', 250.25),
    (3, '0xD3e19d66E6444b1c7C7C7C7C7C7C7C7C7C7C7C7C', 750.75);

-- Create a view for testing
CREATE VIEW wallet_summary AS
SELECT 
    w.id,
    w.address,
    w.name,
    u.username,
    COUNT(t.id) as transaction_count,
    SUM(t.value) as total_value
FROM wallets w
JOIN users u ON w.user_id = u.id
LEFT JOIN transactions t ON w.id = t.wallet_id
GROUP BY w.id, w.address, w.name, u.username;

-- Grant permissions for testing
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO testuser;
