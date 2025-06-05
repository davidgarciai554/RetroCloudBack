from fastapi import FastAPI, Depends, HTTPException, status, Body
from functools import lru_cache
from ext_class.config import Settings
from contextlib import asynccontextmanager
from database.database import init_db, get_db
from ext_class.auth_utils import UserCreate, UserLogin, Token, AuthUtils

import sqlite3
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

def merge_juegos_db():
    import sqlite3
    import os
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
        # Helper to merge any table by matching columns
        def merge_table(table):
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
        # Merge EMPRESAS, CONSOLAS, JUEGOS, JUEGOS_CONSOLAS
        for table in ["EMPRESAS", "CONSOLAS", "JUEGOS", "JUEGOS_CONSOLAS"]:
            merge_table(table)
        conn_main.commit()
    finally:
        conn_main.close()
        conn_juegos.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # crea la DB y tablas si faltan
    merge_juegos_db()  # fusiona la info de juegos.db en database.db
    cfg = get_settings()
    yield  

app = FastAPI(
    title="API de Juegos Retro",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica los orígenes de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@app.get("/getVersion")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "version": settings.version
    }

@app.get("/roles")
async def listar_roles(db: sqlite3.Connection = Depends(get_db)):
    """
    Devuelve todos los roles existentes en la tabla `roles`.
    """
    cursor = db.cursor()
    cursor.execute("SELECT nombre FROM roles;")
    filas = cursor.fetchall()
    return [{ "rol": r[0]} for r in filas]

