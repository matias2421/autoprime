"""Acceso a datos de los servicios del taller."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import RecursoNoEncontrado
from app.models.autoprime import Servicio


async def obtener(sesion: AsyncSession, servicio_id: int) -> Servicio | None:
    return await sesion.get(Servicio, servicio_id)


async def obtener_o_fallar(sesion: AsyncSession, servicio_id: int) -> Servicio:
    servicio = await obtener(sesion, servicio_id)
    if servicio is None:
        raise RecursoNoEncontrado("un servicio", servicio_id)
    return servicio


async def listar(sesion: AsyncSession, estado: str | None = None) -> list[Servicio]:
    consulta = select(Servicio)
    if estado:
        consulta = consulta.where(Servicio.estado == estado)
    return list(await sesion.scalars(consulta.order_by(Servicio.id)))


async def crear(sesion: AsyncSession, datos: dict) -> Servicio:
    servicio = Servicio(**datos)
    sesion.add(servicio)
    await sesion.commit()
    await sesion.refresh(servicio)
    return servicio


async def actualizar(sesion: AsyncSession, servicio: Servicio, cambios: dict) -> Servicio:
    for campo, valor in cambios.items():
        setattr(servicio, campo, valor)
    await sesion.commit()
    await sesion.refresh(servicio)
    return servicio


async def eliminar(sesion: AsyncSession, servicio: Servicio) -> None:
    await sesion.delete(servicio)
    await sesion.commit()
