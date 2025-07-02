-- Enable common extensions required by the application
-- This script is executed automatically by the official postgres image
-- when the data directory is initialised (mounted under /docker-entrypoint-initdb.d)

-- Provide uuid generation helpers (sa.uuid + default server-side uuid-ossp)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Provide cryptographic functions (optional, but useful)
CREATE EXTENSION IF NOT EXISTS pgcrypto;