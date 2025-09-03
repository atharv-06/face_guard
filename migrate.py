import sqlite3

DB_PATH = "faceguard.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check existing columns in 'logs'
c.execute("PRAGMA table_info(logs)")
columns = [col[1] for col in c.fetchall()]

# Add 'snapshot' column if missing
if "snapshot" not in columns:
    c.execute("ALTER TABLE logs ADD COLUMN snapshot TEXT")
    print("✅ Added 'snapshot' column to logs table")
else:
    print("ℹ️ 'snapshot' column already exists")

conn.commit()
conn.close()
