# -*- coding: utf-8 -*-
"""Los dos diagramas del Manual Técnico, dibujados con reportlab.

Se dibujan en vez de incrustar una imagen por una razón práctica: una imagen
exportada de una herramienta de diagramas se queda vieja en cuanto cambia el
esquema, y nadie la regenera. Esto se compone cada vez que se lanza el
generador, y el de entidad-relación LEE las tablas de SQLAlchemy: si mañana
aparece una columna nueva, aparece sola.

Van en vectorial, así que se pueden ampliar sin que se deshagan.
"""

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors

AZUL = colors.HexColor("#1F3864")
AZUL_SUAVE = colors.HexColor("#DCE3F0")
VERDE = colors.HexColor("#2E6B4F")
VERDE_SUAVE = colors.HexColor("#DDEBE3")
AMBAR = colors.HexColor("#8A6410")
AMBAR_SUAVE = colors.HexColor("#F6EBD3")
GRIS = colors.HexColor("#595959")
GRIS_SUAVE = colors.HexColor("#EFEFEF")
LINEA = colors.HexColor("#8C8C8C")


# ---------------------------------------------------------------------------
# Piezas sueltas
# ---------------------------------------------------------------------------
def _caja(dibujo, x, y, ancho, alto, titulo, subtitulo="", borde=AZUL,
          fondo=AZUL_SUAVE, tamano=8.5):
    dibujo.add(Rect(x, y, ancho, alto, fillColor=fondo, strokeColor=borde,
                    strokeWidth=0.9))
    centro = x + ancho / 2.0
    if subtitulo:
        dibujo.add(String(centro, y + alto - 12, titulo, fontName="Times-Bold",
                          fontSize=tamano, fillColor=borde, textAnchor="middle"))
        for i, linea in enumerate(subtitulo.split("\n")):
            dibujo.add(String(centro, y + alto - 22 - i * 9, linea,
                              fontName="Times-Roman", fontSize=tamano - 1,
                              fillColor=GRIS, textAnchor="middle"))
    else:
        dibujo.add(String(centro, y + alto / 2.0 - 3, titulo,
                          fontName="Times-Bold", fontSize=tamano,
                          fillColor=borde, textAnchor="middle"))


def _flecha(dibujo, x1, y1, x2, y2, etiqueta="", punteada=False, color=LINEA):
    guion = (2, 2) if punteada else None
    dibujo.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.9,
                    strokeDashArray=guion))

    # Punta: un triángulo orientado según el tramo.
    import math
    angulo = math.atan2(y2 - y1, x2 - x1)
    largo, medio = 6.0, 2.6
    px = x2 - largo * math.cos(angulo)
    py = y2 - largo * math.sin(angulo)
    dibujo.add(Polygon([
        x2, y2,
        px - medio * math.sin(angulo), py + medio * math.cos(angulo),
        px + medio * math.sin(angulo), py - medio * math.cos(angulo),
    ], fillColor=color, strokeColor=color))

    if etiqueta:
        dibujo.add(String((x1 + x2) / 2.0, (y1 + y2) / 2.0 + 3, etiqueta,
                          fontName="Times-Italic", fontSize=7,
                          fillColor=GRIS, textAnchor="middle"))


