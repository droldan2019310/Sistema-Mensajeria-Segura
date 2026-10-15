from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
import httpx
from sqlalchemy import text

from src.auth import modelos
from src.blockchain import modelos as modelosBlockchain
from src.blockchain.rutas import routerBlockchain
from src.blockchain.servicio import asegurarBloqueGenesis
from src.contacts import modelos as modelosContacts
from src.contacts.rutas import routerContacts
from src.crypto import modelos as modelosCrypto
from src.auth.baseDatos import Base, SesionLocal, motorBaseDatos
from src.auth.configuracion import configuracion
from src.auth.esquemas import EstadoServicioSalida
from src.auth.rutas import routerAuth
from src.crypto.rutas import routerMessages
from src.users.rutas import routerUsers


URL_SALUD_EXTERNA = "https://example.com"


Base.metadata.create_all(bind=motorBaseDatos)


# Inicializa recursos base del sistema
@asynccontextmanager
async def cicloVida(app: FastAPI):
    sesion = SesionLocal()
    try:
        asegurarBloqueGenesis(sesion)
        yield
    finally:
        sesion.close()


app = FastAPI(
    title=configuracion.APPNombre,
    version=configuracion.APIVersion,
    lifespan=cicloVida,
)


@app.middleware("http")
async def agregar_cabeceras_seguridad(request, call_next):
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    return respuesta


app.include_router(routerAuth)
app.include_router(routerUsers)
app.include_router(routerMessages)
app.include_router(routerBlockchain)
app.include_router(routerContacts)


# Verifica que la API este activa
@app.get("/", response_model=EstadoServicioSalida)
def inicio():
    return EstadoServicioSalida(
        estado="ok", servicio=configuracion.APPNombre, version=configuracion.APIVersion
    )


# Verifica conexion con base de datos
@app.get("/salud/db")
def saludBaseDatos():
    sesion = SesionLocal()
    try:
        sesion.execute(text("SELECT 1"))
        return {"estado": "ok", "baseDatos": "conectada"}
    finally:
        sesion.close()


@app.get(
    "/salud/externa",
    responses={503: {"description": "Servicio externo no disponible"}},
)
def saludExterna():
    try:
        respuesta = httpx.get(URL_SALUD_EXTERNA, timeout=5.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio externo no disponible")
    return {"estado": "ok" if respuesta.is_success else "error"}
