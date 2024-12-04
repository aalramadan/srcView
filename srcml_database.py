import sqlite3
import os

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

try:
    connection = sqlite3.connect("data/srcml.db3",check_same_thread=False)
except sqlite3.OperationalError:
    if not os.path.exists('data'):
        os.makedirs('data')
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
        CREATE TABLE IF NOT EXISTS "identifier" (
            name TEXT NOT NULL,
            type TEXT,
            category TEXT NOT NULL,
            file_id INTEGER,
            line INTEGER NOT NULL,
            column INTEGER NOT NULL,
            stereotype TEXT,
            nameChecker TEXT,
            violationCode TEXT,
            FOREIGN KEY(file_id) REFERENCES file(id),
            PRIMARY KEY(name,category,file_id,line,column)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "tag_count" (
            tag TEXT NOT NULL,
            file_id INTEGER,
            count INTEGER NOT NULL,
            FOREIGN KEY(file_id) REFERENCES file(id),
            PRIMARY KEY(tag,file_id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "query_run" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            query_type TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "query_run_result" (
            file_id INTEGER,
            query_id INTEGER,
            FOREIGN KEY(file_id) REFERENCES file(id),
            FOREIGN KEY(query_id) REFERENCES query_run(id),
            PRIMARY KEY(file_id,query_id)
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

def get_file_id_from_name_and_repo(filename,repo_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id
        FROM file
        WHERE name=? AND repo_id=?
    """, (filename,repo_id))
    return cursor.fetchone()["id"]

def add_identifier(name,type,category,file_id,line,column,stereotype, nameChecker, violationCode):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO identifier (name,type,category,file_id,line,column,stereotype, nameChecker, violationCode)
        VALUES (?,?,?,?,?,?,?,?,?)
    """,(name,type,category,file_id,line,column,stereotype, nameChecker, violationCode))


def add_tag_count(tag,file_id,count):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO tag_count (tag,file_id,count)
        VALUES (?,?,?)
    """,(tag,file_id,count))

def fetch_table_data(table_name):
    cursor = connection.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    

    if cols and isinstance(cols[0], dict):  
        columns = [col['name'] for col in cols]
    else:  
        columns = [col[1] for col in cols]
    
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    return columns, rows


def fetch_table_names():
    # try:
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    rows = cursor.fetchall()
    if rows and isinstance(rows[0], dict):  # If rows are dictionaries
        table_names = [row['name'] for row in rows]
    else:  # Default to tuple format
        table_names = [row[0] for row in rows]

    return table_names