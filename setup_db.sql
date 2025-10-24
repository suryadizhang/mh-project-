-- Create user for the application
CREATE ROLE "user" WITH LOGIN PASSWORD 'password';

-- Grant all privileges on database to user
GRANT ALL PRIVILEGES ON DATABASE myhibachi_crm TO "user";

-- Connect to the database (this is a psql meta-command, not SQL)
-- \c myhibachi_crm

-- Grant schema privileges (run these after connecting to the database)
GRANT ALL ON SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "user";
