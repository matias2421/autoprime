"""Acceso a datos de las facturas.

Emitir una factura es copiar la venta, no apuntar a ella. Las líneas se
duplican en `detalle_facturas` a propósito: un documento emitido dice lo que
dice, y si mañana se corrige la venta la factura ya entregada al cliente no
puede cambiar por su cuenta. Copiarlo es lo que permite corregir una cosa sin
falsear la otra.

El consecutivo se saca del id, por lo mismo que en `ventas`: dos emisiones
simultáneas que leyeran `MAX(numero)` pedirían el mismo número.
"""

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import RecursoNoEncontrado, VentaNoFacturable, VentaYaFacturada
from app.models.autoprime import DetalleFactura, Factura, Venta

# Se factura lo que existe y no está anulado. Una venta pendiente sí se
# factura: la factura es lo que el cliente necesita para pagarla.
ESTADOS_FACTURABLES = ("pendiente", "pagada")


async def obtener(sesion: AsyncSession, factura_id: int) -> Factura | None:
    return await sesion.get(Factura, factura_id)


async def obtener_o_fallar(sesion: AsyncSession, factura_id: int) -> Factura:
    factura = await obtener(sesion, factura_id)
    if factura is None:
        raise RecursoNoEncontrado("una factura", factura_id)
    return factura


async def obtener_de_venta(sesion: AsyncSession, venta_id: int) -> Factura | None:
    return await sesion.scalar(select(Factura).where(Factura.venta_id == venta_id))


def _filtrar(
    consulta: Select,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Select:
    """Filtros compartidos por el listado y por su cuenta.

    El filtro por cliente exige pasar por `ventas`: la factura no guarda a
    quién se le emitió, lo guarda la venta de la que salió.
    """
    if usuario_id is not None:
        consulta = consulta.join(Venta, Factura.venta_id == Venta.id).where(
            Venta.usuario_id == usuario_id
        )
    if estado:
        consulta = consulta.where(Factura.estado == estado)
    if desde:
        consulta = consulta.where(
            Factura.fecha_emision >= datetime.combine(desde, datetime.min.time())
        )
    if hasta:
        consulta = consulta.where(
            Factura.fecha_emision <= datetime.combine(hasta, datetime.max.time())
        )
    return consulta


async def contar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> int:
    consulta = _filtrar(
        select(func.count(Factura.id)), usuario_id, estado, desde, hasta
    )
    return await sesion.scalar(consulta) or 0


async def listar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limite: int | None = None,
    desplazamiento: int = 0,
) -> list[Factura]:
    consulta = _filtrar(select(Factura), usuario_id, estado, desde, hasta)
    consulta = consulta.order_by(Factura.fecha_emision.desc(), Factura.id.desc())
    if limite is not None:
        consulta = consulta.limit(limite).offset(desplazamiento)
    return list((await sesion.scalars(consulta)).unique())


async def emitir(sesion: AsyncSession, venta: Venta) -> Factura:
    """Emite la factura de una venta. Una venta, una factura."""
    if venta.estado not in ESTADOS_FACTURABLES:
        raise VentaNoFacturable(venta.estado)

    if await obtener_de_venta(sesion, venta.id) is not None:
        raise VentaYaFacturada(venta.numero)

    factura = Factura(
        numero=f"tmp-{uuid4().hex[:14]}",
        venta_id=venta.id,
        subtotal=venta.subtotal,
        impuestos=venta.impuestos,
        total=venta.total,
        lineas=[
            DetalleFactura(
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                subtotal=linea.subtotal,
            )
            for linea in venta.lineas
        ],
    )
    sesion.add(factura)

    await sesion.flush()
    factura.numero = f"F-{date.today().year}-{factura.id:05d}"
    await sesion.commit()

    await sesion.refresh(factura)
    return factura


async def anular(sesion: AsyncSession, factura: Factura) -> Factura:
    """Una factura no se borra, se anula.

    Borrarla dejaría un hueco en el consecutivo, y un consecutivo con huecos
    no sirve para lo que existe: poder demostrar que no falta ninguna.
    """
    factura.estado = "anulada"
    await sesion.commit()
    await sesion.refresh(factura)
    return factura
