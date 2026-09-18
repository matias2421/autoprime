"""Acceso a datos del chat: conversaciones y mensajes.

Las conversaciones se guardan aunque el asistente sea de otro. Sirven para
tres cosas distintas: que quien vuelve encuentre el hilo donde lo dejó, que
el modelo reciba contexto —sin historial cada mensaje empieza de cero y el
chat no entiende un «¿y cuánto cuesta ese?»— y que el negocio pueda leer qué
le está preguntando la gente.
"""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.configuracion import configuracion
from app.errores import RecursoNoEncontrado
from app.models.autoprime import Conversacion, Mensaje, Producto, Servicio

# Tope de mensajes por conversación. No es una regla de negocio: es el freno
# que impide que una pestaña abierta con un bucle consuma la cuota del
# proveedor. Al llegar, se abre una conversación nueva.
MENSAJES_MAXIMOS = 60


async def obtener(sesion: AsyncSession, conversacion_id: int) -> Conversacion | None:
    return await sesion.get(Conversacion, conversacion_id)


async def obtener_o_fallar(sesion: AsyncSession, conversacion_id: int) -> Conversacion:
    conversacion = await obtener(sesion, conversacion_id)
    if conversacion is None:
        raise RecursoNoEncontrado("una conversación", conversacion_id)
    return conversacion


def _filtrar(consulta: Select, usuario_id: int | None) -> Select:
    if usuario_id is not None:
        consulta = consulta.where(Conversacion.usuario_id == usuario_id)
    return consulta


async def contar(sesion: AsyncSession, usuario_id: int | None = None) -> int:
    return await sesion.scalar(
        _filtrar(select(func.count(Conversacion.id)), usuario_id)
    ) or 0


async def listar(
    sesion: AsyncSession,
    usuario_id: int | None = None,
    limite: int | None = None,
    desplazamiento: int = 0,
) -> list[Conversacion]:
    consulta = _filtrar(select(Conversacion), usuario_id)
    consulta = consulta.order_by(Conversacion.ultima_actividad.desc())
    if limite is not None:
        consulta = consulta.limit(limite).offset(desplazamiento)
    return list((await sesion.scalars(consulta)).unique())


async def abrir(
    sesion: AsyncSession, usuario_id: int | None, titulo: str | None = None
) -> Conversacion:
    conversacion = Conversacion(usuario_id=usuario_id, titulo=titulo)
    sesion.add(conversacion)
    await sesion.commit()
    await sesion.refresh(conversacion)
    return conversacion


async def anotar(
    sesion: AsyncSession, conversacion: Conversacion, rol: str, contenido: str
) -> Mensaje:
    mensaje = Mensaje(conversacion_id=conversacion.id, rol=rol, contenido=contenido)
    sesion.add(mensaje)

    # Tocar la conversación es lo que mantiene el orden de la lista: sin esto,
    # un hilo activo se hunde bajo otros que nadie ha abierto en semanas.
    conversacion.ultima_actividad = mensaje.creado_en or conversacion.ultima_actividad

    await sesion.commit()
    await sesion.refresh(mensaje)
    return mensaje


async def historial_para_modelo(conversacion: Conversacion) -> list[dict]:
    """Los últimos mensajes, en el formato que espera el proveedor.

    Se recorta a propósito. El historial completo crece sin techo y cada
    petición lo paga entero, en dinero y en latencia; con los últimos basta
    para que la conversación se sostenga.
    """
    recientes = conversacion.mensajes[-configuracion.mensajes_de_contexto :]
    return [
        {
            "role": "assistant" if m.rol == "asistente" else "user",
            "content": m.contenido,
        }
        for m in recientes
    ]


async def datos_del_negocio(sesion: AsyncSession) -> tuple[list, list]:
    """El catálogo y los servicios que se le ponen delante al modelo.

    Se leen en cada mensaje. Guardarlos en memoria ahorraría dos consultas y
    haría que el asistente recitara el precio de la semana pasada, que es
    peor que tardar quince milisegundos más.
    """
    productos = list(await sesion.scalars(select(Producto).order_by(Producto.id)))
    servicios = list(
        await sesion.scalars(
            select(Servicio).where(Servicio.estado == "activo").order_by(Servicio.id)
        )
    )
    return productos, servicios


async def eliminar(sesion: AsyncSession, conversacion: Conversacion) -> None:
    await sesion.delete(conversacion)
    await sesion.commit()
