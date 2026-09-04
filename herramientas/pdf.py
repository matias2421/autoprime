# -*- coding: utf-8 -*-
"""Imprime el documento de verificación a PDF.

Usa el mismo Chrome sin ventana que toma las capturas, esta vez con su
impresora interna. Frente a convertir las imágenes a PDF una detrás de otra,
esto conserva el texto: los enunciados y las rutas de archivo se pueden buscar
y copiar del documento, y las capturas no se re-comprimen.

    python herramientas/pdf.py

No hace falta que la aplicación esté en marcha: las capturas ya viven dentro
del documento.
"""

import base64
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capturas import Navegador  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "evidencias", "verificacion.html")
DESTINO = os.path.join(RAIZ, "evidencias", "Evidencias_Cuarto_Avance_AutoPrime.pdf")

# A4 en pulgadas, que es lo que espera el protocolo.
ANCHO_A4, ALTO_A4 = 8.27, 11.69


def main() -> int:
    if not os.path.isfile(ORIGEN):
        print(f"  Falta {ORIGEN}")
        return 1

    nav = Navegador()
    try:
        nav.ir("file:///" + ORIGEN.replace("\\", "/"), espera=3.0)

        # Las capturas van en `loading="lazy"`, que es lo correcto en pantalla
        # pero deja fuera del PDF todo lo que no se haya llegado a mostrar.
        nav.js("[...document.querySelectorAll('img')].forEach(i => i.loading = 'eager')")
        nav.js("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)
        nav.js("window.scrollTo(0, 0)")

        pendientes = nav.js(
            "[...document.querySelectorAll('img')]"
            ".filter(i => !i.complete || i.naturalWidth === 0).length"
        )
        if pendientes:
            print(f"  Aviso: {pendientes} imágenes sin cargar")

        # `printBackground` es imprescindible aquí: el documento es de fondo
        # oscuro con texto claro, así que sin los fondos saldría texto gris
        # sobre blanco, ilegible.
        resultado = nav._enviar(
            "Page.printToPDF",
            printBackground=True,
            paperWidth=ANCHO_A4,
            paperHeight=ALTO_A4,
            marginTop=0.35,
            marginBottom=0.35,
            marginLeft=0.3,
            marginRight=0.3,
            scale=0.8,
            preferCSSPageSize=False,
        )

        with open(DESTINO, "wb") as f:
            f.write(base64.b64decode(resultado["data"]))

    finally:
        nav.cerrar()

    peso = os.path.getsize(DESTINO) / 1024 / 1024
    print(f"  {DESTINO}")
    print(f"  {peso:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
