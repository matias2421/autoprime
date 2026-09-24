"""Esquemas del chat."""

from datetime import datetime

from pydantic import Field

from app.schemas.comunes import con_ejemplo, Esquema


class MensajeCrear(Esquema):
    """Cuerpo de `POST /api/chat/{conversacion_id}/mensajes`.

    El tope de longitud no es estético: el texto viaja al proveedor y se paga
    por lo que ocupa, así que un cuerpo sin límite es una factura sin límite.
    """

    model_config = con_ejemplo(
        contenido="¿Qué vehículos tienen disponibles?",
    )

    contenido: str = Field(min_length=1, max_length=1500)


class ConversacionCrear(Esquema):
    titulo: str | None = Field(default=None, max_length=120)


class MensajeSalida(Esquema):
    id: int
    rol: str
    contenido: str
    creado_en: datetime


class ConversacionSalida(Esquema):
    id: int
    usuario_id: int | None
    titulo: str | None
    creado_en: datetime
    ultima_actividad: datetime
    mensajes: list[MensajeSalida] = []

    @classmethod
    def desde_modelo(cls, c, con_mensajes: bool = True) -> "ConversacionSalida":
        return cls(
            id=c.id,
            usuario_id=c.usuario_id,
            titulo=c.titulo,
            creado_en=c.creado_en,
            ultima_actividad=c.ultima_actividad,
            mensajes=(
                [MensajeSalida.model_validate(m) for m in c.mensajes]
                if con_mensajes
                else []
            ),
        )


class RespuestaChat(Esquema):
    """Lo que devuelve enviar un mensaje: el par pregunta-respuesta.

    Se devuelven los dos y no solo la respuesta para que el frontend pinte la
    conversación con lo que quedó guardado, no con lo que él creía haber
    enviado: si el servidor recortó o normalizó algo, la pantalla lo refleja.
    """

    conversacion_id: int
    pregunta: MensajeSalida
    respuesta: MensajeSalida