# ---------------------------------------------------------------------------
# 1. Arquitectura
# ---------------------------------------------------------------------------
def diagrama_arquitectura(ancho=453):
    """Las cuatro capas y con qué habla cada una."""
    alto = 330
    d = Drawing(ancho, alto)
    centro = ancho / 2.0

    # La columna central y las dos laterales se reparten el ancho DEJANDO
    # hueco entre ellas. La primera versión puso 250 de centro y 128 a cada
    # lado sobre 453 de ancho: no cabían, las cajas laterales se montaban
    # encima de la de la API y las flechas que debían cruzar el hueco medían
    # menos que su propia punta.
    hueco = 26.0
    cajaAncho = 190.0
    anchoLado = (ancho - cajaAncho - 2 * hueco) / 2.0
    x = centro - cajaAncho / 2.0
    xDer = x + cajaAncho + hueco

    # --- Capa 1: quien usa ---
    _caja(d, x, 285, cajaAncho, 38, "NAVEGADOR",
          "Cliente · Empleado · Administrador", AZUL, AZUL_SUAVE)

    # --- Capa 2: frontend ---
    _caja(d, x, 220, cajaAncho, 46, "FRONTEND  ·  React 19 + Vite 8",
          "Tailwind CSS 4 · React Router 7\nDesplegado en Vercel", AZUL, colors.white)
    _flecha(d, centro, 285, centro, 266)

    # --- Capa 3: API ---
    _caja(d, x, 145, cajaAncho, 52, "API  ·  FastAPI (Python 3.12)",
          "Pydantic v2 · JWT · bcrypt\nDesplegada en Render", VERDE, VERDE_SUAVE)
    _flecha(d, centro, 220, centro, 197, "HTTPS · JSON")

    # --- Capa 4: base ---
    _caja(d, x, 62, cajaAncho, 46, "BASE DE DATOS  ·  MySQL 8",
          "SQLAlchemy 2.0 asíncrono (aiomysql)\nAiven · enlace cifrado con TLS",
          VERDE, colors.white)
    _flecha(d, centro, 145, centro, 108, "SQL parametrizado")

    # --- Servicios externos, a la derecha: la API sale hacia ellos ---
    _caja(d, xDer, 148, anchoLado, 46, "SERVICIOS EXTERNOS",
          "Groq · asistente IA\nSMTP · correo\nFestivos · agenda",
          AMBAR, AMBAR_SUAVE, tamano=8)
    _flecha(d, x + cajaAncho, 171, xDer, 171, "HTTPS", punteada=True)

    # --- Documentos que produce, a la izquierda ---
    _caja(d, 0, 148, anchoLado, 46, "DOCUMENTOS",
          "PDF · reportlab\nExcel · XlsxWriter\n(los genera la API)",
          AMBAR, AMBAR_SUAVE, tamano=8)
    # De la API HACIA los documentos, no al revés: la flecha sale del borde
    # izquierdo de la API y termina en el borde derecho de la caja.
    _flecha(d, x, 171, anchoLado, 171, punteada=True)

    # --- Nota de seguridad, abajo ---
    d.add(Rect(0, 0, ancho, 40, fillColor=GRIS_SUAVE, strokeColor=LINEA,
               strokeWidth=0.6))
    d.add(String(centro, 26, "Capa transversal de seguridad",
                 fontName="Times-Bold", fontSize=8.5, fillColor=GRIS,
                 textAnchor="middle"))
    d.add(String(centro, 14,
                 "Cabeceras (nosniff · DENY · CSP · HSTS) · Límite de intentos "
                 "en login y recuperación",
                 fontName="Times-Roman", fontSize=7.5, fillColor=GRIS,
                 textAnchor="middle"))
    d.add(String(centro, 5,
                 "Consultas siempre parametrizadas · Escapes en los documentos "
                 "generados · Contraseñas con bcrypt",
                 fontName="Times-Roman", fontSize=7.5, fillColor=GRIS,
                 textAnchor="middle"))
    return d


# ---------------------------------------------------------------------------
# 2. Entidad-relación
# ---------------------------------------------------------------------------
# Dónde va cada tabla. La rejilla se fija a mano —colocar trece cajas sin que
# las líneas se crucen no lo resuelve un algoritmo sencillo—, pero LAS
# RELACIONES NO: se leen de las claves ajenas que declara SQLAlchemy, así que
# una clave nueva aparece dibujada sin tocar nada aquí.
REJILLA = {
    "roles":            (0, 0), "permisos":         (3, 0),
    "usuarios":         (0, 1),
    "productos":        (2, 1), "servicios":        (3, 1),
    "ventas":           (0, 2), "citas":            (2, 2), "pqr":  (3, 2),
    "detalle_ventas":   (0, 3), "facturas":         (1, 3),
    "conversaciones":   (2, 3),
    "detalle_facturas": (1, 4), "mensajes":         (2, 4),
}

