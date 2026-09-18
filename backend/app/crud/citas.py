"""Acceso a datos de las citas del taller."""

from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tiempo import ahora
from app.errores import CitaNoModificable, FranjaOcupada, RecursoNoEncontrado
from app.models.autoprime import Cita

# Franjas que ofrece el taller, de 8 a 17 en punto.
FRANJAS = [time(h, 0) for h in range(8, 18)]

# Una vez cancelada o completada, la cita queda como registro histórico.
ESTADOS_CERRADOS = ("cancelada", "completada")


async def obtener(sesion: AsyncSession, cita_id: int) -> Cita | None:
    return await sesion.get(Cita, cita_id)


async def obtener_o_fallar(sesion: AsyncSession, cita_id: int) -> Cita:
    cita = await obtener(sesion, cita_id)
    if cita is None:
        raise RecursoNoEncontrado("una cita", cita_id)
    return cita


async def listar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    desde: date | None = None,
) -> list[Cita]:
    """Lista citas. Con `usuario_id` devuelve solo las de esa persona."""
    consulta = select(Cita)
    if usuario_id is not None:
        consulta = consulta.where(Cita.usuario_id == usuario_id)
    if estado:
        consulta = consulta.where(Cita.estado == estado)
    if desde:
        consulta = consulta.where(Cita.fecha >= desde)
    consulta = consulta.order_by(Cita.fecha.desc(), Cita.hora.desc())
    return list((await sesion.scalars(consulta)).unique())


async def _franja_ocupada(
    sesion: AsyncSession,
    fecha: date,
    hora: time,
    producto_id: int | None,
    excluir_id: int | None = None,
) -> bool:
    """Comprueba el cupo.

    Solo choca si es el mismo vehículo: dos clientes pueden coincidir en hora
    si van a ver coches distintos. Sin `producto_id` no hay exclusividad.
    """
    if producto_id is None:
        return False

    consulta = select(Cita).where(
        Cita.fecha == fecha,
        Cita.hora == hora,
        Cita.producto_id == producto_id,
        Cita.estado.notin_(ESTADOS_CERRADOS),
    )
    if excluir_id:
        consulta = consulta.where(Cita.id != excluir_id)
    return await sesion.scalar(consulta) is not None


async def franjas_de(sesion: AsyncSession, fecha: date, producto_id: int | None) -> list[dict]:
    """Devuelve las franjas del día marcando cuáles siguen libres."""
    # El reloj del negocio, no el del servidor: en Render el contenedor va
    # en UTC y ofreceria franjas de un dia que en Colombia aun no empieza.
    instante = ahora()
    salida = []

    for franja in FRANJAS:
        libre = not await _franja_ocupada(sesion, fecha, franja, producto_id)

        # Una hora que ya pasó hoy no se ofrece aunque nadie la haya tomado.
        if fecha == instante.date() and franja <= instante.time():
            libre = False

        salida.append({"hora": franja.strftime("%H:%M"), "disponible": libre})

    return salida


async def crear(sesion: AsyncSession, usuario_id: int, datos: dict) -> Cita:
    if await _franja_ocupada(sesion, datos["fecha"], datos["hora"], datos.get("producto_id")):
        raise FranjaOcupada(
            datos["fecha"].isoformat(), datos["hora"].strftime("%H:%M")
        )

    cita = Cita(usuario_id=usuario_id, **datos)
    sesion.add(cita)
    await sesion.commit()
    await sesion.refresh(cita)
    return cita


async def actualizar(sesion: AsyncSession, cita: Cita, cambios: dict) -> Cita:
    if cita.estado in ESTADOS_CERRADOS:
        raise CitaNoModificable(cita.estado)

    fecha = cambios.get("fecha", cita.fecha)
    hora = cambios.get("hora", cita.hora)
    producto_id = cambios.get("producto_id", cita.producto_id)

    if await _franja_ocupada(sesion, fecha, hora, producto_id, excluir_id=cita.id):
        raise FranjaOcupada(fecha.isoformat(), hora.strftime("%H:%M"))

    for campo, valor in cambios.items():
        setattr(cita, campo, valor)

    await sesion.commit()
    await sesion.refresh(cita)
    return cita


async def cambiar_estado(sesion: AsyncSession, cita: Cita, estado: str) -> Cita:
    cita.estado = estado
    await sesion.commit()
    await sesion.refresh(cita)
    return cita


async def eliminar(sesion: AsyncSession, cita: Cita) -> None:
    await sesion.delete(cita)
    await sesion.commit()


async def resumen(sesion: AsyncSession, usuario_id: int | None = None) -> dict:
    """Contadores por estado para la cabecera de los paneles."""
    citas = await listar(sesion, usuario_id=usuario_id)
    return {
        "total": len(citas),
        "pendientes": sum(1 for c in citas if c.estado == "pendiente"),
        "confirmadas": sum(1 for c in citas if c.estado == "confirmada"),
        "canceladas": sum(1 for c in citas if c.estado == "cancelada"),
        "completadas": sum(1 for c in citas if c.estado == "completada"),
    }
