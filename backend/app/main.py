"""AutoPrime API — aplicación principal.

Cuarto avance: el backend pasa de Express a FastAPI conservando el mismo
dominio, la misma base de datos MySQL y las mismas rutas, de modo que el
frontend en React apenas cambia.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core import asistente
from app.core.cabeceras import CabecerasDeSeguridad
from app.core.base_datos import comprobar_conexion, motor
from app.core.configuracion import configuracion
from app.errores import (
    ConflictoDeNegocio,
    DatosInvalidos,
    ErrorDeDominio,
    NoAutenticado,
    PermisoDenegado,
    DemasiadasPeticiones,
    RecursoNoEncontrado,
    ServicioExternoCaido,
)
from app.dependencias import SesionDep
from app.models import autoprime  # noqa: F401 — registra las tablas en Base
from app.routers import (
    auth,
    chat,
    citas,
    facturas,
    pqr,
    productos,
    reportes,
    servicios,
    usuarios,
    ventas,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("autoprime")

# A partir de aqui una peticion se considera lenta y se anota. Medio
# segundo es mucho para una consulta y poco para armar un PDF de un mes,
# que es justo lo que se quiere ver en el registro.
UMBRAL_LENTO = 0.5

TAGS = [
    {"name": "Autenticación", "description": "Registro, inicio de sesión y perfil."},
    {"name": "Usuarios", "description": "Gestión de cuentas y roles."},
    {"name": "Productos", "description": "Catálogo de vehículos."},
    {"name": "Servicios", "description": "Servicios que ofrece el taller."},
    {"name": "Citas", "description": "Agenda de visitas y pruebas."},
    {"name": "Ventas", "description": "Registro de ventas y su detalle."},
    {"name": "Facturas", "description": "Emisión y consulta de facturas."},
    {"name": "Reportes", "description": "Tableros y descargas en PDF y Excel."},
    {"name": "PQR", "description": "Peticiones, quejas, reclamos y sugerencias."},
    {"name": "Asistente", "description": "Chat con el asistente virtual."},
    {"name": "Sistema", "description": "Estado del servicio."},
]


@asynccontextmanager
async def ciclo_de_vida(aplicacion: FastAPI):
    """Lo que se abre al arrancar y se cierra al apagar.

    El resumen de arranque no es decoración. La mitad de los fallos de un
    despliegue son «faltaba una variable de entorno», y eso se descubre —si
    no se dice aquí— cuando alguien intenta recuperar su contraseña y no le
    llega nada. Decirlo en la primera línea del registro convierte media hora
    de búsqueda en una ojeada.

    El cierre importa por la razón contraria: sin soltar el pool de la base y
    el cliente HTTP, al apagar quedan conexiones a medio cerrar y el registro
    se llena de errores del recolector que no significan nada y esconden los
    que sí.
    """
    # Separador ASCII: la consola de Windows no dibuja el punto medio y lo
    # sustituye por un interrogante en la primera linea del registro.
    logger.info("%s %s | entorno: %s", configuracion.nombre_app,
                configuracion.version, configuracion.entorno)
    logger.info("Origenes permitidos: %s", ", ".join(configuracion.origenes))
    logger.info(
        "Correo saliente: %s",
        configuracion.smtp_host or "sin configurar (los enlaces van al registro)",
    )
    logger.info(
        "Asistente: %s",
        f"activo con {configuracion.groq_modelo}"
        if asistente.disponible()
        else "sin clave (el chat ofrecera la PQR como alternativa)",
    )

    yield

    await asistente.cerrar()
    await motor.dispose()
    logger.info("Conexiones cerradas. Hasta luego.")


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
    lifespan=ciclo_de_vida,
)

# --------------------------- Middleware propio ------------------------------
#
# Corre alrededor de TODA petición, incluidas las que ni siquiera llegan a un
# endpoint —una ruta que no existe, un cuerpo que no valida—. Ahí está su
# utilidad: es el único sitio desde el que se ve lo que realmente entra.


@app.middleware("http")
async def registrar_peticion(peticion: Request, siguiente):
    """Marca cada petición y mide lo que tarda.

    Dos problemas concretos resuelve.

    El primero: cuando algo falla en producción, el registro tiene veinte
    líneas de cuatro peticiones entrelazadas y no hay forma de saber cuáles
    van juntas. Con un identificador por petición, sí: se filtra por él y
    queda solo su historia. El mismo identificador viaja en la respuesta, así
    que quien reporta un fallo puede decir cuál fue el suyo.

    El segundo: sin medir, «va lento» es una opinión. Con el tiempo en cada
    respuesta y un aviso automático al pasar del umbral, es un dato y además
    señala qué endpoint concreto.
    """
    identificador = uuid.uuid4().hex[:8]
    peticion.state.identificador = identificador

    comienzo = time.perf_counter()
    respuesta = await siguiente(peticion)
    duracion = time.perf_counter() - comienzo

    respuesta.headers["X-Peticion-Id"] = identificador
    respuesta.headers["X-Tiempo-Respuesta"] = f"{duracion * 1000:.0f}ms"

    # Solo se registra lo que merece mirarse: los errores y lo que tarda. Un
    # registro que anota los doscientos GET que van bien es un registro que
    # nadie lee, y entonces tampoco se leen las líneas que importan.
    if respuesta.status_code >= 400 or duracion > UMBRAL_LENTO:
        logger.info(
            "[%s] %s %s -> %s en %.0f ms",
            identificador,
            peticion.method,
            peticion.url.path,
            respuesta.status_code,
            duracion * 1000,
        )

    return respuesta


# Cabeceras de seguridad en TODA respuesta, incluidas las de error y las de
# archivo. Va antes que CORS en el codigo, asi que Starlette lo envuelve por
# fuera y alcanza tambien a las respuestas que CORS genera por su cuenta,
# como la de una peticion preflight. Ver `app/core/cabeceras.py`.
app.add_middleware(CabecerasDeSeguridad)

# El frontend de Vite corre en otro puerto, así que toda petición del
# navegador es de origen cruzado y necesita esta autorización explícita.
app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.origenes,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    # Sin exponerlas, el navegador se las oculta a JavaScript por venir de
    # otro origen, y el identificador que sirve para reportar un fallo no
    # llegaria nunca a quien tiene el fallo delante.
    expose_headers=["Content-Disposition", "X-Peticion-Id", "Retry-After"],
)


# --------------------------- Manejadores de error ---------------------------
#
# Todos los errores salen con la misma forma, venga de donde venga el fallo:
# {codigo, mensaje, ruta, detalles}. El frontend decide con `codigo`, que es
# estable, y muestra `mensaje`, que está redactado para leerse.


def _respuesta(
    estado: int, codigo: str, mensaje: str, ruta: str, detalles=None, cabeceras=None
):
    return JSONResponse(
        status_code=estado,
        content={
            "codigo": codigo,
            "mensaje": mensaje,
            "ruta": ruta,
            "detalles": detalles,
        },
        headers=cabeceras,
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
    """El 401 lleva `WWW-Authenticate`, que es lo que lo distingue del 403.

    Sin esa cabecera, un 401 es solo un número: la norma HTTP dice que una
    respuesta 401 tiene que indicar con qué esquema autenticarse, y es lo que
    permite a un cliente genérico —Postman, un `curl`, la propia página de
    `/docs`— saber que debe pedir un token en vez de rendirse.
    """
    return _respuesta(
        status.HTTP_401_UNAUTHORIZED,
        error.codigo,
        error.mensaje,
        peticion.url.path,
        cabeceras={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(PermisoDenegado)
def _sin_permiso(peticion: Request, error: PermisoDenegado):
    return _respuesta(
        status.HTTP_403_FORBIDDEN, error.codigo, error.mensaje, peticion.url.path
    )


@app.exception_handler(DatosInvalidos)
def _datos_invalidos(peticion: Request, error: DatosInvalidos):
    return _respuesta(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "datos_invalidos",
        "Los datos enviados no cumplen el formato esperado.",
        peticion.url.path,
        detalles,
    )


@app.exception_handler(DemasiadasPeticiones)
def _demasiadas(peticion: Request, error: DemasiadasPeticiones):
    """429 con `Retry-After`.

    Sin esa cabecera, quien llama solo sabe que le dijeron que no, y lo que
    hace entonces es reintentar de inmediato: el freno acaba generando más
    peticiones de las que evita.
    """
    return _respuesta(
        status.HTTP_429_TOO_MANY_REQUESTS,
        error.codigo,
        error.mensaje,
        peticion.url.path,
        cabeceras={"Retry-After": str(error.espera)},
    )


@app.exception_handler(ServicioExternoCaido)
def _servicio_externo(peticion: Request, error: ServicioExternoCaido):
    """503, no 500: el fallo no es nuestro y reintentar puede funcionar."""
    logger.warning("Proveedor externo sin responder: %s", error.servicio)
    return _respuesta(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        error.codigo,
        error.mensaje,
        peticion.url.path,
    )


@app.exception_handler(IntegrityError)
def _integridad(peticion: Request, error: IntegrityError):
    """Una restricción de la base rechazó la escritura. → 409, no 500.

    Es un conflicto de datos —un correo repetido, un consecutivo que ya
    existe—, no una avería: el 500 le diría al cliente que el fallo es del
    servidor y que no tiene sentido cambiar nada, cuando es justo al revés.

    El texto del error de MySQL no sale: nombra la tabla y el índice, y eso
    es el esquema. Queda en el log, que es donde hace falta.
    """
    logger.warning("Integridad rechazada en %s: %s", peticion.url.path, error.orig)
    return _respuesta(
        status.HTTP_409_CONFLICT,
        "conflicto_de_integridad",
        "Los datos chocan con un registro que ya existe.",
        peticion.url.path,
    )


@app.exception_handler(SQLAlchemyError)
def _error_base_datos(peticion: Request, error: SQLAlchemyError):
    """No se filtra el detalle del error de SQL: puede revelar el esquema."""
    logger.error(
        "Error de base de datos en %s: %s", peticion.url.path, error, exc_info=True
    )
    return _respuesta(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error_base_datos",
        "No se pudo completar la operación en la base de datos.",
        peticion.url.path,
    )


@app.exception_handler(Exception)
def _fallo_inesperado(peticion: Request, error: Exception):
    """Lo que nadie previó. El cliente recibe poco; el log, todo.

    Sin este manejador, una excepción sin capturar sale con el formato de
    Starlette y no con el de la API, así que el frontend —que lee `codigo`—
    se encuentra un cuerpo que no sabe interpretar justo en el peor momento.

    La traza va al log con `exc_info`, no al cuerpo: un rastro de pila dice
    rutas del servidor, versiones y a veces datos de la petición. Y va con
    un identificador que sí se le entrega a quien llama, para que pueda
    decir «me falló la operación 7f3a…» y eso baste para encontrar el caso
    exacto en el log sin adivinar por la hora.
    """
    referencia = uuid.uuid4().hex[:8]
    logger.exception(
        "Fallo no controlado [%s] en %s %s",
        referencia,
        peticion.method,
        peticion.url.path,
    )
    return _respuesta(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "error_interno",
        f"Ocurrió un error inesperado. Referencia: {referencia}.",
        peticion.url.path,
    )


# --------------------------------- Rutas ------------------------------------

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(servicios.router)
app.include_router(citas.router)
app.include_router(ventas.router)
app.include_router(facturas.router)
app.include_router(reportes.router)
app.include_router(pqr.router)
app.include_router(chat.router)


@app.get("/", tags=["Sistema"], summary="Presentación de la API")
async def raiz():
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
            "ventas": "/api/ventas",
            "facturas": "/api/facturas",
            "reportes": "/api/reportes",
            "pqr": "/api/pqr",
            "chat": "/api/chat",
        },
    }


@app.get("/salud", tags=["Sistema"], summary="Estado del servicio")
async def salud(sesion: SesionDep):
    """Lo que Render consulta para saber si el servicio esta sano.

    Comprueba la conexion de verdad, no solo que el proceso responda: si la
    base cae, el panel del proveedor lo refleja en lugar de dar el servicio
    por bueno. Y dice como va el cifrado del enlace, que es la unica forma de
    confirmar desde fuera que el certificado llego al despliegue.
    """
    await comprobar_conexion(sesion)
    return {
        "ok": True,
        "base_datos": "conectada",
        "cifrado": configuracion.modo_cifrado,
        "entorno": configuracion.entorno,
    }
