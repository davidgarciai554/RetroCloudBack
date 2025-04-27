from fastapi import FastAPI, Depends, HTTPException, status
from functools import lru_cache
from ext_class.config import Settings
from contextlib import asynccontextmanager
from database.database import init_db, get_db
from ext_class.auth_utils import UserCreate, UserLogin, Token, AuthUtils

import sqlite3

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # crea la DB y tablas si faltan
    cfg = get_settings()
    yield  

app = FastAPI(
    title="API de Juegos Retro",
    lifespan=lifespan
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
    cursor.execute("SELECT id, contraseña FROM usuarios WHERE nombre = ?", (user.nombre,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    user_id, hashed_password = row
    if not AuthUtils.verify_password(user.contraseña, hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    access_token = AuthUtils.create_access_token(data={"sub": user.nombre, "user_id": user_id})
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