"""Acceso a datos del catálogo de vehículos."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import RecursoNoEncontrado, SlugYaRegistrado
from app.models.autoprime import Producto


async def obtener(sesion: AsyncSession, producto_id: int) -> Producto | None:
    return await sesion.get(Producto, producto_id)


async def obtener_o_fallar(sesion: AsyncSession, producto_id: int) -> Producto:
    producto = await obtener(sesion, producto_id)
    if producto is None:
        raise RecursoNoEncontrado("un vehículo", producto_id)
    return producto


async def obtener_por_slug(sesion: AsyncSession, slug: str) -> Producto:
    producto = await sesion.scalar(select(Producto).where(Producto.slug == slug))
    if producto is None:
        raise RecursoNoEncontrado("un vehículo", slug)
    return producto


async def listar(
    sesion: AsyncSession, familia: str | None = None, estado: str | None = None
) -> list[Producto]:
    consulta = select(Producto)
    if familia and familia != "todos":
        consulta = consulta.where(Producto.familia == familia)
    if estado:
        consulta = consulta.where(Producto.estado == estado)
    return list(await sesion.scalars(consulta.order_by(Producto.id)))


async def _comprobar_slug(sesion: AsyncSession, slug: str, excluir_id: int | None = None) -> None:
    consulta = select(Producto).where(Producto.slug == slug)
    if excluir_id:
        consulta = consulta.where(Producto.id != excluir_id)
    if await sesion.scalar(consulta):
        raise SlugYaRegistrado(slug)


async def crear(sesion: AsyncSession, datos: dict) -> Producto:
    await _comprobar_slug(sesion, datos["slug"])
    producto = Producto(**datos)
    sesion.add(producto)
    await sesion.commit()
    await sesion.refresh(producto)
    return producto


async def actualizar(sesion: AsyncSession, producto: Producto, cambios: dict) -> Producto:
    if "slug" in cambios:
        await _comprobar_slug(sesion, cambios["slug"], excluir_id=producto.id)
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    await sesion.commit()
    await sesion.refresh(producto)
    return producto


async def eliminar(sesion: AsyncSession, producto: Producto) -> None:
    await sesion.delete(producto)
    await sesion.commit()
