"""Freno de peticiones para el chat.

El chat es el único endpoint público que cuesta dinero por uso: cada mensaje
es una llamada a un proveedor que factura por tokens. Sin freno, una pestaña
con un bucle —o alguien con curiosidad y un `for`— agota la cuota en un rato,
y el chat deja de funcionar para todos los demás.

Lo que hay aquí es una ventana deslizante en memoria: por cada origen se
guardan las marcas de tiempo de sus últimos mensajes y se cuentan las que
caen dentro del último minuto.

**Sus límites, dichos claramente.** Vive en la memoria del proceso, así que:
con varios trabajadores cada uno lleva su propia cuenta y el límite real se
multiplica por el número de procesos; y al reiniciar, la cuenta se pierde.
Para hacerlo bien haría falta un contador compartido (Redis o similar), que
es una pieza más que desplegar y mantener. Para un plan gratuito de un solo
proceso, esto cubre el caso que importa —el bucle accidental y el abuso
casual— y no pretende cubrir el que no —un abuso repartido y deliberado—.
"""

import time
from collections import defaultdict, deque

# Marcas de tiempo por origen, la más antigua delante.
_visitas: dict[str, deque[float]] = defaultdict(deque)

# Cuántos orígenes distintos se recuerdan. Sin este tope, el diccionario
# crece con cada IP que pasa y no lo vacía nadie: una fuga de memoria lenta
# con forma de defensa.
ORIGENES_MAXIMOS = 5000


def permitido(origen: str, cupo: int, ventana: float = 60.0) -> tuple[bool, int]:
    """¿Puede este origen hacer una petición más?

    Devuelve si se le deja pasar y cuántos segundos faltan para que se libere
    un hueco, que es lo que hay que poner en la cabecera `Retry-After` para
    que quien llama sepa cuándo reintentar en vez de golpear a ciegas.
    """
    ahora = time.monotonic()
    marcas = _visitas[origen]

    while marcas and ahora - marcas[0] >= ventana:
        marcas.popleft()

    if len(marcas) >= cupo:
        return False, max(1, int(ventana - (ahora - marcas[0])) + 1)

    marcas.append(ahora)

    if len(_visitas) > ORIGENES_MAXIMOS:
        _limpiar(ahora, ventana)

    return True, 0


def _limpiar(ahora: float, ventana: float) -> None:
    """Suelta los orígenes que ya no tienen marcas vivas."""
    caducados = [
        origen
        for origen, marcas in _visitas.items()
        if not marcas or ahora - marcas[-1] >= ventana
    ]
    for origen in caducados:
        del _visitas[origen]


def reiniciar() -> None:
    """Vacía el contador. Solo lo usan las pruebas."""
    _visitas.clear()
