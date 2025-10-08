#!/usr/bin/env python3
"""
Simple SQLite database initialization for local development.
This creates the essential tables needed for the API to run.
"""

import sqlite3
import os
from pathlib import Path

# Get the database path
db_path = Path(__file__).parent / "mh-bookings.db"

# Remove existing database if it exists
if db_path.exists():
    os.remove(db_path)

# Create new database and tables
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create essential tables for the booking system
cursor.executescript("""
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    hashed_password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chef services table
CREATE TABLE IF NOT EXISTS chef_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price_per_person DECIMAL(10,2),
    duration_hours INTEGER,
    max_guests INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service_id INTEGER,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    guest_count INTEGER NOT NULL,
    total_amount DECIMAL(10,2),
    status TEXT DEFAULT 'pending',
    special_requests TEXT,
    stripe_payment_intent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (service_id) REFERENCES chef_services (id)
);

-- Waitlist table
CREATE TABLE IF NOT EXISTS waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service_id INTEGER,
    preferred_date DATE,
    preferred_time TIME,
    guest_count INTEGER,
    notes TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (service_id) REFERENCES chef_services (id)
);

-- Insert some sample data
INSERT INTO chef_services (name, description, price_per_person, duration_hours, max_guests)
VALUES 
('Hibachi Dinner Experience', 'Traditional hibachi cooking with entertainment', 75.00, 2, 12),
('Sushi Making Class', 'Learn to make sushi with a professional chef', 85.00, 3, 8),
('Teppanyaki Show', 'Interactive teppanyaki cooking show', 90.00, 2, 10);

-- Create an admin user (password is 'admin123' - you should change this)
INSERT INTO users (email, full_name, is_superuser, hashed_password)
VALUES ('admin@myhibachi.com', 'Admin User', TRUE, '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW');
""")

conn.commit()
conn.close()

print(f"✅ SQLite database created at: {db_path}")
print("📊 Tables created: users, chef_services, bookings, waitlist")
print("🔑 Default admin login: admin@myhibachi.com / admin123")
print("🛠️  Database ready for local development!")