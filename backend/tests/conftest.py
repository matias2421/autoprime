# -*- coding: utf-8 -*-
"""Montaje de las pruebas.

**Por qué SQLite y no la base de verdad.** `pruebas_api.py` habla con un
servidor en marcha contra MySQL, y eso está bien para comprobar que el
despliegue entero funciona. Pero como única red de seguridad es mala: tarda,
necesita que alguien encienda cosas antes, y cada corrida deja filas que hay
que limpiar —o que descuadran la siguiente—. Una prueba que ensucia el estado
compartido acaba fallando por lo que hizo la prueba anterior, y entonces
nadie se fía de ella.

Estas corren contra una base en memoria que nace y muere con cada prueba. Sin
servidor, sin red y sin limpieza: la prueba que falla, falla por lo que mide.

**Lo que este montaje NO cubre, dicho claramente.** SQLite no es MySQL: no
comprueba los tipos ENUM, ni el comportamiento exacto de las claves ajenas,
ni que el esquema real tenga las columnas que el modelo declara. Eso lo
cubren `pruebas_api.py` contra MySQL y el cotejo de modelos contra el esquema.
Las dos capas se necesitan; ninguna sustituye a la otra.

El truco que lo hace posible es que las consultas están escritas en SQL
estándar. Mientras usaban `IF()` y `FIELD()` —que solo existen en MySQL— esto
no se podía hacer.
"""

import asyncio
import sys
import warnings

import pytest
import pytest_asyncio

if sys.platform == "win32":
    # Lo mismo que hace `servidor.py`, y por lo mismo: en Windows el bucle
    # por defecto no levanta TLS. Aquí no hay TLS, pero conviene que las
    # pruebas corran sobre el mismo bucle que la aplicación real.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core import limitador  # noqa: E402
from app.core.base_datos import Base, obtener_sesion  # noqa: E402
from app.core.seguridad import hashear_contrasena  # noqa: E402
from app.main import app  # noqa: E402
from app.models.autoprime import (  # noqa: E402
    Permiso,
    Producto,
    Rol,
    Servicio,
    Usuario,
)

CLAVES = {
    "administrador": "Admin2026!",
    "empleado": "Empleado2026!",
    "cliente": "Cliente2026!",
}


@pytest.fixture(autouse=True)
def freno_limpio():
    """Cada prueba arranca con el contador de peticiones a cero.

    El limitador vive en la memoria del proceso y las pruebas comparten
    proceso: sin esto, el `fixture` de tokens —que inicia sesion tres veces
    por prueba— agota el cupo del login a la tercera prueba y todo lo demas
    falla con un 429 que no tiene nada que ver con lo que se estaba
    midiendo.

    Que haya hecho falta es, de paso, la prueba de que el freno funciona.
    """
    limitador.reiniciar()
    yield
    limitador.reiniciar()


@pytest_asyncio.fixture
async def motor():
    """Una base en memoria por prueba, con el esquema de los modelos.

    `StaticPool` y una sola conexión: SQLite en memoria vive dentro de la
    conexión que lo creó, así que con un pool normal cada consulta abriría
    una base distinta —y vacía— sin dar ningún error.
    """
    motor = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with motor.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)

    yield motor

    await motor.dispose()


@pytest_asyncio.fixture
async def sesion(motor):
    fabrica = async_sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)
    async with fabrica() as sesion:
        yield sesion


@pytest_asyncio.fixture
async def datos(sesion):
    """Lo mínimo para que el dominio tenga sentido: roles, gente y catálogo."""
    roles = {
        nombre: Rol(nombre=nombre, descripcion=f"Rol de {nombre}")
        for nombre in ("administrador", "empleado", "cliente")
    }
    sesion.add_all(roles.values())
    sesion.add(Permiso(nombre="ventas.crear", descripcion="Registrar ventas"))
    await sesion.flush()

    usuarios = {}
    for nombre, rol in roles.items():
        usuario = Usuario(
            nombre=nombre.capitalize(),
            apellido="De Prueba",
            tipo_documento="CC",
            numero_documento=f"10{len(usuarios)}00000{len(usuarios)}",
            direccion="Calle 1 # 2-3",
            telefono="3001112233",
            correo=f"{nombre}@autoprime.com.co",
            password_hash=hashear_contrasena(CLAVES[nombre]),
            rol_id=rol.id,
        )
        usuarios[nombre] = usuario
    sesion.add_all(usuarios.values())

    # Dos vehículos a propósito: uno con precio de lista y otro bajo consulta,
    # que son los dos caminos distintos al armar una línea de venta.
    productos = [
        Producto(
            slug="phantom-viii",
            marca="MANSORY",
            modelo="Phantom VIII",
            familia="gama",
            base="Rolls-Royce Phantom",
            lema="El silencio, amplificado",
            descripcion="Una berlina reinterpretada por MANSORY.",
            imagen="phantom.webp",
            anio=2024,
            precio=3_200_000_000,
            motor="V12 biturbo",
            potencia="610 hp",
            aceleracion="5.1 s",
            velocidad="250 km/h",
            transmision="Automatica de 8",
            traccion="Trasera",
        ),
        Producto(
            slug="art-piece",
            marca="MANSORY",
            modelo="Art Piece AL3C",
            familia="coleccion",
            base="Pieza unica",
            lema="Una sola en el mundo",
            descripcion="Pieza de coleccion sin precio de lista.",
            imagen="artpiece.webp",
            anio=2024,
            precio=None,
            unidades=1,
            motor="V12",
            potencia="1000 hp",
            aceleracion="2.8 s",
            velocidad="350 km/h",
            transmision="Automatica de 7",
            traccion="Integral",
        ),
    ]
    servicios = [
        Servicio(
            nombre="Peritaje de 120 puntos",
            descripcion="Revision completa",
            duracion_min=120,
            precio=350_000,
        ),
        Servicio(
            nombre="Prueba de manejo",
            descripcion="Una hora con el vehiculo",
            duracion_min=60,
            precio=0,
        ),
    ]
    sesion.add_all(productos + servicios)
    await sesion.commit()

    for objeto in [*usuarios.values(), *productos, *servicios]:
        await sesion.refresh(objeto)

    return {
        "roles": roles,
        "usuarios": usuarios,
        "productos": productos,
        "servicios": servicios,
    }


@pytest_asyncio.fixture
async def cliente(motor, datos):
    """Cliente HTTP que habla con la aplicación sin levantar un servidor.

    `ASGITransport` llama a la aplicación directamente, en el mismo proceso.
    No hay puerto, ni socket, ni espera a que algo arranque; y el fallo, si
    lo hay, sale con su traza completa en vez de como un 500 opaco.
    """
    fabrica = async_sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)

    async def sesion_de_prueba():
        async with fabrica() as sesion:
            yield sesion

    app.dependency_overrides[obtener_sesion] = sesion_de_prueba

    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://pruebas") as http:
        yield http

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tokens(cliente, datos):
    """Un token por rol, listo para usar en las cabeceras."""
    salida = {}
    for nombre, clave in CLAVES.items():
        respuesta = await cliente.post(
            "/api/auth/login",
            json={"correo": f"{nombre}@autoprime.com.co", "password": clave},
        )
        assert respuesta.status_code == 200, respuesta.text
        salida[nombre] = respuesta.json()["token"]
    return salida


@pytest.fixture
def como(tokens):
    """`como("administrador")` devuelve la cabecera de autorización."""

    def cabecera(rol: str) -> dict:
        return {"Authorization": f"Bearer {tokens[rol]}"}

    return cabecera
