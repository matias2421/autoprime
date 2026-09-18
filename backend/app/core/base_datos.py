"""Conexión a la base de datos con SQLAlchemy, en asíncrono.

Una petición web pasa la mayor parte de su vida esperando: a la base, al
servidor de correo, al proveedor de turno. Con el motor síncrono cada una de
esas esperas bloquea un hilo entero; con el asíncrono, el proceso atiende otras
mientras tanto. En una máquina pequeña —el plan gratuito de Render tiene una
sola CPU— esa diferencia es la que separa atender a treinta personas de
atender a tres.

El precio es que ahora toda la cadena tiene que ser asíncrona: si una sola
función de `crud` se queda síncrona y bloquea, frena el bucle entero y el
resto de peticiones se quedan esperando sin que nada lo delate.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.configuracion import configuracion

motor = create_async_engine(
    configuracion.url_base_datos,
    echo=False,
    # El cifrado del enlace con la base. En local va vacío; contra un proveedor
    # remoto lleva el contexto TLS armado con su certificado.
    connect_args=configuracion.conexion_args,
    # MySQL cierra las conexiones que llevan rato inactivas. Sin estas dos
    # opciones, la primera petición tras un descanso fallaría con una
    # conexión ya muerta que el pool creía viva.
    pool_pre_ping=True,
    pool_recycle=3600,
)

FabricaDeSesiones = async_sessionmaker(
    bind=motor,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa: reúne los metadatos de todas las tablas."""


async def obtener_sesion() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia: abre la sesión, la entrega y la cierra pase lo que pase."""
    async with FabricaDeSesiones() as sesion:
        yield sesion


async def comprobar_conexion(sesion: AsyncSession) -> bool:
    """Ping de infraestructura para el endpoint de salud.

    No consulta ningún recurso del dominio, así que no pertenece a la capa
    `crud`: solo verifica que la conexión responde.
    """
    await sesion.execute(text("SELECT 1"))
    return True
