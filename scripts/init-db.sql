-- Initialize database for MyHibachi application
CREATE DATABASE IF NOT EXISTS myhibachi_db;

-- Create application user if not exists
CREATE USER IF NOT EXISTS 'myhibachi_user'@'%' IDENTIFIED BY 'REDACTED_DB_PASSWORD';
GRANT ALL PRIVILEGES ON myhibachi_db.* TO 'myhibachi_user'@'%';

-- Basic tables for development
\c myhibachi_db;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    service_type VARCHAR(100) NOT NULL,
    booking_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (email, name) VALUES
    ('test@example.com', 'Test User'),
    ('admin@myhibachi.com', 'Admin User')
ON CONFLICT (email) DO NOTHING;
