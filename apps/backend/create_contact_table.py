import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Get database URL and convert SQLAlchemy format to psycopg2
db_url = os.getenv("DATABASE_URL_SYNC")
# Convert postgresql+psycopg2:// to postgresql://
db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

print(f"Connecting to database...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

print("Creating contact_submissions table...")
cur.execute('''
    CREATE TABLE IF NOT EXISTS contact_submissions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        subject VARCHAR(50) NOT NULL,
        message TEXT NOT NULL,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        processed BOOLEAN NOT NULL DEFAULT FALSE,
        processed_at TIMESTAMP WITH TIME ZONE
    );
''')

print("Creating indexes...")
cur.execute('CREATE INDEX IF NOT EXISTS ix_contact_submissions_email ON contact_submissions(email);')
cur.execute('CREATE INDEX IF NOT EXISTS ix_contact_submissions_subject ON contact_submissions(subject);')
cur.execute('CREATE INDEX IF NOT EXISTS ix_contact_submissions_created_at ON contact_submissions(created_at);')

conn.commit()
cur.close()
conn.close()

print("✅ contact_submissions table created successfully!")
