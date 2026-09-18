"""Acceso a datos de las ventas.

Dos decisiones que conviene leer antes que el código:

1. **La venta entera cabe en una transacción.** Crear la cabecera, sus líneas
   y marcar como vendidos los vehículos son un solo `commit`. Si algo falla a
   mitad, no queda una venta sin líneas ni un coche marcado como vendido sin
   venta que lo respalde.

2. **El consecutivo sale del id que asigna la base**, no de un `MAX(numero)`
   leído antes de insertar. Dos ventas simultáneas leerían el mismo máximo y
   pelearían por el mismo número: una se cae contra el UNIQUE y hay que
   repetir todo el trabajo. Así que la fila se inserta con un número
   provisional, la base asigna el id —eso sí es atómico— y el definitivo se
   escribe dentro de la misma transacción. El provisional no llega a verlo
   nadie: solo existe entre el INSERT y el COMMIT.
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errores import (
    PrecioBajoConsulta,
    RecursoNoEncontrado,
    VehiculoNoDisponible,
    VentaNoModificable,
)
from app.models.autoprime import DetalleVenta, Producto, Servicio, Venta

# IVA colombiano. Vive aquí y no en la configuración porque es una regla del
# negocio, no del entorno: no cambia entre desarrollo y producción.
TASA_IVA = Decimal("0.19")

CENTIMO = Decimal("0.01")

# Una venta pagada o anulada ya es histórico y no se toca.
ESTADOS_CERRADOS = ("pagada", "anulada")


def _redondear(valor: Decimal) -> Decimal:
    """Al céntimo, con el medio hacia arriba, que es como se redondea dinero.

    Sin esto, `Decimal` arrastra todos los decimales que salgan de multiplicar
    por la tasa, y la suma de las líneas deja de cuadrar con el total por unos
    céntimos que nadie sabe explicar.
    """
    return valor.quantize(CENTIMO, rounding=ROUND_HALF_UP)


async def obtener(sesion: AsyncSession, venta_id: int) -> Venta | None:
    return await sesion.get(Venta, venta_id)


async def obtener_o_fallar(sesion: AsyncSession, venta_id: int) -> Venta:
    venta = await obtener(sesion, venta_id)
    if venta is None:
        raise RecursoNoEncontrado("una venta", venta_id)
    return venta


def _filtrar(
    consulta: Select,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Select:
    """Los mismos filtros para listar y para contar.

    Compartirlos es lo que garantiza que el total del paginador corresponda a
    lo que se está listando. Con dos copias, cualquier filtro añadido a una y
    olvidado en la otra produce un paginador que miente.
    """
    if usuario_id is not None:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    if estado:
        consulta = consulta.where(Venta.estado == estado)
    if desde:
        consulta = consulta.where(
            Venta.fecha >= datetime.combine(desde, datetime.min.time())
        )
    if hasta:
        consulta = consulta.where(
            Venta.fecha <= datetime.combine(hasta, datetime.max.time())
        )
    return consulta


async def contar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> int:
    """Cuenta en la base. Traer las filas para hacerles `len()` es traerlas."""
    consulta = _filtrar(
        select(func.count()).select_from(Venta), usuario_id, estado, desde, hasta
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
) -> list[Venta]:
    consulta = _filtrar(select(Venta), usuario_id, estado, desde, hasta)
    consulta = consulta.order_by(Venta.fecha.desc(), Venta.id.desc())
    if limite is not None:
        consulta = consulta.limit(limite).offset(desplazamiento)
    return list((await sesion.scalars(consulta)).unique())


async def _armar_linea(
    sesion: AsyncSession, datos: dict, puede_fijar_precio: bool
) -> DetalleVenta:
    """Convierte una línea pedida en una línea vendible.

    Aquí es donde el precio deja de venir de fuera: se lee del catálogo. Y
    donde se comprueba que lo que se vende exista y esté a la venta.
    """
    cantidad = datos.get("cantidad", 1)
    descuento = _redondear(Decimal(datos.get("descuento") or 0))
    precio_pedido = datos.get("precio_unitario")

    if datos.get("producto_id"):
        producto = await sesion.get(Producto, datos["producto_id"])
        if producto is None:
            raise RecursoNoEncontrado("un vehículo", datos["producto_id"])

        etiqueta = f"{producto.marca} {producto.modelo}"
        if producto.estado != "disponible":
            raise VehiculoNoDisponible(etiqueta, producto.estado)

        if puede_fijar_precio and precio_pedido is not None:
            precio = Decimal(precio_pedido)
        elif producto.precio is None:
            # Pieza sin precio de lista: la cifra la pone un asesor.
            raise PrecioBajoConsulta(etiqueta)
        else:
            precio = Decimal(producto.precio)

        descripcion = f"{etiqueta} ({producto.anio})"
        referencia = {"producto_id": producto.id}
    else:
        servicio = await sesion.get(Servicio, datos["servicio_id"])
        if servicio is None:
            raise RecursoNoEncontrado("un servicio", datos["servicio_id"])

        if puede_fijar_precio and precio_pedido is not None:
            precio = Decimal(precio_pedido)
        else:
            precio = Decimal(servicio.precio)

        descripcion = servicio.nombre
        referencia = {"servicio_id": servicio.id}

    precio = _redondear(precio)
    subtotal = _redondear(precio * cantidad - descuento)
    if subtotal < 0:
        # Un descuento mayor que la línea la dejaría en negativo y restaría
        # del total de la venta, que es justo lo que un descuento no hace.
        subtotal = Decimal("0.00")

    return DetalleVenta(
        descripcion=descripcion,
        cantidad=cantidad,
        precio_unitario=precio,
        descuento=descuento,
        subtotal=subtotal,
        **referencia,
    )


async def crear(
    sesion: AsyncSession,
    comprador_id: int,
    datos: dict,
    vendedor_id: int | None = None,
    puede_fijar_precio: bool = False,
) -> Venta:
    """Registra la venta completa en una sola transacción."""
    lineas = [
        await _armar_linea(sesion, linea, puede_fijar_precio)
        for linea in datos["lineas"]
    ]

    bruto = sum((linea.subtotal for linea in lineas), Decimal(0))
    descuento = _redondear(Decimal(datos.get("descuento") or 0))
    if descuento > bruto:
        descuento = bruto

    subtotal = _redondear(bruto - descuento)
    impuestos = _redondear(subtotal * TASA_IVA)
    total = _redondear(subtotal + impuestos)

    venta = Venta(
        # Provisional: vive lo que dure la transacción. Ver la cabecera.
        numero=f"tmp-{uuid4().hex[:14]}",
        usuario_id=comprador_id,
        vendedor_id=vendedor_id,
        subtotal=subtotal,
        descuento=descuento,
        impuestos=impuestos,
        total=total,
        notas=datos.get("notas"),
        lineas=lineas,
    )
    sesion.add(venta)

    # Un vehículo vendido sale del catálogo aunque la venta siga pendiente de
    # pago: mientras se cobra está reservado, y no puede vendérsele a otra
    # persona entretanto.
    for linea in lineas:
        if linea.producto_id:
            producto = await sesion.get(Producto, linea.producto_id)
            producto.estado = "vendido"

    await sesion.flush()  # aquí la base asigna el id
    venta.numero = f"V-{date.today().year}-{venta.id:05d}"
    await sesion.commit()

    await sesion.refresh(venta)
    return venta


async def cambiar_estado(sesion: AsyncSession, venta: Venta, estado: str) -> Venta:
    """Anular devuelve los vehículos al catálogo; lo demás solo marca."""
    if venta.estado == estado:
        return venta

    if estado == "anulada":
        for linea in venta.lineas:
            if linea.producto_id:
                producto = await sesion.get(Producto, linea.producto_id)
                if producto and producto.estado == "vendido":
                    producto.estado = "disponible"

    venta.estado = estado
    await sesion.commit()
    await sesion.refresh(venta)
    return venta


async def actualizar_notas(
    sesion: AsyncSession, venta: Venta, notas: str | None
) -> Venta:
    if venta.estado in ESTADOS_CERRADOS:
        raise VentaNoModificable(venta.estado)
    venta.notas = notas
    await sesion.commit()
    await sesion.refresh(venta)
    return venta


async def eliminar(sesion: AsyncSession, venta: Venta) -> None:
    """Borra la venta y devuelve sus vehículos al catálogo."""
    for linea in venta.lineas:
        if linea.producto_id:
            producto = await sesion.get(Producto, linea.producto_id)
            if producto and producto.estado == "vendido":
                producto.estado = "disponible"
    await sesion.delete(venta)
    await sesion.commit()


async def resumen(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> dict:
    """Contadores e ingresos, calculados por la base en una sola consulta.

    La versión obvia —traer las ventas y recorrerlas en Python— funciona con
    diez filas y deja de funcionar con diez mil: transporta la tabla entera
    para devolver seis números. Contar y sumar es exactamente lo que MySQL
    hace sin mover las filas a ninguna parte.
    """
    columnas = (
        func.count(Venta.id),
        func.sum(func.if_(Venta.estado == "pendiente", 1, 0)),
        func.sum(func.if_(Venta.estado == "pagada", 1, 0)),
        func.sum(func.if_(Venta.estado == "anulada", 1, 0)),
        # Ingresos es lo cobrado: una venta anulada no ingresó nada.
        func.sum(func.if_(Venta.estado == "pagada", Venta.total, 0)),
    )
    consulta = _filtrar(select(*columnas), usuario_id, None, desde, hasta)
    total, pendientes, pagadas, anuladas, ingresos = (
        await sesion.execute(consulta)
    ).one()

    ingresos = Decimal(ingresos or 0)
    pagadas = int(pagadas or 0)

    return {
        "total": int(total or 0),
        "pendientes": int(pendientes or 0),
        "pagadas": pagadas,
        "anuladas": int(anuladas or 0),
        "ingresos": _redondear(ingresos),
        # El promedio se mide sobre lo cobrado: dividirlo entre el total de
        # ventas contaría las anuladas y saldría un ticket más bajo del real.
        "ticket_promedio": (
            _redondear(ingresos / pagadas) if pagadas else Decimal("0.00")
        ),
    }