COLOR_GRUPO = {
    "roles": (AZUL, AZUL_SUAVE), "permisos": (GRIS, GRIS_SUAVE),
    "usuarios": (AZUL, AZUL_SUAVE),
    "productos": (AMBAR, AMBAR_SUAVE), "servicios": (AMBAR, AMBAR_SUAVE),
    "ventas": (VERDE, VERDE_SUAVE), "detalle_ventas": (VERDE, VERDE_SUAVE),
    "facturas": (VERDE, VERDE_SUAVE), "detalle_facturas": (VERDE, VERDE_SUAVE),
    "citas": (AMBAR, AMBAR_SUAVE), "pqr": (AMBAR, AMBAR_SUAVE),
    "conversaciones": (GRIS, GRIS_SUAVE), "mensajes": (GRIS, GRIS_SUAVE),
}


def diagrama_entidad_relacion(entidades, ancho=453):
    """Las trece tablas y las claves ajenas que las enlazan.

    De cada tabla se enseña la clave primaria y sus claves ajenas, que es lo
    que define la relación. El resto de columnas va en el diccionario de datos
    del apartado siguiente: meterlas aquí daría un diagrama ilegible.
    """
    columnas, filas = 4, 5
    cajaAncho, cajaAlto = 100.0, 54.0
    hueco_x = (ancho - columnas * cajaAncho) / max(columnas - 1, 1)
    hueco_y = 22.0
    alto = filas * cajaAlto + (filas - 1) * hueco_y

    d = Drawing(ancho, alto)
    porNombre = {e["tabla"]: e for e in entidades}
    posicion = {}

    for nombre, (col, fila) in REJILLA.items():
        if nombre not in porNombre:
            continue
        x = col * (cajaAncho + hueco_x)
        # La fila 0 va arriba del todo.
        y = alto - (fila + 1) * cajaAlto - fila * hueco_y
        posicion[nombre] = (x, y, cajaAncho, cajaAlto)

    # --- Primero las líneas, para que las cajas queden encima ---
    for entidad in entidades:
        origen = entidad["tabla"]
        if origen not in posicion:
            continue
        for columna in entidad["columnas"]:
            if not columna["fk"]:
                continue
            destino = columna["fk"].split(".")[0]
            if destino not in posicion or destino == origen:
                continue
            ox, oy, oa, ob = posicion[origen]
            dx, dy, da, db = posicion[destino]
            # Del borde más cercano al borde más cercano.
            x1, y1 = ox + oa / 2.0, oy + ob
            x2, y2 = dx + da / 2.0, dy
            if dy > oy:                       # el destino está por encima
                x1, y1 = ox + oa / 2.0, oy + ob
                x2, y2 = dx + da / 2.0, dy
            else:                             # o al lado
                x1, y1 = ox + oa, oy + ob / 2.0
                x2, y2 = dx, dy + db / 2.0
            _flecha(d, x1, y1, x2, y2, "N:1")

    # --- Y ahora las cajas ---
    for nombre, (x, y, a, b) in posicion.items():
        borde, fondo = COLOR_GRUPO.get(nombre, (GRIS, GRIS_SUAVE))
        d.add(Rect(x, y, a, b, fillColor=fondo, strokeColor=borde,
                   strokeWidth=1.0))
        # Banda del título.
        d.add(Rect(x, y + b - 14, a, 14, fillColor=borde, strokeColor=borde))
        d.add(String(x + a / 2.0, y + b - 10.5, nombre, fontName="Times-Bold",
                     fontSize=7.5, fillColor=colors.white, textAnchor="middle"))

        entidad = porNombre[nombre]
        claves = [c["nombre"] + "  PK" for c in entidad["columnas"] if c["pk"]]
        claves += [c["nombre"] + "  FK" for c in entidad["columnas"] if c["fk"]]
        for i, texto in enumerate(claves[:4]):
            d.add(String(x + 5, y + b - 24 - i * 8.5, texto,
                         fontName="Times-Roman", fontSize=6.5, fillColor=GRIS))
        sobran = len(entidad["columnas"]) - len(claves)
        if sobran > 0 and len(claves) < 4:
            d.add(String(x + 5, y + b - 24 - len(claves) * 8.5,
                         "+ %d columnas" % sobran, fontName="Times-Italic",
                         fontSize=6.5, fillColor=LINEA))
    return d
