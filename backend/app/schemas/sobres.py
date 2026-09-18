"""Sobres de respuesta.

El backend anterior devolvía cada recurso dentro de una clave con su nombre
(`{"usuarios": [...]}`), y el frontend lo lee así desde el tercer avance.
Se conserva ese contrato para que el cambio de Express a FastAPI no obligue
a tocar ni un componente de React.
"""

from app.schemas.cita import CitaSalida, FranjaDisponible, ResumenCitas
from app.schemas.comunes import Esquema
from app.schemas.factura import FacturaSalida
from app.schemas.paginacion import Pagina
from app.schemas.producto import ProductoSalida
from app.schemas.servicio import ServicioSalida
from app.schemas.usuario import UsuarioSalida
from app.schemas.venta import ResumenVentas, VentaSalida


class SobreUsuarios(Esquema):
    usuarios: list[UsuarioSalida]
    total: int


class SobreUsuario(Esquema):
    usuario: UsuarioSalida


class SobreProductos(Esquema):
    productos: list[ProductoSalida]
    total: int


class SobreProducto(Esquema):
    producto: ProductoSalida


class SobreServicios(Esquema):
    servicios: list[ServicioSalida]
    total: int


class SobreServicio(Esquema):
    servicio: ServicioSalida


class SobreCitas(Esquema):
    citas: list[CitaSalida]
    total: int


class SobreCita(Esquema):
    cita: CitaSalida


class SobreResumen(Esquema):
    resumen: ResumenCitas


class SobreDisponibilidad(Esquema):
    fecha: str
    horas: list[FranjaDisponible]


# --- Quinto avance ---
#
# Estos listados sí pueden crecer, así que además del total llevan `pagina`
# con lo que el paginador necesita para dibujarse.


class SobreVentas(Esquema):
    ventas: list[VentaSalida]
    total: int
    pagina: Pagina


class SobreVenta(Esquema):
    venta: VentaSalida


class SobreResumenVentas(Esquema):
    resumen: ResumenVentas


class SobreFacturas(Esquema):
    facturas: list[FacturaSalida]
    total: int
    pagina: Pagina


class SobreFactura(Esquema):
    factura: FacturaSalida
