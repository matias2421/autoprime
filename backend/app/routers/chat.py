"""Chat con el asistente.

Es el único router que atiende sin sesión iniciada, y a propósito: es lo
primero que ve un visitante, y exigirle registro antes de dejarle preguntar
un precio es perder la conversación antes de empezarla.

Que sea público cambia dos cosas respecto a los demás.

**Cuesta dinero por uso**, porque cada mensaje es una llamada a un proveedor
que factura por tokens. De ahí el freno por origen y el tope de mensajes por
conversación.

**El historial no se sirve sin sesión.** Los identificadores de conversación
son consecutivos, así que un `GET /api/chat/conversaciones/4` con un número
al azar leería la conversación de otra persona. Enviar un mensaje devuelve
solo el par que se acaba de intercambiar; para volver a leer un hilo hay que
haber iniciado sesión y ser su dueño. El frontend de un visitante guarda su
propia transcripción mientras dure la pestaña.
"""

from fastapi import APIRouter, Request, Response, status

from app.core import asistente, limitador
from app.crud import chat as crud_chat
from app.dependencias import (
    ConversacionRuta,
    SesionDep,
    UsuarioActual,
    UsuarioOpcional,
)
from app.documentacion import (
    NO_AUTENTICADO,
    NO_ENCONTRADO,
    NO_VALIDO,
    SERVICIO_CAIDO,
    SIN_PERMISO,
    respuestas,
)
from app.errores import DatosInvalidos, DemasiadasPeticiones, PermisoDenegado
from app.schemas.chat import (
    ConversacionCrear,
    ConversacionSalida,
    MensajeCrear,
    MensajeSalida,
    RespuestaChat,
)
from app.schemas.paginacion import PaginaDep
from app.schemas.sobres import (
    SobreChat,
    SobreConversacion,
    SobreConversaciones,
)

router = APIRouter(prefix="/api/chat", tags=["Asistente"])

# Mensajes por minuto y por origen. Doce da para una conversación fluida —uno
# cada cinco segundos— y corta en seco un bucle.
MENSAJES_POR_MINUTO = 12

# Aperturas de conversación por minuto. Más bajo: abrir hilos vacíos en masa
# no es conversar, es llenar la tabla.
APERTURAS_POR_MINUTO = 6


def _origen(peticion: Request) -> str:
    """De dónde viene la petición, para contarle sus mensajes.

    Detrás de Render hay un balanceador, así que `request.client.host` es el
    del balanceador y sería el mismo para todo el mundo: el límite pasaría a
    ser global y el primer usuario activo dejaría fuera a los demás. El
    primer valor de `X-Forwarded-For` es el cliente real.
    """
    reenviado = peticion.headers.get("x-forwarded-for")
    if reenviado:
        return reenviado.split(",")[0].strip()
    return peticion.client.host if peticion.client else "desconocido"


def _frenar(peticion: Request, cupo: int) -> None:
    permitido, espera = limitador.permitido(_origen(peticion), cupo)
    if not permitido:
        # 429 con `Retry-After`: sin la cabecera, quien llama solo sabe que
        # le dijeron que no, y lo normal es que reintente de inmediato.
        raise DemasiadasPeticiones(espera)



def _exigir_dueno(usuario, conversacion) -> None:
    """Solo el dueño lee su hilo. Uno anónimo no lo lee nadie."""
    if conversacion.usuario_id is None or usuario is None:
        raise PermisoDenegado(
            "Esa conversación no está asociada a tu cuenta. Inicia sesión para "
            "conservar tus conversaciones."
        )
    if conversacion.usuario_id != usuario.id:
        raise PermisoDenegado("Esa conversación no te pertenece.")


@router.get("/estado", summary="¿Está disponible el asistente?")
async def estado() -> dict:
    """Lo consulta el frontend antes de pintar el chat.

    Sin clave configurada, la respuesta es que no está disponible en lugar de
    un error: el resto del sitio funciona igual y el widget puede ofrecer la
    PQR como alternativa sin que nadie vea una pantalla rota.
    """
    return {
        "disponible": asistente.disponible(),
        "alternativa": "/pqr" if not asistente.disponible() else None,
    }


