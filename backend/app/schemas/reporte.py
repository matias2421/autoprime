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


class Comparacion(Esquema):
    """Las mismas cifras del tramo anterior, de igual duracion.

    Existe porque «$50 mil M» no dice si el periodo fue bueno. Al lado de lo
    que se hizo en el tramo anterior, si; y esa era la primera pregunta de
    cualquiera que abria el reporte, que hasta ahora obligaba a generar un
    segundo reporte y comparar a ojo.
    """

    desde: date
    hasta: date
    total: int
    ingresos: Dinero
    ticket_promedio: Dinero


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
    comparacion: Comparacion | None = None
    por_dia: list[PuntoDiario]
    por_estado: list[CorteEstado]
    top_vehiculos: list[CorteConcepto]
    top_servicios: list[CorteConcepto]


class PanelAdministrativo(Esquema):
    """Cifras de cabecera del tablero del administrador.

    Van en tres grupos porque responden a tres preguntas distintas: como va
    hoy, que hay que hacer, y como esta el negocio. Un panel donde las doce
    cifras tienen el mismo aspecto obliga a leerlas todas para encontrar la
    que importa.
    """

    # Como va hoy. Las de ayer estan para que las de hoy signifiquen algo:
    # «4 ventas» no dice si el dia va bien hasta que se sabe que ayer hubo 2.
    ventas_hoy: int
    ingresos_hoy: Dinero
    ventas_ayer: int
    ingresos_ayer: Dinero

    # Que espera una accion de alguien. Esto es la lista de pendientes del
    # negocio, y es lo unico del panel sobre lo que se puede actuar hoy.
    ventas_por_cobrar: int
    importe_por_cobrar: Dinero
    ventas_sin_facturar: int
    citas_pendientes: int
    pqr_abiertas: int

    # Como esta el negocio.
    usuarios_activos: int
    vehiculos_disponibles: int
    vehiculos_vendidos: int
    valor_inventario: Dinero
    facturas_emitidas: int


class SobreReporteVentas(Esquema):
    reporte: ReporteVentas


class SobrePanel(Esquema):
    panel: PanelAdministrativo
