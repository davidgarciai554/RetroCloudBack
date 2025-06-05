from fastapi import APIRouter, Depends
from database.database import get_db
from services.game_service import GameService
from models.responses import EmpresaResponse
from typing import List
import sqlite3

router = APIRouter(prefix="/empresas", tags=["empresas"])

@router.get("/", response_model=List[EmpresaResponse])
def empresas_con_juegos_con_route(db: sqlite3.Connection = Depends(get_db)):
    empresas = GameService.get_empresas_con_juegos(db)
    return [{"empresa_id": e[0], "empresa_nombre": e[1]} for e in empresas]