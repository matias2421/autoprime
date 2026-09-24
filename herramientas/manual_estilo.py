# -*- coding: utf-8 -*-
"""Estilos y piezas de composición del Manual Técnico.

Vive aparte del generador para que las secciones puedan usarlo sin que se
forme un círculo de importaciones: `manual_secciones` necesita los estilos,
y `manual_tecnico` necesita las secciones.

El formato lo fija la solicitud del instructor: Times New Roman a 11 pt,
interlineado 1.15, márgenes estándar y encabezado institucional.
"""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, Paragraph, Table, TableStyle

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURAS = os.path.join(RAIZ, "evidencias", "capturas-quinta")

MARGEN = 2.5 * cm
ANCHO_UTIL = A4[0] - 2 * MARGEN

GRIS = colors.HexColor("#595959")
LINEA = colors.HexColor("#BFBFBF")
CABECERA = colors.HexColor("#1F3864")
FONDO_TABLA = colors.HexColor("#EDF0F7")


def construir_estilos():
    """11 pt con interlineado 1.15, que son 12.65 puntos.

    Poner «1.15» en un procesador de texto y poner 12.65 puntos aquí es lo
    mismo; la diferencia es que esto no depende de cómo lo interprete el
    programa que abra el archivo.
    """
    hojas = getSampleStyleSheet()
    interlineado = 11 * 1.15

    estilos = {
        "cuerpo": ParagraphStyle(
            "cuerpo", parent=hojas["Normal"], fontName="Times-Roman",
            fontSize=11, leading=interlineado, alignment=TA_JUSTIFY,
            spaceAfter=7),
        "h1": ParagraphStyle(
            "h1", parent=hojas["Heading1"], fontName="Times-Bold",
            fontSize=15, leading=18, textColor=CABECERA,
            spaceBefore=16, spaceAfter=10, keepWithNext=1),
        "h2": ParagraphStyle(
            "h2", parent=hojas["Heading2"], fontName="Times-Bold",
            fontSize=12.5, leading=15, textColor=colors.black,
            spaceBefore=12, spaceAfter=6, keepWithNext=1),
        "h3": ParagraphStyle(
            "h3", parent=hojas["Heading3"], fontName="Times-BoldItalic",
            fontSize=11, leading=13, textColor=GRIS,
            spaceBefore=9, spaceAfter=4, keepWithNext=1),
        "lista": ParagraphStyle(
            "lista", parent=hojas["Normal"], fontName="Times-Roman",
            fontSize=11, leading=interlineado, alignment=TA_JUSTIFY,
            leftIndent=16, bulletIndent=4, spaceAfter=4),
        "pie": ParagraphStyle(
            "pie", parent=hojas["Normal"], fontName="Times-Italic",
            fontSize=9, leading=11, textColor=GRIS, alignment=TA_CENTER,
            spaceBefore=4, spaceAfter=12),
        "codigo": ParagraphStyle(
            "codigo", parent=hojas["Normal"], fontName="Courier",
            fontSize=8.5, leading=11, leftIndent=10, spaceAfter=6,
            textColor=colors.HexColor("#243447")),
        "celda": ParagraphStyle(
            "celda", parent=hojas["Normal"], fontName="Times-Roman",
            fontSize=8.5, leading=10.5),
        "celdaCabecera": ParagraphStyle(
            "celdaCabecera", parent=hojas["Normal"], fontName="Times-Bold",
            fontSize=8.5, leading=10.5, textColor=colors.white),
        "portadaTitulo": ParagraphStyle(
            "portadaTitulo", parent=hojas["Normal"], fontName="Times-Bold",
            fontSize=26, leading=30, alignment=TA_CENTER,
            textColor=CABECERA, spaceAfter=6),
        "portadaSub": ParagraphStyle(
            "portadaSub", parent=hojas["Normal"], fontName="Times-Italic",
            fontSize=14, leading=18, alignment=TA_CENTER,
            textColor=GRIS, spaceAfter=26),
        "portadaCentro": ParagraphStyle(
            "portadaCentro", parent=hojas["Normal"], fontName="Times-Roman",
            fontSize=11.5, leading=16, alignment=TA_CENTER),
    }
    # Un título que se ve como un h1 pero NO entra en la tabla de contenido.
    #
    # Hace falta porque el índice se construye recogiendo todo lo que tenga
    # estilo «h1» u «h2», y el encabezado de la propia página del índice
    # cumplía esa condición: la tabla de contenido se listaba a sí misma
    # como primera entrada, apuntando a su propia página.
    estilos["tituloSuelto"] = ParagraphStyle(
        "tituloSuelto", parent=estilos["h1"])

    # Dos niveles en la tabla de contenido: capítulo y apartado.
    estilos["toc1"] = ParagraphStyle(
        "toc1", fontName="Times-Bold", fontSize=11, leading=14,
        leftIndent=0, firstLineIndent=-14, spaceBefore=3)
    estilos["toc2"] = ParagraphStyle(
        "toc2", fontName="Times-Roman", fontSize=10.5, leading=12.5,
        leftIndent=20, firstLineIndent=-14, textColor=GRIS)
    return estilos


