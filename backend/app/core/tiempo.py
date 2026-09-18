"""El reloj del negocio. Uno solo, y explícito.

El fallo que esto arregla no se ve desarrollando y aparece de noche. Hasta
ahora las marcas de tiempo las ponía MySQL con `CURRENT_TIMESTAMP`, y el
servidor de Aiven corre en UTC; las fechas de los reportes las ponía Python
con `date.today()`, y este portátil corre en hora de Colombia. Son dos relojes
con cinco horas de diferencia, así que una venta hecha a las 8 de la noche
quedaba fechada al día siguiente y el reporte diario —que preguntaba por hoy—
no la encontraba. El reporte salía en blanco sin dar ningún error.

En Render el desajuste es el contrario: allí el contenedor también va en UTC,
así que la API y la base coinciden, pero las dos van cinco horas por delante
de la persona que mira la pantalla en Medellín. El «reporte de hoy» sería el
de un día que aún no ha empezado.

Con un solo reloj declarado —el del negocio, que está en Colombia— los tres
sitios dicen lo mismo: el portátil, el contenedor y la base.

Colombia no aplica horario de verano: lo intentó en 1992 y lo dejó al año
siguiente. Su desfase es −05:00 todo el año, y por eso el respaldo de más
abajo es exacto y no una aproximación.
"""

import logging
from datetime import date, datetime, time, timedelta, timezone

logger = logging.getLogger("autoprime")

ZONA_NOMBRE = "America/Bogota"

try:
    from zoneinfo import ZoneInfo

    ZONA = ZoneInfo(ZONA_NOMBRE)
except Exception:  # pragma: no cover — instalación sin base de zonas
    # En Windows, `zoneinfo` necesita el paquete `tzdata`; sin él no hay
    # ninguna zona. Se sigue con el desfase fijo, que para Colombia es el
    # mismo dato, y se avisa: la instalación está incompleta aunque funcione.
    ZONA = timezone(timedelta(hours=-5), name="-05")
    logger.warning(
        "Sin base de zonas horarias (falta el paquete tzdata). Se usa el "
        "desfase fijo -05:00, exacto para Colombia."
    )


def ahora() -> datetime:
    """La hora local del negocio, sin zona pegada.

    Se devuelve «ingenua» a propósito: las columnas son `DATETIME` y MySQL no
    guarda zona. Pegarle una aquí daría la falsa impresión de que la base
    conserva esa información, y al releer la fila volvería sin ella.
    """
    return datetime.now(ZONA).replace(tzinfo=None)


def hoy() -> date:
    """El día de hoy en Colombia, corra esto donde corra."""
    return ahora().date()


def inicio_del_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min)


def fin_del_dia(dia: date) -> datetime:
    """El último instante del día, con segundos enteros.

    `time.max` trae .999999, y MySQL redondea los microsegundos al segundo
    más cercano cuando la columna no guarda fracciones: ese valor se
    convertiría en las 00:00:00 del día siguiente y el rango abarcaría un
    día de más.
    """
    return datetime.combine(dia, time(23, 59, 59))
