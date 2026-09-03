"""Conexión a la base de datos con SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.configuracion import configuracion

motor = create_engine(
    configuracion.url_base_datos,
    echo=False,
    # MySQL cierra las conexiones que llevan rato inactivas. Sin estas dos
    # opciones, la primera petición tras un descanso fallaría con una
    # conexión ya muerta que el pool creía viva.
    pool_pre_ping=True,
    pool_recycle=3600,
)

FabricaDeSesiones = sessionmaker(bind=motor, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa: reúne los metadatos de todas las tablas."""


def obtener_sesion() -> Generator[Session, None, None]:
    """Dependencia: abre la sesión, la entrega y la cierra pase lo que pase."""
    sesion = FabricaDeSesiones()
    try:
        yield sesion
    finally:
        sesion.close()


def comprobar_conexion(sesion: Session) -> bool:
    """Ping de infraestructura para el endpoint de salud.

    No consulta ningún recurso del dominio, así que no pertenece a la capa
    `crud`: solo verifica que la conexión responde.
    """
    sesion.execute(text("SELECT 1"))
    return True