ESTILOS = construir_estilos()


# ---------------------------------------------------------------------------
# Atajos
# ---------------------------------------------------------------------------
def p(texto):
    return Paragraph(texto, ESTILOS["cuerpo"])


def h1(texto):
    return Paragraph(texto, ESTILOS["h1"])


def h2(texto):
    return Paragraph(texto, ESTILOS["h2"])


def h3(texto):
    return Paragraph(texto, ESTILOS["h3"])


def vinetas(elementos):
    return [Paragraph(t, ESTILOS["lista"], bulletText="•")
            for t in elementos]


def numerada(elementos):
    return [Paragraph(t, ESTILOS["lista"], bulletText="%d." % (i + 1))
            for i, t in enumerate(elementos)]


def codigo(lineas):
    """Bloque monoespaciado. Los espacios se conservan a propósito."""
    escapado = []
    for linea in lineas:
        texto = (linea.replace("&", "&amp;").replace("<", "&lt;")
                      .replace(">", "&gt;").replace(" ", "&nbsp;"))
        escapado.append(texto)
    return Paragraph("<br/>".join(escapado), ESTILOS["codigo"])


def tabla(cabeceras, filas, anchos):
    """Tabla con cabecera azul, filas alternas y cabecera repetida.

    `repeatRows` importa más de lo que parece: sin eso, una tabla que pasa de
    página deja al lector sin saber qué columna es cuál a partir de la
    segunda, y el diccionario de datos ocupa varias páginas.
    """
    cuerpo = [[Paragraph(str(c), ESTILOS["celdaCabecera"]) for c in cabeceras]]
    for fila in filas:
        cuerpo.append([Paragraph(str(c), ESTILOS["celda"]) for c in fila])

    t = Table(cuerpo, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), CABECERA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(cuerpo), 2):
        estilo.append(("BACKGROUND", (0, i), (-1, i), FONDO_TABLA))
    t.setStyle(TableStyle(estilo))
    return t


def captura(nombre, pie, proporcion_ancho=1.0):
    """Incrusta una captura escalada al ancho útil, con su pie.

    Si falta, el documento lo dice en su sitio. Un hueco silencioso sería
    peor: nadie se enteraría hasta tener el manual impreso delante.
    """
    ruta = os.path.join(CAPTURAS, nombre + ".png")
    if not os.path.isfile(ruta):
        return [p("<i>[Falta la captura %s.png. Se genera con "
                  "herramientas/capturas_quinta.py]</i>" % nombre)]

    from PIL import Image as Lienzo
    with Lienzo.open(ruta) as imagen:
        alto_sobre_ancho = imagen.height / float(imagen.width)

    ancho = ANCHO_UTIL * proporcion_ancho
    figura = Image(ruta, width=ancho, height=ancho * alto_sobre_ancho)
    figura.hAlign = "CENTER"
    return [KeepTogether([figura, Paragraph(pie, ESTILOS["pie"])])]
