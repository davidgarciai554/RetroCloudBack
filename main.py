from fastapi import FastAPI, Depends 
from functools import lru_cache
from config import Settings
from contextlib import asynccontextmanager
from database.database import init_db, get_db
import sqlite3

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # crea la DB y tablas si faltan
    yield  

app = FastAPI(
    title="API de Juegos Retro",
    lifespan=lifespan
)

@app.on_event("startup")
async def startup_event():
    cfg = get_settings()

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