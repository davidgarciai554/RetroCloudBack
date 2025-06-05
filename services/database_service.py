import sqlite3
import os
from typing import List, Optional, Tuple

class DatabaseService:
    @staticmethod
    def merge_juegos_db():
        """Fusiona la base de datos de juegos con la principal."""
        db_path = os.path.join("database", "database.db")
        juegos_db_path = os.path.join("database", "juegos.db")
        
        if not os.path.exists(juegos_db_path):
            print(f"juegos.db not found at {juegos_db_path}")
            return
        
        conn_main = sqlite3.connect(db_path)
        conn_juegos = sqlite3.connect(juegos_db_path)
        
        try:
            main_cur = conn_main.cursor()
            juegos_cur = conn_juegos.cursor()
            
            def merge_table(table: str):
                main_cur.execute(f"PRAGMA table_info({table})")
                main_cols = [col[1] for col in main_cur.fetchall()]
                juegos_cur.execute(f"PRAGMA table_info({table})")
                juegos_cols = [col[1] for col in juegos_cur.fetchall()]
                common_cols = [col for col in juegos_cols if col in main_cols]
                col_str = ", ".join(common_cols)
                placeholders = ", ".join(["?" for _ in common_cols])
                rows = juegos_cur.execute(f"SELECT {col_str} FROM {table}").fetchall()
                for row in rows:
                    main_cur.execute(f"INSERT OR IGNORE INTO {table} ({col_str}) VALUES ({placeholders})", row)
            
            for table in ["EMPRESAS", "CONSOLAS", "JUEGOS", "JUEGOS_CONSOLAS"]:
                merge_table(table)
            
            conn_main.commit()
        finally:
            conn_main.close()
            conn_juegos.close()