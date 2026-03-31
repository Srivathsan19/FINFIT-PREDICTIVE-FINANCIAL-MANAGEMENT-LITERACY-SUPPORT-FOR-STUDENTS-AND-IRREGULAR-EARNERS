#!/usr/bin/env python3
"""
Simple script to view FinFit SQLite database.
Run from the backend folder:  python view_database.py
"""
import os
import sqlite3

# Database is in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        print("Run the Flask app first to create the database (python app.py).")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    cur = conn.cursor()

    # Get list of tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]
    print("=" * 60)
    print("FinFit Database Viewer")
    print("=" * 60)
    print(f"Database: {DB_PATH}\n")
    print("Tables:", ", ".join(tables))
    print()

    for table in tables:
        print("-" * 60)
        print(f"TABLE: {table}")
        print("-" * 60)
        cur.execute(f"SELECT * FROM {table} LIMIT 20")
        rows = cur.fetchall()
        if not rows:
            print("  (no rows)\n")
            continue
        # Column names
        col_names = [d[0] for d in cur.description]
        print("  Columns:", ", ".join(col_names))
        print()
        for row in rows:
            # Mask password_hash for security
            row_dict = dict(row)
            if 'password_hash' in row_dict and row_dict['password_hash']:
                row_dict['password_hash'] = '***'
            print("  ", dict(row_dict))
        if cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 20:
            print("  ... (showing first 20 rows only)")
        print()

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
