"""Identidad de los documentos que genera la API, y formato de cifras.

El sitio es negro con acento azul. Un documento no puede serlo: se imprime.
Una factura con fondo negro gasta un cartucho por página, se lee peor en
papel y es lo primero que alguien tacha cuando la archiva. Así que los
documentos van al revés —papel blanco, tinta oscura— y la marca aparece solo
donde hace falta: la banda del encabezado y las reglas de las tablas.

El azul es el mismo `--color-accion-fondo` del sitio (#3d6274) y no el claro:
el claro está calculado para contrastar sobre negro, y sobre blanco se queda
en 2.4:1, ilegible. El oscuro da 6.3:1 sobre blanco.
"""

from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm

# --- Paleta ---
TINTA = colors.HexColor("#111114")
TINTA_SUAVE = colors.HexColor("#55555c")
ACENTO = colors.HexColor("#3d6274")
ACENTO_TENUE = colors.HexColor("#e8eef1")
LINEA = colors.HexColor("#d5d5db")
PAPEL = colors.white

MARGEN = 18 * mm

EMPRESA = {
    "nombre": "AutoPrime",
    "lema": "Atelier de automóviles de autor",
    "nit": "NIT 901.456.789-1",
    "direccion": "Carrera 43A # 1-50, Medellín, Colombia",
    "contacto": "contacto@autoprime.com.co  ·  +57 604 444 5566",
}


def estilos() -> dict:
    """Los estilos de párrafo del documento, ya armados."""
    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "titulo",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=TINTA,
            spaceAfter=2,
            alignment=0,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=TINTA_SUAVE,
        ),
        "seccion": ParagraphStyle(
            "seccion",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=ACENTO,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "cuerpo": ParagraphStyle(
            "cuerpo",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=TINTA,
        ),
        "celda": ParagraphStyle(
            "celda",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TINTA,
        ),
        "celda_derecha": ParagraphStyle(
            "celda_derecha",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TINTA,
            alignment=TA_RIGHT,
        ),
        "pie": ParagraphStyle(
            "pie",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=TINTA_SUAVE,
            alignment=TA_CENTER,
        ),
    }


def pesos(valor) -> str:
    """Formato colombiano: punto para los miles, coma para los decimales.

    Python hace lo contrario por defecto, así que se intercambian. Sin esto,
    «$ 3,200,000,000.00» se lee como tres coma dos en media Europa y como
    tres mil doscientos millones en Colombia: el mismo texto, dos cifras.
    """
    numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    entero, _, decimales = f"{numero:,.2f}".partition(".")
    entero = entero.replace(",", ".")
    return f"$ {entero},{decimales}"


def numero(valor) -> str:
    """Un entero con separador de miles, sin símbolo de moneda."""
    return f"{int(valor or 0):,}".replace(",", ".")
