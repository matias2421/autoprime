# -*- coding: utf-8 -*-
"""Recorta el fondo sobrante de las evidencias de consola.

El navegador captura siempre el alto de la ventana, así que una ficha corta
sale con medio folio de negro debajo. Pegada en el documento del entregable
eso deja un hueco raro; recortada al contenido, cada imagen ocupa lo que mide.

Solo toca las fichas de consola: las capturas de la aplicación son pantallas
completas y ahí el encuadre es el que es.

    backend/venv/Scripts/python herramientas/recortar.py
"""

import os
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURAS = os.path.join(RAIZ, "evidencias", "capturas")

MARGEN = 26          # el mismo relleno que usa la plantilla
FONDO = (2, 2, 4)    # --color-negro


def recortar(ruta: str) -> tuple[int, int] | None:
    """Quita las filas y columnas de fondo liso, dejando el margen."""
    imagen = Image.open(ruta).convert("RGB")
    ancho, alto = imagen.size

    # `getbbox` sobre la diferencia con el fondo da la caja del contenido en
    # una sola pasada en C, mucho más rápido que recorrer píxeles en Python.
    fondo = Image.new("RGB", imagen.size, FONDO)
    from PIL import ImageChops
    caja = ImageChops.difference(imagen, fondo).getbbox()

    if caja is None:
        return None  # imagen enteramente de fondo: no se toca

    izq, arr, der, aba = caja
    izq = max(0, izq - MARGEN)
    arr = max(0, arr - MARGEN)
    der = min(ancho, der + MARGEN)
    aba = min(alto, aba + MARGEN)

    if (der - izq, aba - arr) == (ancho, alto):
        return None  # ya estaba ajustada

    imagen.crop((izq, arr, der, aba)).save(ruta, "PNG", optimize=True)
    return alto, aba - arr


def main() -> int:
    if not os.path.isdir(CAPTURAS):
        print("  No hay capturas todavía.")
        return 1

    fichas = sorted(
        f for f in os.listdir(CAPTURAS)
        if f.endswith(".png") and any(
            c in f for c in ("estructura", "entorno", "tablas", "tabla-usuarios",
                             "hash", "jwt", "roles", "revalidacion", "hooks",
                             "pruebas")
        )
    )

    tocadas = 0
    for nombre in fichas:
        r = recortar(os.path.join(CAPTURAS, nombre))
        if r:
            antes, ahora = r
            print(f"  {nombre:<30} {antes} -> {ahora} px de alto")
            tocadas += 1
        else:
            print(f"  {nombre:<30} sin cambios")

    print()
    print(f"  {tocadas} de {len(fichas)} recortadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
