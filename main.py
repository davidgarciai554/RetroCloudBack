from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from functools import lru_cache

from ext_class.config import Settings
from database.database import init_db
from services.database_service import DatabaseService

# Importar routers
from routers import auth, empresas, consolas, juegos, usuarios, search, search_general

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    init_db()
    DatabaseService.merge_juegos_db()
    yield

app = FastAPI(
    title="API de Juegos Retro",
    description="API para gestionar juegos retro con autenticación y rutas en la nube",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(empresas.router)
app.include_router(consolas.router)
app.include_router(juegos.router)
app.include_router(search.router)
app.include_router(search_general.router)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@app.get("/")
async def root():
    return {"message": "API de Juegos Retro - Funcionando correctamente"}

@app.get("/version")
async def get_version(settings: Settings = Depends(get_settings)):
    return {"version": settings.version}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}