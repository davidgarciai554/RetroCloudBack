from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import sqlite3

from services.database_service import DatabaseService
from services.game_service import GameService
from models.responses import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Término de búsqueda"),
    type: Optional[str] = Query("all", regex="^(games|companies|consoles|all)$", description="Filtro de tipo de búsqueda")
):
    """
    Busca en empresas, consolas y juegos según el término proporcionado.
    
    - **q**: Término de búsqueda (obligatorio)
    - **type**: Filtro opcional (games, companies, consoles, all)
    
    Retorna un objeto con arrays de empresas, consolas y juegos que coinciden con la búsqueda.
    Solo incluye elementos que tienen juegos con ruta en la nube.
    """
    try:
        db = DatabaseService.get_db_connection()
        results = GameService.search_all(db, q, type)
        db.close()
        
        return SearchResponse(
            companies=results["companies"],
            consoles=results["consoles"],
            games=results["games"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {str(e)}")