@router.post(
    "/conversaciones",
    response_model=SobreConversacion,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir una conversación",
    responses=respuestas(NO_VALIDO),
)
async def abrir(
    datos: ConversacionCrear,
    peticion: Request,
    sesion: SesionDep,
    usuario: UsuarioOpcional,
) -> SobreConversacion:
    """Con sesión, la conversación queda asociada a la cuenta y se recupera
    después. Sin sesión, vive mientras dure la pestaña."""
    _frenar(peticion, APERTURAS_POR_MINUTO)
    conversacion = await crud_chat.abrir(
        sesion, usuario.id if usuario else None, datos.titulo
    )
    return SobreConversacion(
        conversacion=ConversacionSalida.desde_modelo(conversacion)
    )


@router.post(
    "/conversaciones/{conversacion_id}/mensajes",
    response_model=SobreChat,
    summary="Escribir al asistente",
    responses=respuestas(NO_ENCONTRADO, NO_VALIDO, SERVICIO_CAIDO),
)
async def escribir(
    datos: MensajeCrear,
    conversacion: ConversacionRuta,
    peticion: Request,
    sesion: SesionDep,
    usuario: UsuarioOpcional,
) -> SobreChat:
    """Guarda la pregunta, consulta al modelo y guarda la respuesta.

    La pregunta se guarda ANTES de llamar al proveedor. Si el modelo falla, el
    mensaje de quien escribió no se pierde: la conversación queda con su
    pregunta y se puede reintentar sin volver a escribirla.
    """
    _frenar(peticion, MENSAJES_POR_MINUTO)

    # Un hilo con dueño solo lo continúa su dueño.
    if conversacion.usuario_id is not None:
        if usuario is None or usuario.id != conversacion.usuario_id:
            raise PermisoDenegado("Esa conversación no te pertenece.")

    if len(conversacion.mensajes) >= crud_chat.MENSAJES_MAXIMOS:
        raise DatosInvalidos(
            "Esta conversación llegó a su límite de mensajes. Abre una nueva "
            "para seguir."
        )

    pregunta = await crud_chat.anotar(sesion, conversacion, "usuario", datos.contenido)

    productos, servicios = await crud_chat.datos_del_negocio(sesion)
    ficha = asistente.construir_ficha(productos, servicios)

    await sesion.refresh(conversacion)
    historial = await crud_chat.historial_para_modelo(conversacion)

    texto = await asistente.responder(ficha, historial)
    respuesta = await crud_chat.anotar(sesion, conversacion, "asistente", texto)

    return SobreChat(
        chat=RespuestaChat(
            conversacion_id=conversacion.id,
            pregunta=MensajeSalida.model_validate(pregunta),
            respuesta=MensajeSalida.model_validate(respuesta),
        )
    )


@router.get(
    "/conversaciones",
    response_model=SobreConversaciones,
    summary="Mis conversaciones",
    responses=respuestas(NO_AUTENTICADO, SIN_PERMISO, NO_VALIDO),
)
async def listar(
    sesion: SesionDep, usuario: UsuarioActual, pagina: PaginaDep
) -> SobreConversaciones:
    """Solo con sesión: un visitante no tiene lista que consultar."""
    total = await crud_chat.contar(sesion, usuario.id)
    conversaciones = await crud_chat.listar(
        sesion, usuario.id, limite=pagina.limite, desplazamiento=pagina.desplazamiento
    )
    return SobreConversaciones(
        conversaciones=[
            ConversacionSalida.desde_modelo(c, con_mensajes=False)
            for c in conversaciones
        ],
        total=total,
        pagina=pagina.resultado(total),
    )


@router.get(
    "/conversaciones/{conversacion_id}",
    response_model=SobreConversacion,
    summary="Leer una conversación",
    responses=respuestas(NO_AUTENTICADO, SIN_PERMISO, NO_ENCONTRADO),
)
async def leer(
    conversacion: ConversacionRuta, usuario: UsuarioOpcional
) -> SobreConversacion:
    _exigir_dueno(usuario, conversacion)
    return SobreConversacion(
        conversacion=ConversacionSalida.desde_modelo(conversacion)
    )


@router.delete(
    "/conversaciones/{conversacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una conversación",
    responses=respuestas(NO_AUTENTICADO, SIN_PERMISO, NO_ENCONTRADO),
)
async def eliminar(
    conversacion: ConversacionRuta, sesion: SesionDep, usuario: UsuarioOpcional
) -> Response:
    _exigir_dueno(usuario, conversacion)
    await crud_chat.eliminar(sesion, conversacion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
