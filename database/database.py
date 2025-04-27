import os
import sqlite3

# Nombre de la DB y ruta al SQL
DB_FILE    = "database.db"
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    """
    Si no existe database.db, lo crea y ejecuta el SQL de schema.sql
    """
    db_exists = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    if not db_exists:
        with open(SCHEMA_FILE, encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
    conn.close()

def get_db():
    """
    Dependencia de FastAPI que abre una conexión SQLite
    y la cierra al terminar la petición.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()