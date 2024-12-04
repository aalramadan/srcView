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

def get_repo_name_from_id(repo_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT name
        FROM repository
        WHERE id=?
    """, (repo_id,))
    return cursor.fetchone()["name"]

def get_repo_name_from_file_id(file_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT repository.name
        FROM file
            INNER JOIN repository ON file.repo_id = repository.id
        WHERE file.id=?
    """, (file_id,))
    return cursor.fetchone()["name"]

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

def get_file_name_from_id(file_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT name
        FROM file
        WHERE id=?
    """, (file_id,))
    return cursor.fetchone()["name"]

def add_identifier(name,type,category,file_id,line,column,stereotype):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO identifier (name,type,category,file_id,line,column,stereotype)
        VALUES (?,?,?,?,?,?,?)
    """,(name,type,category,file_id,line,column,stereotype))


def add_tag_count(tag,file_id,count):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO tag_count (tag,file_id,count)
        VALUES (?,?,?)
    """,(tag,file_id,count))


def retrieve_repos():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, name
        FROM repository
    """)
    return cursor.fetchall()

def retrieve_files(repo_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, name, language
        FROM file
        WHERE repo_id = ?
    """, (repo_id,))
    return cursor.fetchall()

def retrieve_identifiers(file_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT name, type, category, file_id, line, column, stereotype
        FROM identifier
        WHERE file_id = ?
    """, (file_id,))
    return cursor.fetchall()

def retrieve_identifiers_from_repo(repo_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT identifier.name, type, category, file_id, line, column, file.name as filename, stereotype
        FROM file
            INNER JOIN identifier ON file.id = identifier.file_id 
        WHERE repo_id = ?;
    """, (repo_id,))
    return cursor.fetchall()

def retrieve_tags(file_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT tag, file_id, count
        FROM tag_count
        WHERE file_id IN (SELECT id FROM file WHERE file_id = ?)
    """, (file_id,))
    return cursor.fetchall()

def retrieve_tags_from_repo(repo_id):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT tag, SUM(count) as count
        FROM repository
            INNER JOIN file ON repository.id = file.repo_id
            INNER JOIN tag_count ON file.id = tag_count.file_id
        WHERE repository.id = ?
        GROUP BY repository.id, tag
    """, (repo_id,))
    return cursor.fetchall()

def create_query_run(query,type):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO query_run(query,query_type)
        VALUES (?,?)
    """,(query,type))
    return cursor.lastrowid

def add_query_result(file_id,query_id):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO query_run_result(file_id,query_id)
        VALUES (?,?)
    """,(file_id,query_id))


def remove_repo(repo_id):
    cursor = connection.cursor()

    # Delete associated tags
    cursor.execute("""
        DELETE FROM tag_count
        WHERE file_id IN (SELECT id FROM file WHERE repo_id = ?)
    """, (repo_id,))

    # Delete associated identifiers
    cursor.execute("""
        DELETE FROM identifier
        WHERE file_id IN (SELECT id FROM file WHERE repo_id = ?)
    """, (repo_id,))

    # Delete associated files
    cursor.execute("""
        DELETE FROM file
        WHERE repo_id = ?
    """, (repo_id,))

    # Delete the repository
    cursor.execute("""
        DELETE FROM repository
        WHERE id = ?
    """, (repo_id,))

    commit()










