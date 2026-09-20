# -*- coding: utf-8 -*-
"""Lista de chequeo del quinto avance, en Excel y con las evidencias pegadas.

    backend/venv/Scripts/python herramientas/lista_chequeo_quinta.py

Reproduce el instrumento del SENA —mismas secciones, mismas columnas, mismos
colores, tomados del PDF original que se transcribió para el cuarto avance— y
pega cada captura en su casilla «Espacio para Evidencia».

UNA SOLA LISTA PARA LOS DOS DOCUMENTOS
--------------------------------------
Las filas NO se escriben aquí: se leen de `documento_quinta.SECCIONES`, que es
la misma lista con la que se monta el PDF de evidencias. Escribirlas dos veces
garantizaba que tarde o temprano el PDF y el Excel dirían cosas distintas
sobre la misma captura, y que nadie se enterara hasta tenerlos delante.

SOBRE LA NUMERACIÓN
-------------------
El instrumento del quinto avance no está en el repositorio, así que la columna
«No.» va con la numeración de este documento (01, 02, 03…) y no con la del
instructor. Poner números inventados al lado de cada evidencia sería peor que
no poner ninguno: parecería que corresponden a algo. Cuando llegue el
instrumento, se cambia la columna y el resto encaja.
"""

import os
import sys

import xlsxwriter
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from documento_quinta import AUTOR, CAPTURAS, SECCIONES  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(RAIZ, "evidencias", "plantilla", "logo-1.png")
DESTINO = os.path.join(
    RAIZ, "evidencias", "Lista_Chequeo_Quinto_Avance_AutoPrime.xlsx")

# Colores muestreados del PDF original, no elegidos a ojo.
VERDE_OSCURO = "#1D5900"
VERDE = "#3AAA00"
VERDE_CLARO = "#E9F2E8"
AZUL_CLARO = "#DBE6F0"
GRIS = "#F2F2F2"
BLANCO = "#FFFFFF"
BORDE = "#808080"

ANCHOS = {"A": 14.5, "B": 25.5, "C": 45.0, "D": 70.0, "E": 32.0}

ANCHO_IMAGEN = 480          # px a los que se escala cada captura
ALTO_MAXIMO_FILA = 409      # el máximo que admite Excel, en puntos


def ancho_px(caracteres: float) -> int:
    """Pasa el ancho de columna de Excel (en caracteres) a píxeles."""
    return int(caracteres * 7 + 5)


def filas_del_avance():
    """Aplana las secciones en filas de la tabla.

    Devuelve (seccion, archivo, titulo, demuestra, pie) por cada evidencia.
    """
    for seccion, _intro, bloques in SECCIONES:
        for archivo, titulo, demuestra, pie in bloques:
            yield seccion, archivo, titulo, demuestra, pie


