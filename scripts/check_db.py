import sqlite3
conn = sqlite3.connect('database/patents.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for (t,) in tables:
    cols = [c[1] for c in conn.execute(f'PRAGMA table_info({t})')]
    print(f'{t}: {cols}')
conn.close()