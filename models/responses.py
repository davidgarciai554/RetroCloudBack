from pydantic import BaseModel
from typing import Optional

class EmpresaResponse(BaseModel):
    empresa_id: int
    empresa_nombre: str

class ConsolaResponse(BaseModel):
    consola_id: int
    nombre: str

class ConsolaConEmpresaResponse(BaseModel):
    consola_id: int
    consola_nombre: str
    empresa_nombre: str

class JuegoResponse(BaseModel):
    id: int
    nombre: str
    fecha_lanzamiento: Optional[str]

class UsuarioResponse(BaseModel):
    id: int
    nombre: str

class RolResponse(BaseModel):
    rol: str

class RegistroJuegoResponse(BaseModel):
    ruta: str

class ErrorResponse(BaseModel):
    error: str