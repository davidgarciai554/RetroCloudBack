from fastapi import FastAPI, Depends, HTTPException, status
from functools import lru_cache
from ext_class.config import Settings
from contextlib import asynccontextmanager
from database.database import init_db, get_db
from ext_class.auth_utils import UserCreate, UserLogin, Token, AuthUtils

import sqlite3
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware

def merge_juegos_db():
    # Ruta de las bases de datos
    db_main = "database/database.db"
    db_juegos = "database/juegos.db"
    if not os.path.exists(db_juegos):
        return  # No hay nada que migrar

    conn_main = sqlite3.connect(db_main)
    conn_juegos = sqlite3.connect(db_juegos)
    cursor_main = conn_main.cursor()
    cursor_juegos = conn_juegos.cursor()

    # Listar tablas de juegos.db
    cursor_juegos.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [row[0] for row in cursor_juegos.fetchall()]

    for tabla in tablas:
        # Obtener el esquema de la tabla
        cursor_juegos.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tabla}';")
        esquema = cursor_juegos.fetchone()[0]
        try:
            cursor_main.execute(esquema)
        except sqlite3.OperationalError:
            pass  # La tabla ya existe

        # Copiar los datos
        cursor_juegos.execute(f"SELECT * FROM {tabla}")
        filas = cursor_juegos.fetchall()
        if filas:
            placeholders = ",".join(["?"] * len(filas[0]))
            try:
                cursor_main.executemany(f"INSERT OR IGNORE INTO {tabla} VALUES ({placeholders})", filas)
            except Exception:
                pass  # Si hay conflicto de columnas, ignora

    conn_main.commit()
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
    Devuelve las empresas que tengan al menos un juego con route distinto de NULL.
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT c.NOMBRE
        FROM CONSOLAS c
        JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
        JOIN JUEGOS j ON jc.JUEGO_ID = j.ID
        WHERE j.ROUTE IS NOT NULL
    """
    cursor.execute(query)
    empresas = cursor.fetchall()
    return [{"empresa_id": e[0]} for e in empresas]

@app.get("/consolas/{empresa_id}")
def consolas_con_juegos_con_route(empresa_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Devuelve las consolas de una empresa que tengan al menos un juego con route distinto de NULL.
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT c.ID, c.NOMBRE
        FROM CONSOLAS c
        JOIN JUEGOS_CONSOLAS jc ON c.ID = jc.CONSOLA_ID
        JOIN JUEGOS j ON jc.JUEGO_ID = j.ID
        WHERE c.EMPRESA_ID = ? AND j.ROUTE IS NOT NULL
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
    Devuelve los juegos de una empresa y consola que tengan route distinto de NULL.
    """
    cursor = db.cursor()
    query = """
        SELECT DISTINCT j.ID, j.NOMBRE, j.ROUTE
        FROM JUEGOS j
        JOIN JUEGOS_CONSOLAS jc ON j.ID = jc.JUEGO_ID
        JOIN CONSOLAS c ON jc.CONSOLA_ID = c.ID
        WHERE c.EMPRESA_ID = ? AND c.ID = ? AND j.ROUTE IS NOT NULL
    """
    cursor.execute(query, (empresa_id, consola_id))
    juegos = cursor.fetchall()
    return [{"juego_id": j[0], "nombre": j[1], "route": j[2]} for j in juegos]