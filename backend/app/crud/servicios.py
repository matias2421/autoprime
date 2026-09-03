"""Acceso a datos de los servicios del taller."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errores import RecursoNoEncontrado
from app.models.autoprime import Servicio


def obtener(sesion: Session, servicio_id: int) -> Servicio | None:
    return sesion.get(Servicio, servicio_id)


def obtener_o_fallar(sesion: Session, servicio_id: int) -> Servicio:
    servicio = obtener(sesion, servicio_id)
    if servicio is None:
        raise RecursoNoEncontrado("un servicio", servicio_id)
    return servicio


def listar(sesion: Session, estado: str | None = None) -> list[Servicio]:
    consulta = select(Servicio)
    if estado:
        consulta = consulta.where(Servicio.estado == estado)
    return list(sesion.scalars(consulta.order_by(Servicio.id)))


def crear(sesion: Session, datos: dict) -> Servicio:
    servicio = Servicio(**datos)
    sesion.add(servicio)
    sesion.commit()
    sesion.refresh(servicio)
    return servicio


def actualizar(sesion: Session, servicio: Servicio, cambios: dict) -> Servicio:
    for campo, valor in cambios.items():
        setattr(servicio, campo, valor)
    sesion.commit()
    sesion.refresh(servicio)
    return servicio


def eliminar(sesion: Session, servicio: Servicio) -> None:
    sesion.delete(servicio)
    sesion.commit()
