import sqlite3
import glob
import os

def check_db(path):
    print("Checking:", path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables:", tables)
    for t in tables:
        tname = t[0]
        cur.execute(f"PRAGMA table_info({tname});")
        cols = cur.fetchall()
        print(f"  Table {tname}:", [c[1] for c in cols])
        cur.execute(f"SELECT count(*) FROM {tname};")
        print(f"    Count: {cur.fetchone()[0]}")
    conn.close()

if __name__ == '__main__':
    check_db(os.path.expanduser(r"~/.gemini/antigravity/conversation_summaries.db"))
    sample_dbs = glob.glob(os.path.expanduser(r"~/.gemini/antigravity/conversations/*.db"))
    if sample_dbs:
        print("\n--- Sample conversation db ---")
        check_db(sample_dbs[0])
