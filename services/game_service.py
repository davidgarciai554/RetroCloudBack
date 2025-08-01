import sqlite3
import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()
PRINCIPIO_RUTA = os.getenv("PRINCIPIO_RUTA", "")

class GameService:
    @staticmethod
    def get_empresas_con_juegos(db: sqlite3.Connection) -> List[Tuple[int, str]]:
        """Obtiene empresas que tienen juegos con ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT DISTINCT e.ID, e.NOMBRE
            FROM EMPRESAS e
            JOIN CONSOLAS c ON e.ID = c.EMPRESA_ID
            JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
            WHERE IFNULL(jc.RUTA_NUBE, '') != ''
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def get_consolas_por_empresa(db: sqlite3.Connection, empresa_id: int) -> List[Tuple[int, str]]:
        """Obtiene consolas de una empresa que tienen juegos con ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT DISTINCT c.ID, c.NOMBRE
            FROM CONSOLAS c
            JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
            JOIN JUEGOS j ON jc.JUEGO_ID = j.ID
            WHERE c.EMPRESA_ID = ? AND IFNULL(jc.RUTA_NUBE, '') != ''
        """
        cursor.execute(query, (empresa_id,))
        return cursor.fetchall()
    
    @staticmethod
    def get_todas_consolas_con_juegos(db: sqlite3.Connection) -> List[Tuple[int, str, str]]:
        """Obtiene todas las consolas que tienen juegos con ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT DISTINCT c.ID, c.NOMBRE, e.NOMBRE as EMPRESA_NOMBRE
            FROM CONSOLAS c
            JOIN EMPRESAS e ON c.EMPRESA_ID = e.ID
            JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
            WHERE IFNULL(jc.RUTA_NUBE, '') != ''
            ORDER BY e.NOMBRE, c.NOMBRE
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def get_juegos_por_consola(db: sqlite3.Connection, consola_id: int) -> List[Tuple[int, str, Optional[str]]]:
        """Obtiene juegos de una consola que tienen ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT j.ID, j.NOMBRE, j.FECHA_LANZAMIENTO
            FROM JUEGOS j
            JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
            WHERE jc.CONSOLA_ID = ? AND IFNULL(jc.RUTA_NUBE, '') != ''
        """
        cursor.execute(query, (consola_id,))
        return cursor.fetchall()
    
    @staticmethod
    def registrar_juego(db: sqlite3.Connection, juego_id: int, consola_id: int) -> Optional[str]:
        """Registra un juego asignando una ruta predeterminada."""
        cursor = db.cursor()
        cursor.execute(
            "SELECT e.NOMBRE, c.NOMBRE, j.NOMBRE FROM JUEGOS j "
            "JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID "
            "JOIN CONSOLAS c ON jc.CONSOLA_ID = c.ID "
            "JOIN EMPRESAS e ON c.EMPRESA_ID = e.ID "
            "WHERE j.ID = ? AND c.ID = ?",
            (juego_id, consola_id)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        nombre_empresa, nombre_consola, nombre_juego = row
        nombre_juego = nombre_juego.strip()
        ruta = f"{PRINCIPIO_RUTA}/{nombre_empresa}/{nombre_consola}/{nombre_juego}.zip"
        
        cursor.execute(
            "UPDATE JUEGOS_CONSOLAS SET RUTA_NUBE = ? WHERE JUEGO_ID = ? AND CONSOLA_ID = ?",
            (ruta, juego_id, consola_id)
        )
        db.commit()
        return ruta
    
    @staticmethod
    def search_all(db: sqlite3.Connection, query: str, search_type: str = "all") -> dict:
        """Busca en empresas, consolas y juegos según el término de búsqueda."""
        cursor = db.cursor()
        search_term = f"%{query.lower()}%"
        
        result = {
            "companies": [],
            "consoles": [],
            "games": []
        }
        
        # Buscar empresas
        if search_type in ["companies", "all"]:
            companies_query = """
                SELECT DISTINCT e.ID, e.NOMBRE
                FROM EMPRESAS e
                JOIN CONSOLAS c ON e.ID = c.EMPRESA_ID
                JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
                WHERE LOWER(e.NOMBRE) LIKE ? AND IFNULL(jc.RUTA_NUBE, '') != ''
                ORDER BY e.NOMBRE
            """
            cursor.execute(companies_query, (search_term,))
            result["companies"] = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        # Buscar consolas
        if search_type in ["consoles", "all"]:
            consoles_query = """
                SELECT DISTINCT c.ID, c.NOMBRE, c.EMPRESA_ID
                FROM CONSOLAS c
                JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
                WHERE LOWER(c.NOMBRE) LIKE ? AND IFNULL(jc.RUTA_NUBE, '') != ''
                ORDER BY c.NOMBRE
            """
            cursor.execute(consoles_query, (search_term,))
            result["consoles"] = [{"id": row[0], "name": row[1], "company_id": row[2]} for row in cursor.fetchall()]
        
        # Buscar juegos
        if search_type in ["games", "all"]:
            games_query = """
                SELECT DISTINCT j.ID, j.NOMBRE, jc.CONSOLA_ID, j.FECHA_LANZAMIENTO
                FROM JUEGOS j
                JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
                WHERE LOWER(j.NOMBRE) LIKE ? AND IFNULL(jc.RUTA_NUBE, '') != ''
                ORDER BY j.NOMBRE
            """
            cursor.execute(games_query, (search_term,))
            result["games"] = [{
                "id": row[0], 
                "title": row[1], 
                "console_id": row[2], 
                "release_date": row[3]
            } for row in cursor.fetchall()]
        
        return result
    
    @staticmethod
    def get_todas_consolas(db: sqlite3.Connection) -> List[Tuple[int, str, str]]:
        """Obtiene todas las consolas sin filtrar por ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT c.ID, c.NOMBRE, e.NOMBRE as EMPRESA_NOMBRE
            FROM CONSOLAS c
            JOIN EMPRESAS e ON c.EMPRESA_ID = e.ID
            ORDER BY e.NOMBRE, c.NOMBRE
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def get_consolas_por_empresa_todas(db: sqlite3.Connection, empresa_id: int) -> List[Tuple[int, str]]:
        """Obtiene todas las consolas de una empresa sin filtrar por ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT c.ID, c.NOMBRE
            FROM CONSOLAS c
            WHERE c.EMPRESA_ID = ?
            ORDER BY c.NOMBRE
        """
        cursor.execute(query, (empresa_id,))
        return cursor.fetchall()
    
    @staticmethod
    def get_todos_juegos_por_consola(db: sqlite3.Connection, consola_id: int) -> List[Tuple[int, str, Optional[str]]]:
        """Obtiene todos los juegos de una consola que tienen ruta en la nube."""
        cursor = db.cursor()
        query = """
            SELECT j.ID, j.NOMBRE, j.FECHA_LANZAMIENTO
            FROM JUEGOS j
            JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
            WHERE jc.CONSOLA_ID = ? AND IFNULL(jc.RUTA_NUBE, '') != ''
            ORDER BY j.NOMBRE
        """
        cursor.execute(query, (consola_id,))
        return cursor.fetchall()
    
    @staticmethod
    def search_all_general(db: sqlite3.Connection, query: str, search_type: str = "all") -> dict:
        """Busca en empresas, consolas y juegos sin filtrar por ruta en la nube."""
        cursor = db.cursor()
        search_term = f"%{query.lower()}%"
        
        result = {
            "companies": [],
            "consoles": [],
            "games": []
        }
        
        # Buscar empresas
        if search_type in ["companies", "all"]:
            companies_query = """
                SELECT DISTINCT e.ID, e.NOMBRE
                FROM EMPRESAS e
                WHERE LOWER(e.NOMBRE) LIKE ?
                ORDER BY e.NOMBRE
            """
            cursor.execute(companies_query, (search_term,))
            result["companies"] = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        # Buscar consolas
        if search_type in ["consoles", "all"]:
            consoles_query = """
                SELECT DISTINCT c.ID, c.NOMBRE, c.EMPRESA_ID
                FROM CONSOLAS c
                WHERE LOWER(c.NOMBRE) LIKE ?
                ORDER BY c.NOMBRE
            """
            cursor.execute(consoles_query, (search_term,))
            result["consoles"] = [{"id": row[0], "name": row[1], "company_id": row[2]} for row in cursor.fetchall()]
        
        # Buscar juegos
        if search_type in ["games", "all"]:
            games_query = """
                SELECT DISTINCT j.ID, j.NOMBRE, jc.CONSOLA_ID, j.FECHA_LANZAMIENTO
                FROM JUEGOS j
                JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
                WHERE LOWER(j.NOMBRE) LIKE ?
                ORDER BY j.NOMBRE
            """
            cursor.execute(games_query, (search_term,))
            result["games"] = [{
                "id": row[0], 
                "title": row[1], 
                "console_id": row[2], 
                "release_date": row[3]
            } for row in cursor.fetchall()]
        
        return result