@app.post("/createUser/", status_code=201)
def crear_usuario(user: UserCreate, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE nombre = ?", (user.nombre,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    # Hashear la contraseña antes de guardarla
    hashed_password = AuthUtils.get_password_hash(user.contraseña)
    cursor.execute(
        "INSERT INTO usuarios (nombre, contraseña, rol_id) VALUES (?, ?, ?)",
        (user.nombre, hashed_password, user.rol_id)
    )
    db.commit()
    return {"msg": "Usuario creado correctamente"}

@app.post("/login", response_model=Token)
def login(user: UserLogin, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, contraseña, rol_id FROM usuarios WHERE nombre = ?", (user.nombre,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    user_id, hashed_password, rol_id = row
    
    # Verificar la contraseña ingresada contra el hash almacenado
    if not AuthUtils.verify_password(user.contraseña, hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    # Obtener el nombre del rol
    cursor.execute("SELECT nombre FROM roles WHERE id = ?", (rol_id,))
    rol_row = cursor.fetchone()
    
    if not rol_row:
        raise HTTPException(status_code=400, detail="Rol no encontrado para el usuario")
    
    rol_nombre = rol_row[0].lower()  # minúsculas para consistencia con el frontend
    access_token = AuthUtils.create_access_token(data={"sub": user.nombre, "user_id": user_id, "role": rol_nombre})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/usuariosRol/{rol}")
def usuarios_por_rol(
    rol: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Devuelve todos los usuarios que tienen el rol especificado en la URL.
    Ejemplo: /usuariosRol/ADMIN
    """
    cursor = db.cursor()
    rol = rol.upper()
    # Busca el ID del rol
    cursor.execute("SELECT id FROM roles WHERE nombre = ?", (rol,))
    rol_row = cursor.fetchone()
    if not rol_row:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    rol_id = rol_row[0]
    # Busca los usuarios con ese rol
    cursor.execute(
        "SELECT u.id, u.nombre FROM usuarios u WHERE u.rol_id = ?",
        (rol_id,)
    )
    usuarios = cursor.fetchall()
    return [{"id": u[0], "nombre": u[1]} for u in usuarios]

@app.get("/empresas")
def empresas_con_juegos_con_route(db: sqlite3.Connection = Depends(get_db)):
    """
    Devuelve las empresas que tengan al menos un juego con ruta en la nube (RUTA_NUBE no vacía).
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT e.ID, e.NOMBRE
        FROM EMPRESAS e
        JOIN CONSOLAS c ON e.ID = c.EMPRESA_ID
        JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
        WHERE IFNULL(jc.RUTA_NUBE, '') != ''
    """
    cursor.execute(query)
    empresas = cursor.fetchall()
    return [{"empresa_id": e[0], "empresa_nombre": e[1]} for e in empresas]

@app.get("/consolas/{empresa_id}")
def consolas_con_juegos_con_route(empresa_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Devuelve las consolas de una empresa que tengan al menos un juego con ruta en la nube (valor distinto a '').
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT c.ID, c.NOMBRE
        FROM CONSOLAS c
        JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
        JOIN JUEGOS j ON jc.JUEGO_ID = j.ID
        WHERE c.EMPRESA_ID = ? AND IFNULL(jc.RUTA_NUBE, '') != ''
    """
    cursor.execute(query, (empresa_id,))
    consolas = cursor.fetchall()
    return [{"consola_id": c[0], "nombre": c[1]} for c in consolas]

@app.get("/juegos")
def juegos_con_route(
    empresa_id: int,
    consola_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Devuelve los juegos de una empresa y consola que tengan ruta en la nube.
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT j.ID, j.NOMBRE, jc.RUTA_NUBE
        FROM JUEGOS j
        JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
        JOIN CONSOLAS c ON jc.CONSOLA_ID = c.ID
        WHERE c.EMPRESA_ID = ? AND c.ID = ? AND jc.RUTA_NUBE IS NOT NULL AND jc.RUTA_NUBE != ''
    """
    cursor.execute(query, (empresa_id, consola_id))
    juegos = cursor.fetchall()
    return [{"juego_id": j[0], "nombre": j[1], "ruta_nube": j[2]} for j in juegos]

@app.get("/juegos/consola/{consola_id}")
def juegos_por_consola(consola_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Devuelve los juegos de una consola por su ID, incluyendo id, nombre, fecha de lanzamiento y descripción.
    """
    cursor = db.cursor()
    query = """
        SELECT j.ID, j.NOMBRE, j.FECHA_LANZAMIENTO
        FROM JUEGOS j
        JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
        WHERE jc.CONSOLA_ID = ?
    """
    cursor.execute(query, (consola_id,))
    juegos = cursor.fetchall()
    return [
        {
            "id": j[0],
            "nombre": j[1],
            "fecha_lanzamiento": j[2]
        } for j in juegos
    ]



load_dotenv()
PRINCIPIO_RUTA = os.getenv("PRINCIPIO_RUTA", "")

@app.post("/registrar_juego")
def registrar_juego(juego_id: int = Body(...), consola_id: int = Body(...), db: sqlite3.Connection = Depends(get_db)):
    """
    Registra un juego asignando una ruta predeterminada en JUEGOS_CONSOLAS.RUTA_NUBE.
    """
    cursor = db.cursor()
    # Obtener nombres
    cursor.execute("SELECT e.NOMBRE, c.NOMBRE, j.NOMBRE FROM JUEGOS j JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID JOIN CONSOLAS c ON jc.CONSOLA_ID = c.ID JOIN EMPRESAS e ON c.EMPRESA_ID = e.ID WHERE j.ID = ? AND c.ID = ?", (juego_id, consola_id))
    row = cursor.fetchone()
    if not row:
        return {"error": "No se encontró la combinación de juego y consola"}
    nombre_empresa, nombre_consola, nombre_juego = row
    nombre_juego = nombre_juego.strip()
    ruta = f"{PRINCIPIO_RUTA}/{nombre_empresa}/{nombre_consola}/{nombre_juego}.zip"
    # Actualizar la ruta en JUEGOS_CONSOLAS
    cursor.execute("UPDATE JUEGOS_CONSOLAS SET RUTA_NUBE = ? WHERE JUEGO_ID = ? AND CONSOLA_ID = ?", (ruta, juego_id, consola_id))
    db.commit()
    return {"ruta": ruta}