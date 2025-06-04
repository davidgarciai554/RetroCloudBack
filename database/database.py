import os
import sqlite3

DB_FILE    = "database/database.db"
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    db_exists = os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        with open(SCHEMA_FILE, encoding="utf-8") as f:
            schema_sql = f.read()
        if not db_exists:
            conn.executescript(schema_sql)
        else:
            # Check if JUEGOS_CONSOLAS has RUTA_NUBE and JUEGOS does NOT have ROUTE
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(JUEGOS_CONSOLAS)")
            juegos_consolas_cols = [row[1] for row in cursor.fetchall()]
            cursor.execute("PRAGMA table_info(JUEGOS)")
            juegos_cols = [row[1] for row in cursor.fetchall()]
            needs_migration = False
            if "RUTA_NUBE" not in juegos_consolas_cols:
                needs_migration = True
            if "ROUTE" in juegos_cols:
                needs_migration = True
            if needs_migration:
                try:
                    # Try to migrate: add RUTA_NUBE, remove ROUTE
                    if "RUTA_NUBE" not in juegos_consolas_cols:
                        cursor.execute("ALTER TABLE JUEGOS_CONSOLAS ADD COLUMN RUTA_NUBE TEXT DEFAULT ''")
                    if "ROUTE" in juegos_cols:
                        # SQLite does not support DROP COLUMN directly; need to recreate table
                        raise Exception("La columna 'ROUTE' debe eliminarse manualmente de la tabla JUEGOS. Por favor, realiza una migración manual.")
                    conn.commit()
                except Exception as e:
                    raise Exception(f"Error actualizando la estructura de la base de datos: {e}")
    finally:
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