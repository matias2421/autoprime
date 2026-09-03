"""Acceso a datos del catálogo de vehículos."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errores import RecursoNoEncontrado, SlugYaRegistrado
from app.models.autoprime import Producto


def obtener(sesion: Session, producto_id: int) -> Producto | None:
    return sesion.get(Producto, producto_id)


def obtener_o_fallar(sesion: Session, producto_id: int) -> Producto:
    producto = obtener(sesion, producto_id)
    if producto is None:
        raise RecursoNoEncontrado("un vehículo", producto_id)
    return producto


def obtener_por_slug(sesion: Session, slug: str) -> Producto:
    producto = sesion.scalar(select(Producto).where(Producto.slug == slug))
    if producto is None:
        raise RecursoNoEncontrado("un vehículo", slug)
    return producto


def listar(
    sesion: Session, familia: str | None = None, estado: str | None = None
) -> list[Producto]:
    consulta = select(Producto)
    if familia and familia != "todos":
        consulta = consulta.where(Producto.familia == familia)
    if estado:
        consulta = consulta.where(Producto.estado == estado)
    return list(sesion.scalars(consulta.order_by(Producto.id)))


def _comprobar_slug(sesion: Session, slug: str, excluir_id: int | None = None) -> None:
    consulta = select(Producto).where(Producto.slug == slug)
    if excluir_id:
        consulta = consulta.where(Producto.id != excluir_id)
    if sesion.scalar(consulta):
        raise SlugYaRegistrado(slug)


def crear(sesion: Session, datos: dict) -> Producto:
    _comprobar_slug(sesion, datos["slug"])
    producto = Producto(**datos)
    sesion.add(producto)
    sesion.commit()
    sesion.refresh(producto)
    return producto


def actualizar(sesion: Session, producto: Producto, cambios: dict) -> Producto:
    if "slug" in cambios:
        _comprobar_slug(sesion, cambios["slug"], excluir_id=producto.id)
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    sesion.commit()
    sesion.refresh(producto)
    return producto


def eliminar(sesion: Session, producto: Producto) -> None:
    sesion.delete(producto)
    sesion.commit()
