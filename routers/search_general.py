from fastapi import APIRouter, Depends, Query
from database.database import get_db
from services.game_service import GameService
from models.responses import SearchCompanyResponse, SearchConsoleResponse, SearchGameResponse
from typing import List
import sqlite3

router = APIRouter(prefix="/search-general", tags=["search-general"])

@router.get("/all")
def search_all_general(
    q: str = Query(..., description="Término de búsqueda"),
    type: str = Query("all", description="Tipo de búsqueda: all, companies, consoles, games"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Busca en empresas, consolas y juegos sin filtrar por ruta en la nube."""
    return GameService.search_all_general(db, q, type)