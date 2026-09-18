"""Acceso a datos de las PQR."""

from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tiempo import hoy
from app.errores import PqrNoModificable, RecursoNoEncontrado
from app.models.autoprime import Pqr

# Una PQR cerrada es historia: ni se responde otra vez ni cambia de estado.
ESTADOS_CERRADOS = ("cerrada",)


async def obtener(sesion: AsyncSession, pqr_id: int) -> Pqr | None:
    return await sesion.get(Pqr, pqr_id)


async def obtener_o_fallar(sesion: AsyncSession, pqr_id: int) -> Pqr:
    registro = await obtener(sesion, pqr_id)
    if registro is None:
        raise RecursoNoEncontrado("una PQR", pqr_id)
    return registro


def _filtrar(
    consulta: Select,
    usuario_id: int | None = None,
    estado: str | None = None,
    tipo: str | None = None,
) -> Select:
    if usuario_id is not None:
        consulta = consulta.where(Pqr.usuario_id == usuario_id)
    if estado:
        consulta = consulta.where(Pqr.estado == estado)
    if tipo:
        consulta = consulta.where(Pqr.tipo == tipo)
    return consulta


async def contar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    tipo: str | None = None,
) -> int:
    return (
        await sesion.scalar(
            _filtrar(select(func.count(Pqr.id)), usuario_id, estado, tipo)
        )
        or 0
    )


async def listar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    estado: str | None = None,
    tipo: str | None = None,
    limite: int | None = None,
    desplazamiento: int = 0,
) -> list[Pqr]:
    consulta = _filtrar(select(Pqr), usuario_id, estado, tipo)

    # Lo pendiente primero: es una bandeja de trabajo, no un archivo. Ordenar
    # solo por fecha enterraría un reclamo sin atender bajo veinte cerrados.
    orden_estado = func.field(Pqr.estado, "pendiente", "en_proceso", "respondida")
    consulta = consulta.order_by(orden_estado, Pqr.creado_en.desc())

    if limite is not None:
        consulta = consulta.limit(limite).offset(desplazamiento)
    return list((await sesion.scalars(consulta)).unique())


async def crear(sesion: AsyncSession, usuario_id: int, datos: dict) -> Pqr:
    """Radica la PQR y le asigna consecutivo.

    El número sale del id que asigna la base, igual que en ventas y facturas:
    leer un `MAX(numero)` antes de insertar hace que dos radicados simultáneos
    pidan el mismo.
    """
    registro = Pqr(numero=f"tmp-{uuid4().hex[:14]}", usuario_id=usuario_id, **datos)
    sesion.add(registro)

    await sesion.flush()
    registro.numero = f"P-{hoy().year}-{registro.id:05d}"
    await sesion.commit()

    await sesion.refresh(registro)
    return registro


async def responder(
    sesion: AsyncSession, registro: Pqr, respuesta: str, estado: str, atendido_por: int
) -> Pqr:
    if registro.estado in ESTADOS_CERRADOS:
        raise PqrNoModificable(registro.estado)

    registro.respuesta = respuesta
    registro.estado = estado
    registro.atendido_por = atendido_por
    await sesion.commit()
    await sesion.refresh(registro)
    return registro


async def cambiar_estado(sesion: AsyncSession, registro: Pqr, estado: str) -> Pqr:
    if registro.estado in ESTADOS_CERRADOS:
        raise PqrNoModificable(registro.estado)
    registro.estado = estado
    await sesion.commit()
    await sesion.refresh(registro)
    return registro


async def eliminar(sesion: AsyncSession, registro: Pqr) -> None:
    await sesion.delete(registro)
    await sesion.commit()


async def resumen(sesion: AsyncSession, usuario_id: int | None = None) -> dict:
    """Los cinco contadores en una sola consulta, calculados por la base."""
    columnas = (
        func.count(Pqr.id),
        func.sum(func.if_(Pqr.estado == "pendiente", 1, 0)),
        func.sum(func.if_(Pqr.estado == "en_proceso", 1, 0)),
        func.sum(func.if_(Pqr.estado == "respondida", 1, 0)),
        func.sum(func.if_(Pqr.estado == "cerrada", 1, 0)),
    )
    fila = (await sesion.execute(_filtrar(select(*columnas), usuario_id))).one()
    total, pendientes, en_proceso, respondidas, cerradas = fila

    return {
        "total": int(total or 0),
        "pendientes": int(pendientes or 0),
        "en_proceso": int(en_proceso or 0),
        "respondidas": int(respondidas or 0),
        "cerradas": int(cerradas or 0),
    }
