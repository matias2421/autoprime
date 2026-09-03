"""AutoPrime API — aplicación principal.

Cuarto avance: el backend pasa de Express a FastAPI conservando el mismo
dominio, la misma base de datos MySQL y las mismas rutas, de modo que el
frontend en React apenas cambia.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.base_datos import comprobar_conexion
from app.core.configuracion import configuracion
from app.errores import (
    ConflictoDeNegocio,
    DatosInvalidos,
    ErrorDeDominio,
    NoAutenticado,
    PermisoDenegado,
    RecursoNoEncontrado,
)
from app.dependencias import SesionDep
from app.models import autoprime  # noqa: F401 — registra las tablas en Base
from app.routers import auth, citas, productos, servicios, usuarios

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("autoprime")

TAGS = [
    {"name": "Autenticación", "description": "Registro, inicio de sesión y perfil."},
    {"name": "Usuarios", "description": "Gestión de cuentas y roles."},
    {"name": "Productos", "description": "Catálogo de vehículos."},
    {"name": "Servicios", "description": "Servicios que ofrece el taller."},
    {"name": "Citas", "description": "Agenda de visitas y pruebas."},
    {"name": "Sistema", "description": "Estado del servicio."},
]

app = FastAPI(
    title=configuracion.nombre_app,
    version=configuracion.version,
    description=(
        "API REST del atelier AutoPrime. Autenticación con JWT, control por "
        "roles (administrador, empleado y cliente) y CRUD sobre MySQL."
    ),
    openapi_tags=TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

# El frontend de Vite corre en otro puerto, así que toda petición del
# navegador es de origen cruzado y necesita esta autorización explícita.
app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.origenes_permitidos,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# --------------------------- Manejadores de error ---------------------------
#
# Todos los errores salen con la misma forma, venga de donde venga el fallo:
# {codigo, mensaje, ruta, detalles}. El frontend decide con `codigo`, que es
# estable, y muestra `mensaje`, que está redactado para leerse.


def _respuesta(estado: int, codigo: str, mensaje: str, ruta: str, detalles=None):
    return JSONResponse(
        status_code=estado,
        content={
            "codigo": codigo,
            "mensaje": mensaje,
            "ruta": ruta,
            "detalles": detalles,
        },
    )


@app.exception_handler(RecursoNoEncontrado)
def _no_encontrado(peticion: Request, error: RecursoNoEncontrado):
    return _respuesta(
        status.HTTP_404_NOT_FOUND, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(ConflictoDeNegocio)
def _conflicto(peticion: Request, error: ConflictoDeNegocio):
    return _respuesta(
        status.HTTP_409_CONFLICT, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(NoAutenticado)
def _no_autenticado(peticion: Request, error: NoAutenticado):
    return _respuesta(
        status.HTTP_401_UNAUTHORIZED, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(PermisoDenegado)
def _sin_permiso(peticion: Request, error: PermisoDenegado):
    return _respuesta(
        status.HTTP_403_FORBIDDEN, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(DatosInvalidos)
def _datos_invalidos(peticion: Request, error: DatosInvalidos):
    return _respuesta(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        error.codigo,
        error.mensaje,
        peticion.url.path,
    )


@app.exception_handler(ErrorDeDominio)
def _error_dominio(peticion: Request, error: ErrorDeDominio):
    """Red de seguridad para cualquier error de negocio sin manejador propio."""
    return _respuesta(
        status.HTTP_400_BAD_REQUEST, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(RequestValidationError)
def _validacion(peticion: Request, error: RequestValidationError):
    """Traduce los errores de Pydantic al formato de la API.

    Se aplana `loc` al último elemento porque es el nombre del campo, que es
    lo único que el formulario necesita para marcar el input correcto.
    """
    detalles = [
        {
            "campo": str(fallo["loc"][-1]) if fallo.get("loc") else "cuerpo",
            "problema": fallo.get("msg", "Valor no válido."),
        }
        for fallo in error.errors()
    ]
    return _respuesta(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "datos_invalidos",
        "Los datos enviados no cumplen el formato esperado.",
        peticion.url.path,
        detalles,
    )


@app.exception_handler(SQLAlchemyError)
def _error_base_datos(peticion: Request, error: SQLAlchemyError):
    """No se filtra el detalle del error de SQL: puede revelar el esquema."""
    logger.error("Error de base de datos en %s: %s", peticion.url.path, error)
    return _respuesta(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error_base_datos",
        "No se pudo completar la operación en la base de datos.",
        peticion.url.path,
    )


# --------------------------------- Rutas ------------------------------------

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(servicios.router)
app.include_router(citas.router)


@app.get("/", tags=["Sistema"], summary="Presentación de la API")
def raiz():
    return {
        "ok": True,
        "api": configuracion.nombre_app,
        "version": configuracion.version,
        "documentacion": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "usuarios": "/api/usuarios",
            "productos": "/api/productos",
            "servicios": "/api/servicios",
            "citas": "/api/citas",
        },
    }


@app.get("/salud", tags=["Sistema"], summary="Estado del servicio")
def salud(sesion: SesionDep):
    comprobar_conexion(sesion)
    return {"ok": True, "base_datos": "conectada", "entorno": configuracion.entorno}
