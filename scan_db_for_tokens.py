import sys, sqlite3, re

if len(sys.argv) < 2:
    print("Usage: python scan_db_for_tokens.py path/to/db")
    sys.exit(1)

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
cur = conn.cursor()

patterns = [
    re.compile(r'ya29\.[A-Za-z0-9_\-\.]{10,}'),
    re.compile(r'AIza[0-9A-Za-z\-_]{10,}'),
    re.compile(r'1//[A-Za-z0-9_\-\.]{10,}'),
    re.compile(r'[A-Za-z0-9_\-]{40,}')
]

def match_any(s):
    if not s:
        return None
    for p in patterns:
        m = p.search(s)
        if m:
            return m.group(0)
    return None

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]

found = []
for t in tables:
    try:
        cur.execute(f"PRAGMA table_info('{t}');")
        cols = [r[1] for r in cur.fetchall()]
        cur.execute(f"SELECT rowid, * FROM '{t}';")
        rows = cur.fetchall()
        for row in rows:
            rowid = row[0]
            for idx, val in enumerate(row[1:], start=1):
                if isinstance(val, (str, bytes)):
                    s = val.decode('utf-8', errors='ignore') if isinstance(val, bytes) else val
                    m = match_any(s)
                    if m:
                        colname = cols[idx-1] if idx-1 < len(cols) else f'col{idx-1}'
                        found.append((t, rowid, colname, m, s[:300]))
    except Exception:
        pass

if not found:
    print("No suspicious patterns found.")
else:
    print("Found suspicious strings:")
    for t, rowid, col, match, snippet in found:
        print(f"TABLE: {t}  ROWID: {rowid}  COLUMN: {col}  MATCH: {match}")
        print("SNIPPET:", snippet)
        print("-" * 50)

conn.close()
