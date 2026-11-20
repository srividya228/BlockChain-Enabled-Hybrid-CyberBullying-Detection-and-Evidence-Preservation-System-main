import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("UPDATE users SET vulgar_count=0, blocked=0")

conn.commit()
conn.close()

print("reset done")