import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT unique,
            phone text unique,
username TEXT,
password TEXT,
vulgar_count INTEGER DEFAULT 0,
blocked INTEGER DEFAULT 0,
logical_address TEXT   -- ✅ ADDED
)
""")

cur.execute("""
CREATE TABLE posts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
caption TEXT,
image TEXT,
result TEXT,
likes INTEGER
)
""")

cur.execute("""
CREATE TABLE comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
post_id INTEGER,
username TEXT,
comment TEXT
)
""")

cur.execute("""
CREATE TABLE reels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
video TEXT
)
""")

cur.execute("""
CREATE TABLE messages(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
message TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully")