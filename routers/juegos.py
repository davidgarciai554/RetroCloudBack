from fastapi import APIRouter, Depends, Body
from database.database import get_db
from services.game_service import GameService
from models.responses import JuegoResponse, RegistroJuegoResponse, ErrorResponse
from typing import List, Union
import sqlite3

router = APIRouter(prefix="/juegos", tags=["juegos"])

@router.get("/consola/{consola_id}", response_model=List[JuegoResponse])
def juegos_por_consola(consola_id: int, db: sqlite3.Connection = Depends(get_db)):
    juegos = GameService.get_juegos_por_consola(db, consola_id)
    return [
        {
            "id": j[0],
            "nombre": j[1],
            "fecha_lanzamiento": j[2]
        } for j in juegos
    ]

@router.get("/all/consola/{consola_id}", response_model=List[JuegoResponse])
def todos_juegos_por_consola(consola_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Obtiene todos los juegos de una consola sin filtrar por ruta en la nube."""
    juegos = GameService.get_todos_juegos_por_consola(db, consola_id)
    return [
        {
            "id": j[0],
            "nombre": j[1],
            "fecha_lanzamiento": j[2]
        } for j in juegos
    ]

@router.post("/registrar", response_model=Union[RegistroJuegoResponse, ErrorResponse])
def registrar_juego(
    juego_id: int = Body(...), 
    consola_id: int = Body(...), 
    db: sqlite3.Connection = Depends(get_db)
):
    ruta = GameService.registrar_juego(db, juego_id, consola_id)
    if not ruta:
        return {"error": "No se encontró la combinación de juego y consola"}
    return {"ruta": ruta}