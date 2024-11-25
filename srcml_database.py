import sqlite3

connection = sqlite3.connect("data/srcml.db3", check_same_thread=False)
connection.execute("PRAGMA foreign_keys = 1")
connection.row_factory = sqlite3.Row

def _create_database():
    cursor.execute("""
CREATE TABLE IF NOT EXISTS "repository" (
    "repository_name" TEXT
);
""")
