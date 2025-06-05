from fastapi import APIRouter, Depends, HTTPException
from database.database import get_db
from models.responses import UsuarioResponse
from typing import List
import sqlite3

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.get("/rol/{rol}", response_model=List[UsuarioResponse])
def usuarios_por_rol(rol: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    rol = rol.upper()
    cursor.execute("SELECT id FROM roles WHERE nombre = ?", (rol,))
    rol_row = cursor.fetchone()
    if not rol_row:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    rol_id = rol_row[0]
    cursor.execute(
        "SELECT u.id, u.nombre FROM usuarios u WHERE u.rol_id = ?",
        (rol_id,)
    )
    usuarios = cursor.fetchall()
    return [{"id": u[0], "nombre": u[1]} for u in usuarios]