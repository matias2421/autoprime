"""Consultas agregadas para reportes y tableros.

Todo lo de aquí se calcula en la base. La alternativa —traer las ventas y
agruparlas en Python— da el mismo número hoy, con treinta filas, y dentro de
un año transporta la tabla entera por la red para dibujar una gráfica de doce
puntos. Agrupar y sumar es exactamente lo que MySQL hace sin mover las filas
a ninguna parte.

Las series salen ordenadas por fecha desde la propia consulta: ordenar en
Python lo que la base ya puede entregar ordenado es trabajo repetido, y el
`ORDER BY` además aprovecha el índice que ya existe sobre `fecha`.
"""

from datetime import date, timedelta

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tiempo import fin_del_dia, hoy, inicio_del_dia
from app.models.autoprime import (
    Cita,
    DetalleVenta,
    Factura,
    Pqr,
    Producto,
    Usuario,
    Venta,
)

# Una venta anulada no ingresó nada: cuenta para el histórico, no para las
# cifras de negocio.
ESTADOS_VIVOS = ("pendiente", "pagada")


def rango_por_defecto(desde: date | None, hasta: date | None) -> tuple[date, date]:
    """Sin fechas, el reporte es el de hoy.

    Es el reporte diario, que es el que se pide a diario; cualquier otro
    periodo se indica a mano.
    """
    dia = hoy()
    return desde or dia, hasta or dia


def _en_rango(consulta: Select, desde: date, hasta: date) -> Select:
    return consulta.where(
        Venta.fecha >= inicio_del_dia(desde),
        Venta.fecha <= fin_del_dia(hasta),
    )


async def serie_diaria(
    sesion: AsyncSession, desde: date, hasta: date, usuario_id: int | None = None
) -> list[dict]:
    """Ventas e ingresos por día, con los días vacíos rellenados.

    Rellenarlos importa: una gráfica de líneas que salta del día 3 al día 9
    dibuja una pendiente suave donde en realidad hubo una semana a cero, y
    eso no es un detalle estético sino una lectura equivocada del negocio.
    """
    dia = func.date(Venta.fecha).label("dia")
    consulta = select(
        dia,
        func.count(Venta.id),
        func.sum(case((Venta.estado == "pagada", Venta.total), else_=0)),
    ).where(Venta.estado.in_(ESTADOS_VIVOS))
    consulta = _en_rango(consulta, desde, hasta)
    if usuario_id is not None:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    consulta = consulta.group_by(dia).order_by(dia)

    medidos = {}
    for fila_dia, ventas, ingresos in await sesion.execute(consulta):
        # MySQL devuelve `date`; SQLite y algunos drivers, una cadena.
        clave = fila_dia if isinstance(fila_dia, date) else date.fromisoformat(str(fila_dia))
        medidos[clave] = (int(ventas or 0), float(ingresos or 0))

    serie = []
    actual = desde
    while actual <= hasta:
        ventas, ingresos = medidos.get(actual, (0, 0.0))
        serie.append(
            {"fecha": actual.isoformat(), "ventas": ventas, "ingresos": ingresos}
        )
        actual += timedelta(days=1)
    return serie


async def por_estado(
    sesion: AsyncSession, desde: date, hasta: date, usuario_id: int | None = None
) -> list[dict]:
    consulta = select(
        Venta.estado, func.count(Venta.id), func.coalesce(func.sum(Venta.total), 0)
    )
    consulta = _en_rango(consulta, desde, hasta)
    if usuario_id is not None:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    consulta = consulta.group_by(Venta.estado).order_by(func.count(Venta.id).desc())

    return [
        {"estado": estado, "ventas": int(n or 0), "importe": float(importe or 0)}
        for estado, n, importe in await sesion.execute(consulta)
    ]


