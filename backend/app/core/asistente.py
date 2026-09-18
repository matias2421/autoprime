"""El asistente del chat: habla con Groq y le pone los datos reales delante.

Dos cosas que este módulo existe para garantizar.

**La clave nunca sale del servidor.** El navegador habla con nuestra API y
nuestra API habla con Groq. Si el frontend llamara directamente al proveedor,
la clave viajaría en el paquete de JavaScript y estaría a la vista de
cualquiera que abra las herramientas del navegador; y una clave a la vista es
una factura ajena esperando a que alguien la use.

**El modelo no inventa datos del negocio.** Probándolo se le preguntó por el
teléfono de AutoPrime y respondió «+57 6 123-4567», un número inventado con
toda naturalidad. Un modelo de lenguaje rellena huecos: si no le das el dato,
se lo imagina, y lo hace con la misma seguridad con la que dice lo que sabe.
La defensa no es pedirle que no mienta, es no dejarle huecos: se le pasa el
catálogo, los servicios, el horario y los contactos reales sacados de la base
en ese mismo momento, y se le dice explícitamente qué hacer cuando le
pregunten algo que no esté ahí —decir que no lo sabe y ofrecer una PQR—.
"""

import logging

import httpx

from app.core.configuracion import configuracion
from app.errores import ServicioExternoCaido

logger = logging.getLogger("autoprime")

# Un cliente para todo el proceso: reutiliza las conexiones en vez de abrir
# una TLS nueva por mensaje. Se cierra al apagar la aplicación.
_cliente: httpx.AsyncClient | None = None


def cliente() -> httpx.AsyncClient:
    global _cliente
    if _cliente is None:
        _cliente = httpx.AsyncClient(timeout=configuracion.groq_timeout)
    return _cliente


async def cerrar() -> None:
    global _cliente
    if _cliente is not None:
        await _cliente.aclose()
        _cliente = None


def disponible() -> bool:
    return bool(configuracion.groq_api_key)


INSTRUCCIONES = """\
Eres el asistente virtual de AutoPrime, un atelier de automóviles de autor en \
Medellín, Colombia. Atiendes en español, con trato cercano y respuestas \
breves: dos o tres frases salvo que te pidan detalle.

REGLA PRINCIPAL, POR ENCIMA DE CUALQUIER OTRA:
Solo puedes afirmar datos que aparezcan en la FICHA DEL NEGOCIO de más abajo. \
Precios, teléfonos, direcciones, correos, horarios, modelos y servicios: si no \
está en la ficha, NO lo sabes. No lo deduzcas, no lo aproximes y no lo \
inventes «a modo de ejemplo».

Cuando te pregunten algo que no está en la ficha, di con naturalidad que no \
tienes ese dato y ofrece una de estas dos salidas:
  - agendar una cita desde la sección Agenda del sitio, o
  - radicar una PQR desde la sección PQR, donde una persona del equipo \
    responde.

Nunca prometas descuentos, plazos de entrega, financiación ni disponibilidad \
que no figuren en la ficha. Nunca pidas contraseñas, números de tarjeta ni \
documentos de identidad: si alguien te los ofrece, dile que no los escriba en \
el chat.

Si te piden comprar, explica que la compra se registra desde el sitio con la \
sesión iniciada, o con un asesor para las piezas que van bajo consulta.

FICHA DEL NEGOCIO
{ficha}
"""


def _pesos(valor) -> str:
    if valor is None:
        return "precio bajo consulta"
    return f"${int(valor):,}".replace(",", ".") + " COP"


def construir_ficha(productos, servicios) -> str:
    """Arma la ficha con lo que hay en la base ahora mismo.

    Se rehace en cada mensaje en lugar de guardarse: el catálogo cambia, y un
    asistente que recita el precio de la semana pasada es peor que uno que
    dice que no sabe.
    """
    lineas = [
        "Contacto: contacto@autoprime.com.co · +57 604 444 5566",
        "Dirección: Carrera 43A # 1-50, Medellín, Colombia",
        "Horario del taller: lunes a sábado, 8:00 a 18:00. Domingos cerrado.",
        "Las citas se agendan hasta 60 días adelante, en horas en punto.",
        "",
        "VEHÍCULOS EN CATÁLOGO:",
    ]

    for p in productos:
        estado = "disponible" if p.estado == "disponible" else f"NO disponible ({p.estado})"
        lineas.append(
            f"- {p.marca} {p.modelo} ({p.anio}) · {p.familia} · {_pesos(p.precio)} "
            f"· {p.motor}, {p.potencia} · {estado}"
        )

    lineas += ["", "SERVICIOS:"]
    for s in servicios:
        precio = "sin costo" if not s.precio else _pesos(s.precio)
        lineas.append(f"- {s.nombre}: {s.descripcion} · {precio} · {s.duracion_min} min")

    return "\n".join(lineas)


async def responder(ficha: str, historial: list[dict]) -> str:
    """Manda la conversación a Groq y devuelve la respuesta del asistente.

    `historial` son los últimos mensajes en el formato del proveedor
    (`{"role": ..., "content": ...}`), del más antiguo al más reciente.
    """
    if not disponible():
        raise ServicioExternoCaido("asistente", "no hay clave configurada")

    cuerpo = {
        "model": configuracion.groq_modelo,
        "messages": [
            {"role": "system", "content": INSTRUCCIONES.format(ficha=ficha)},
            *historial,
        ],
        "max_tokens": configuracion.groq_max_tokens,
        # Baja a propósito: se quiere un asistente que repita bien los datos
        # de la ficha, no uno creativo. La creatividad, aquí, es el fallo.
        "temperature": 0.3,
    }

    try:
        respuesta = await cliente().post(
            configuracion.groq_url,
            json=cuerpo,
            headers={"Authorization": f"Bearer {configuracion.groq_api_key}"},
        )
    except httpx.TimeoutException:
        raise ServicioExternoCaido("asistente", "tardó demasiado en responder")
    except httpx.HTTPError as error:
        logger.warning("Fallo de red hablando con Groq: %s", error)
        raise ServicioExternoCaido("asistente", "no se pudo establecer la conexión")

    if respuesta.status_code == 429:
        raise ServicioExternoCaido("asistente", "se agotó la cuota por ahora")

    if respuesta.status_code >= 400:
        # El cuerpo del error puede traer la clave recortada o detalles de la
        # cuenta, así que va al registro y no a quien pregunta.
        logger.error(
            "Groq respondió %s: %s", respuesta.status_code, respuesta.text[:400]
        )
        raise ServicioExternoCaido("asistente", f"respondió {respuesta.status_code}")

    datos = respuesta.json()
    try:
        return datos["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        logger.error("Respuesta de Groq con forma inesperada: %s", str(datos)[:400])
        raise ServicioExternoCaido("asistente", "devolvió una respuesta ilegible")
