import sqlite3

DB_PATH = 'faceguard.db'

def get_conn():
    """Return a SQLite connection with threading support."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_column(cursor, table, column, col_type):
    """Add a missing column to a table if it doesn’t exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✅ Added missing column '{column}' to {table}")

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY,
            name TEXT,
            room TEXT,
            contact TEXT
        )
    ''')

    # Persons table (for face recognition dataset)
    c.execute('''
        CREATE TABLE IF NOT EXISTS persons(
            id INTEGER PRIMARY KEY,
            name TEXT,
            image_path TEXT
        )
    ''')

    # Blacklist table
    c.execute('''
        CREATE TABLE IF NOT EXISTS blacklist(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            reason TEXT
        )
    ''')

    # Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            timestamp TEXT,
            status TEXT
        )
    ''')

    # Ensure 'snapshot' column exists in logs (safe migration)
    ensure_column(c, "logs", "snapshot", "TEXT")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('✅ Database initialized and up-to-date.')