async def top_vehiculos(
    sesion: AsyncSession, desde: date, hasta: date, limite: int = 5
) -> list[dict]:
    """Los modelos que más facturaron en el periodo.

    Agrupa por la descripción guardada en la línea, no por el producto: una
    línea puede apuntar a un vehículo que ya no está en el catálogo, y aun
    así esa venta ocurrió y tiene que contar.
    """
    consulta = (
        select(
            DetalleVenta.descripcion,
            func.sum(DetalleVenta.cantidad),
            func.sum(DetalleVenta.subtotal),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(Venta.estado.in_(ESTADOS_VIVOS), DetalleVenta.producto_id.isnot(None))
    )
    consulta = _en_rango(consulta, desde, hasta)
    consulta = (
        consulta.group_by(DetalleVenta.descripcion)
        .order_by(func.sum(DetalleVenta.subtotal).desc())
        .limit(limite)
    )

    return [
        {
            "descripcion": descripcion,
            "unidades": int(unidades or 0),
            "importe": float(importe or 0),
        }
        for descripcion, unidades, importe in await sesion.execute(consulta)
    ]


async def top_servicios(
    sesion: AsyncSession, desde: date, hasta: date, limite: int = 5
) -> list[dict]:
    consulta = (
        select(
            DetalleVenta.descripcion,
            func.sum(DetalleVenta.cantidad),
            func.sum(DetalleVenta.subtotal),
        )
        .join(Venta, DetalleVenta.venta_id == Venta.id)
        .where(Venta.estado.in_(ESTADOS_VIVOS), DetalleVenta.servicio_id.isnot(None))
    )
    consulta = _en_rango(consulta, desde, hasta)
    consulta = (
        consulta.group_by(DetalleVenta.descripcion)
        .order_by(func.sum(DetalleVenta.subtotal).desc())
        .limit(limite)
    )

    return [
        {
            "descripcion": descripcion,
            "unidades": int(unidades or 0),
            "importe": float(importe or 0),
        }
        for descripcion, unidades, importe in await sesion.execute(consulta)
    ]


async def detalle_ventas(
    sesion: AsyncSession, desde: date, hasta: date, usuario_id: int | None = None
) -> list[Venta]:
    """Las ventas del periodo, para la tabla del PDF y del Excel.

    Sin paginar a propósito: un reporte es el periodo entero o no es un
    reporte. Lo que acota el tamaño es el rango de fechas, que es lo que el
    usuario elige.
    """
    consulta = select(Venta)
    consulta = _en_rango(consulta, desde, hasta)
    if usuario_id is not None:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    consulta = consulta.order_by(Venta.fecha, Venta.id)
    return list((await sesion.scalars(consulta)).unique())


async def panel_administrativo(sesion: AsyncSession) -> dict:
    """Cifras de todo el negocio para el tablero del administrador.

    Son seis consultas de conteo y ninguna trae filas: cada una devuelve un
    número. Juntarlas en una sola sentencia sería una madeja de subconsultas
    peor de leer y no más rápida.
    """
    inicio_hoy = inicio_del_dia(hoy())

    usuarios = await sesion.scalar(
        select(func.count(Usuario.id)).where(Usuario.estado == "activo")
    )
    vehiculos = await sesion.scalar(
        select(func.count(Producto.id)).where(Producto.estado == "disponible")
    )
    vendidos = await sesion.scalar(
        select(func.count(Producto.id)).where(Producto.estado == "vendido")
    )
    citas_pendientes = await sesion.scalar(
        select(func.count(Cita.id)).where(Cita.estado.in_(("pendiente", "confirmada")))
    )
    pqr_abiertas = await sesion.scalar(
        select(func.count(Pqr.id)).where(Pqr.estado.in_(("pendiente", "en_proceso")))
    )
    facturas_emitidas = await sesion.scalar(
        select(func.count(Factura.id)).where(Factura.estado == "emitida")
    )
    ventas_hoy, ingresos_hoy = (
        await sesion.execute(
            select(
                func.count(Venta.id),
                func.coalesce(
                    func.sum(case((Venta.estado == "pagada", Venta.total), else_=0)), 0
                ),
            ).where(Venta.fecha >= inicio_hoy)
        )
    ).one()

    return {
        "usuarios_activos": int(usuarios or 0),
        "vehiculos_disponibles": int(vehiculos or 0),
        "vehiculos_vendidos": int(vendidos or 0),
        "citas_pendientes": int(citas_pendientes or 0),
        "pqr_abiertas": int(pqr_abiertas or 0),
        "facturas_emitidas": int(facturas_emitidas or 0),
        "ventas_hoy": int(ventas_hoy or 0),
        "ingresos_hoy": float(ingresos_hoy or 0),
    }
