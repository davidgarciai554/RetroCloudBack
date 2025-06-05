from fastapi import APIRouter, Depends
from database.database import get_db
from services.game_service import GameService
from models.responses import ConsolaResponse, ConsolaConEmpresaResponse
from typing import List
import sqlite3

router = APIRouter(prefix="/consolas", tags=["consolas"])

@router.get("/empresa/{empresa_id}", response_model=List[ConsolaResponse])
def consolas_por_empresa(empresa_id: int, db: sqlite3.Connection = Depends(get_db)):
    consolas = GameService.get_consolas_por_empresa(db, empresa_id)
    return [{"consola_id": c[0], "nombre": c[1]} for c in consolas]

@router.get("/", response_model=List[ConsolaConEmpresaResponse])
def todas_las_consolas_con_juegos(db: sqlite3.Connection = Depends(get_db)):
    consolas = GameService.get_todas_consolas_con_juegos(db)
    return [
        {
            "consola_id": c[0],
            "consola_nombre": c[1],
            "empresa_nombre": c[2]
        } for c in consolas
    ]