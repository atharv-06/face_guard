from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DB_PATH = "faceguard.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # ✅ access rows as dict
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logs")
def logs():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("logs.html", rows=rows)

@app.route("/alerts")
def alerts():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM logs WHERE status IN ('Intruder', 'Late Entry') ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return render_template("alerts.html", rows=rows)

if __name__ == "__main__":
    app.run(debug=True)
