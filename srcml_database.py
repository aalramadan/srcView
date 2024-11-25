import sqlite3

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

try:
    connection = sqlite3.connect("data/srcml.db3",check_same_thread=False)
except sqlite3.OperationalError:
    file = open("data/srcml.db3",'wb')
    file.close()
finally:
    connection = sqlite3.connect("data/srcml.db3",check_same_thread=False)
connection.execute("PRAGMA foreign_keys = 1")
connection.row_factory = dict_factory

def _create_database():
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "repository" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "file" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            language TEXT NOT NULL,
            repo_id INTEGER,
            FOREIGN KEY(repo_id) REFERENCES repository(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "variable_name" (
            name TEXT NOT NULL,
            type TEXT,
            category TEXT NOT NULL,
            file_id INTEGER,
            line INTEGER NOT NULL,
            column INTEGER NOT NULL,
            FOREIGN KEY(file_id) REFERENCES file(id),
            PRIMARY KEY(name,category,file_id,line,column)
        );
    """)

def commit():
    connection.commit()


def add_repo(repo_name):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO repository (name)
        VALUES (?)
    """,(repo_name,))

def get_repo_id_from_name(repo_name):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id
        FROM repository
        WHERE name=?
    """, (repo_name,))
    return cursor.fetchone()["id"]

def add_file(name,language,repo_name):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO file (name,language,repo_id)
        VALUES (?,?,?);
    """, (name,language,get_repo_id_from_name(repo_name)))