def main() -> int:
    filas = list(filas_del_avance())

    libro = xlsxwriter.Workbook(DESTINO, {"nan_inf_to_errors": True})
    hoja = libro.add_worksheet("Lista de Chequeo")

    def f(**extra):
        base = {"border": 1, "border_color": BORDE, "valign": "vcenter",
                "font_name": "Calibri"}
        base.update(extra)
        return libro.add_format(base)

    titulo_f = f(bg_color=VERDE_OSCURO, font_color=BLANCO, bold=True,
                 font_size=18, align="center")
    subtitulo = f(bg_color=VERDE_OSCURO, font_color=BLANCO, italic=True,
                  font_size=11, align="center")
    banda_clara = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                    font_size=12, align="center")
    banda_seccion = f(bg_color=VERDE_OSCURO, font_color=BLANCO, italic=True,
                      bold=True, font_size=11, align="center")
    banda_verde = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                    font_size=11, align="left", indent=1)
    banda_tema = f(bg_color=VERDE_CLARO, font_color=VERDE_OSCURO, bold=True,
                   font_size=11, align="left", indent=1)

    etiqueta = f(bold=True, align="right", font_size=11)
    valor_blanco = f(align="left", font_size=11, indent=1)
    valor_verde = f(bg_color=VERDE_CLARO, align="center", bold=True, font_size=11)
    valor_azul = f(bg_color=AZUL_CLARO, align="center", font_size=11)

    cabecera_tabla = f(bg_color=VERDE, font_color=BLANCO, bold=True,
                       align="center", font_size=11, text_wrap=True)

    def formatos_fila(par: bool):
        fondo = GRIS if par else BLANCO
        return {
            "num": f(bg_color=fondo, bold=True, align="center", font_size=11),
            "req": f(bg_color=fondo, bold=True, align="center",
                     text_wrap=True, font_size=11),
            "det": f(bg_color=fondo, italic=True, font_color="#595959",
                     align="center", text_wrap=True, font_size=10),
            "evi": f(bg_color=fondo, align="center"),
            "obs": f(bg_color=AZUL_CLARO, align="left", text_wrap=True,
                     font_size=10, indent=1),
        }

    pie_nota = libro.add_format({"italic": True, "font_size": 9,
                                 "font_color": "#595959",
                                 "font_name": "Calibri", "text_wrap": True})

    for i, col in enumerate("ABCDE"):
        hoja.set_column(i, i, ANCHOS[col])

    r = 0

    # --- Cabecera institucional ----------------------------------------
    hoja.merge_range(r, 0, r + 1, 4, "SENA - REGIONAL ANTIOQUIA", titulo_f)
    hoja.set_row(r, 30)
    hoja.set_row(r + 1, 18)
    if os.path.isfile(LOGO):
        hoja.insert_image(r, 0, LOGO, {
            "x_scale": 0.20, "y_scale": 0.20,
            "x_offset": 12, "y_offset": 6,
            "object_position": 1,
        })
    r += 2

    hoja.merge_range(r, 0, r, 4, "Centro de Servicio y Gestión Empresarial",
                     subtitulo)
    hoja.set_row(r, 18)
    r += 1

    hoja.merge_range(
        r, 0, r, 4,
        "LISTA DE CHEQUEO - QUINTO AVANCE - PROYECTO AUTOPRIME", banda_clara)
    hoja.set_row(r, 22)
    r += 1

    hoja.merge_range(r, 0, r, 4, "1. DATOS DEL APRENDIZ Y DEL PROGRAMA",
                     banda_seccion)
    hoja.set_row(r, 20)
    r += 1

    import datetime
    hoy = datetime.date.today().isoformat()
    datos = [
        ("Nombre del Aprendiz:", AUTOR, valor_verde,
         "Fecha de Presentación:", hoy, valor_azul),
        # El documento va como texto y no como número: es un identificador,
        # no una cantidad, y así Excel no le mete separador de miles.
        ("Documento de Identidad:", "1038928023", valor_azul,
         "Ficha de Caracterización:", "3406211", valor_blanco),
        ("Programa de Formación:", "ADSO (Análisis y Desarrollo de Software)",
         valor_blanco, "Trimestre / Ambiente:", "03 / 702", valor_blanco),
        ("Competencia:", "React", valor_blanco,
         "Instructor:", "Jhan Hader Muñoz", valor_blanco),
    ]
    for et_i, val_i, fmt_i, et_d, val_d, fmt_d in datos:
        hoja.merge_range(r, 0, r, 1, et_i, etiqueta)
        hoja.write(r, 2, val_i, fmt_i)
        hoja.write(r, 3, et_d, etiqueta)
        hoja.write(r, 4, val_d, fmt_d)
        hoja.set_row(r, 22)
        r += 1

    # --- Indicadores ----------------------------------------------------
    hoja.merge_range(r, 0, r, 4, "2. INDICADORES DE AVANCE Y CALIFICACIÓN",
                     banda_verde)
    hoja.set_row(r, 20)
    r += 1

    fila_total = r + 1  # 1-indexada, para la fórmula
    hoja.write(r, 0, "Total Evidencias:",
               f(bold=True, align="center", text_wrap=True, font_size=10))
    hoja.write(r, 1, len(filas), valor_verde)
    hoja.write(r, 2, "Evidencias Aportadas:", etiqueta)
    hoja.write(r, 3, len(filas), valor_verde)
    # El porcentaje se calcula, no se escribe: si el instructor corrige el
    # número de cumplidos, el avance se actualiza solo.
    hoja.write_formula(
        r, 4, "=IF(B%d=0,0,D%d/B%d)" % (fila_total, fila_total, fila_total),
        f(bg_color=VERDE_CLARO, align="center", bold=True, font_size=11,
          num_format="0.0%"), 1.0)
    hoja.set_row(r, 26)
    r += 1

    hoja.merge_range(r, 0, r, 1, "Estado de Avance:", etiqueta)
    hoja.write(r, 2, "COMPLETO - PENDIENTE REVISIÓN", valor_verde)
    hoja.write(r, 3, "Valoración Final Instructor:", etiqueta)
    hoja.write(r, 4, "Aprobado / No Aprobado", valor_azul)
    hoja.set_row(r, 22)
    r += 1

    # --- La tabla -------------------------------------------------------
    hoja.merge_range(
        r, 0, r, 4,
        "3. EVIDENCIAS DEL QUINTO AVANCE (01 AL %02d)" % len(filas),
        banda_verde)
    hoja.set_row(r, 20)
    r += 1

    encabezados = ["No.", "Evidencia", "Qué demuestra",
                   "Espacio para Evidencia / Captura de Pantalla",
                   "Observaciones del Aprendiz / Notas de Entrega"]
    for c, texto in enumerate(encabezados):
        hoja.write(r, c, texto, cabecera_tabla)
    hoja.set_row(r, 34)
    fila_encabezado = r
    r += 1

    ancho_celda = ancho_px(ANCHOS["D"])
    seccion_anterior = None
    sin_captura = []

    for indice, (seccion, archivo, subtitulo_fila, demuestra, pie) in \
            enumerate(filas, 1):
        # Una banda por tema, para que la tabla no sea una lista plana de
        # veintidós filas sin agrupar.
        if seccion != seccion_anterior:
            hoja.merge_range(r, 0, r, 4, seccion.upper(), banda_tema)
            hoja.set_row(r, 20)
            r += 1
            seccion_anterior = seccion

        fmt = formatos_fila(indice % 2 == 0)
        hoja.write(r, 0, "%02d" % indice, fmt["num"])
        hoja.write(r, 1, subtitulo_fila, fmt["req"])
        hoja.write(r, 2, demuestra, fmt["det"])
        hoja.write(r, 3, "", fmt["evi"])
        hoja.write(r, 4, pie, fmt["obs"])

        ruta = os.path.join(CAPTURAS, archivo + ".png")
        if os.path.isfile(ruta):
            with Image.open(ruta) as imagen:
                escala = ANCHO_IMAGEN / imagen.width
                alto_pt = imagen.height * escala * 0.75  # px -> puntos
            alto_fila = min(alto_pt + 10, ALTO_MAXIMO_FILA)
            hoja.set_row(r, alto_fila)
            hoja.insert_image(r, 3, ruta, {
                "x_scale": escala, "y_scale": escala,
                "x_offset": max(4, (ancho_celda - ANCHO_IMAGEN) // 2),
                "y_offset": 5,
                "object_position": 1,
            })
        else:
            sin_captura.append(archivo)
            hoja.write(r, 3, "FALTA %s.png" % archivo, fmt["evi"])
            hoja.set_row(r, 40)
        r += 1

    # Que la cabecera de la tabla se repita al imprimir; si no, a partir de
    # la segunda pagina no se sabe que columna es cual.
    hoja.repeat_rows(fila_encabezado)
    hoja.freeze_panes(fila_encabezado + 1, 0)

    r += 1
    hoja.merge_range(
        r, 0, r + 2, 4,
        "La columna «No.» lleva la numeración de este documento, no la del "
        "instrumento del instructor: se ajusta cuando se tenga a la vista. "
        "Todas las capturas se generaron ejecutando el sistema "
        "(herramientas/capturas_quinta.py y evidencias_consola_quinta.py); "
        "las de consola recogen la salida real de cada comando.",
        pie_nota)
    hoja.set_row(r, 16)

    hoja.set_landscape()
    hoja.set_paper(9)          # A4
    hoja.fit_to_pages(1, 0)

    libro.close()

    print("  %s" % DESTINO)
    print("  %d evidencias en %d temas, %.1f MB"
          % (len(filas), len({s for s, _, _, _, _ in filas}),
             os.path.getsize(DESTINO) / 1024 / 1024))
    if sin_captura:
        print()
        print("  %d sin captura:" % len(sin_captura))
        for nombre in sin_captura:
            print("    %s" % nombre)
    return 0


if __name__ == "__main__":
    sys.exit(main())
