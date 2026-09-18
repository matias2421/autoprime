"""Esquemas de reportes y tableros.

Lo que sale de aquí alimenta las gráficas del panel. Por eso la serie diaria
llega con los días vacíos incluidos y no solo los que tuvieron ventas: una
gráfica de líneas que salta del día 3 al 9 dibuja una pendiente suave donde
hubo una semana a cero.
"""

from datetime import date

from app.schemas.comunes import Dinero, Esquema
from app.schemas.venta import ResumenVentas


class PuntoDiario(Esquema):
    fecha: date
    ventas: int
    ingresos: Dinero


class CorteEstado(Esquema):
    estado: str
    ventas: int
    importe: Dinero


class CorteConcepto(Esquema):
    """Una fila del ranking: un modelo de vehículo o un servicio."""

    descripcion: str
    unidades: int
    importe: Dinero


class Rango(Esquema):
    desde: date
    hasta: date
    dias: int


class ReporteVentas(Esquema):
    """Todo lo que el tablero de ventas necesita, en una sola petición.

    Se devuelve junto y no en cinco endpoints porque el panel los pinta a la
    vez: cinco peticiones serían cinco viajes, cinco estados de carga y cinco
    formas de quedarse a medias si una falla.
    """

    rango: Rango

    # De quien son estas cifras. El panel lo usa como subtitulo, y sirve
    # para que un cliente vea claro que esta mirando sus compras y no las
    # del negocio: el mismo endpoint devuelve una cosa u otra segun el rol.
    alcance: str

    resumen: ResumenVentas
    por_dia: list[PuntoDiario]
    por_estado: list[CorteEstado]
    top_vehiculos: list[CorteConcepto]
    top_servicios: list[CorteConcepto]


class PanelAdministrativo(Esquema):
    """Cifras de cabecera del tablero del administrador."""

    usuarios_activos: int
    vehiculos_disponibles: int
    vehiculos_vendidos: int
    citas_pendientes: int
    pqr_abiertas: int
    facturas_emitidas: int
    ventas_hoy: int
    ingresos_hoy: Dinero


class SobreReporteVentas(Esquema):
    reporte: ReporteVentas


class SobrePanel(Esquema):
    panel: PanelAdministrativo
