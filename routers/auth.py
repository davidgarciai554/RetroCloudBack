from fastapi import APIRouter, Depends, HTTPException, Body
from database.database import get_db
from ext_class.auth_utils import UserCreate, UserLogin, Token, AuthUtils
from models.responses import UsuarioResponse, RolResponse
from typing import List
import sqlite3

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", status_code=201)
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

@router.post("/login", response_model=Token)
def login(user: UserLogin, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, contraseña, rol_id FROM usuarios WHERE nombre = ?", (user.nombre,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    user_id, hashed_password, rol_id = row
    
    if not AuthUtils.verify_password(user.contraseña, hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    cursor.execute("SELECT nombre FROM roles WHERE id = ?", (rol_id,))
    rol_row = cursor.fetchone()
    
    if not rol_row:
        raise HTTPException(status_code=400, detail="Rol no encontrado para el usuario")
    
    rol_nombre = rol_row[0].lower()
    access_token = AuthUtils.create_access_token(data={"sub": user.nombre, "user_id": user_id, "role": rol_nombre})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/roles", response_model=List[RolResponse])
def listar_roles(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT nombre FROM roles;")
    filas = cursor.fetchall()
    return [{"rol": r[0]} for r in filas]