# -*- coding: utf-8 -*-
"""Genera el Manual Técnico del proyecto formativo, en PDF.

    backend/venv/Scripts/python herramientas/manual_tecnico.py

Responde a la solicitud del instructor César Augusto Moreno Mena: las
secciones que pide, en el orden que pide, con el formato que pide —Times New
Roman a 11 pt, interlineado 1.15, márgenes estándar y encabezado
institucional— y con tabla de contenido numerada.

POR QUÉ SE GENERA Y NO SE ESCRIBE A MANO
----------------------------------------
Casi todo lo que va dentro ya existe en el proyecto: las tablas las declara
SQLAlchemy, los endpoints los publica el propio OpenAPI, las dependencias
están en requirements.txt y las capturas se tomaron ejecutando el sistema.
Copiarlo a mano significa que el día que cambie una tabla el manual mienta y
nadie se entere. Aquí se LEE del proyecto, así que volver a lanzarlo lo deja
al día.

Lo que sí está escrito a mano —el problema, los objetivos, el alcance, las
decisiones de diseño y las conclusiones— vive en `manual_secciones.py`.

LA TABLA DE CONTENIDO LLEVA PÁGINAS DE VERDAD
---------------------------------------------
Eso obliga a componer el documento dos veces: en la primera pasada aún no se
sabe en qué página cae cada título. De eso se encarga `multiBuild` junto con
`afterFlowable`, que va anotando cada encabezado con la página donde acabó.

Y una tercera pasada, para el pie: «Página 3 de 41» no se puede escribir sin
saber cuántas hay, y eso tampoco se sabe hasta haber compuesto el documento
entero. Se compone, se apunta el total y se compone otra vez.
"""

import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manual_estilo import CABECERA, GRIS, LINEA, MARGEN  # noqa: E402
from manual_secciones import APRENDIZ, FICHA, relato_completo  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(
    RAIZ, "evidencias",
    "ManualTecnico_Ficha3406211_Agudelo_Bolivar_Jose_Matias.pdf")


class ManualTecnico(BaseDocTemplate):
    """Documento con encabezado institucional, pie numerado y contenido.

    `afterFlowable` es lo que hace posible la tabla de contenido: cada vez
    que se coloca un encabezado, avisa con el número de página en el que
    acabó.
    """

    def __init__(self, ruta, total_paginas=0, **extra):
        super().__init__(
            ruta, pagesize=A4,
            leftMargin=MARGEN, rightMargin=MARGEN,
            topMargin=MARGEN + 0.9 * cm, bottomMargin=MARGEN + 0.4 * cm,
            title="Manual Técnico — AutoPrime",
            author=APRENDIZ,
            subject="Proyecto formativo · Ficha %s" % FICHA,
            **extra)

        self.total_paginas = total_paginas
        marco = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="cuerpo")
        self.addPageTemplates([
            PageTemplate(id="portada", frames=[marco], onPage=self._portada),
            PageTemplate(id="normal", frames=[marco], onPage=self._adorno),
        ])

    # -- adornos de página --
    def _portada(self, lienzo, doc):
        """La portada va limpia: ni encabezado ni número de página."""
        lienzo.saveState()
        lienzo.setStrokeColor(CABECERA)
        lienzo.setLineWidth(2)
        lienzo.rect(MARGEN - 14, MARGEN - 14,
                    A4[0] - 2 * (MARGEN - 14), A4[1] - 2 * (MARGEN - 14))
        lienzo.restoreState()
        # A partir de la segunda página manda la plantilla normal.
        doc.handle_nextPageTemplate("normal")

    def _adorno(self, lienzo, doc):
        lienzo.saveState()

        alto = A4[1] - MARGEN + 0.3 * cm
        lienzo.setFont("Times-Bold", 8.5)
        lienzo.setFillColor(CABECERA)
        lienzo.drawString(MARGEN, alto, "SERVICIO NACIONAL DE APRENDIZAJE — SENA")
        lienzo.setFont("Times-Roman", 8.5)
        lienzo.setFillColor(GRIS)
        lienzo.drawRightString(A4[0] - MARGEN, alto,
                               "Manual Técnico · AutoPrime · Ficha %s" % FICHA)
        lienzo.setStrokeColor(LINEA)
        lienzo.setLineWidth(0.6)
        lienzo.line(MARGEN, alto - 5, A4[0] - MARGEN, alto - 5)

        bajo = MARGEN - 0.55 * cm
        lienzo.line(MARGEN, bajo + 12, A4[0] - MARGEN, bajo + 12)
        lienzo.setFont("Times-Roman", 8.5)
        lienzo.setFillColor(GRIS)
        lienzo.drawString(MARGEN, bajo, APRENDIZ)
        total = self.total_paginas or "?"
        lienzo.drawRightString(A4[0] - MARGEN, bajo,
                               "Página %d de %s" % (doc.page, total))
        lienzo.restoreState()

    # -- tabla de contenido --
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        nombre = flowable.style.name
        if nombre not in ("h1", "h2"):
            return
        nivel = 0 if nombre == "h1" else 1
        clave = "ancla-%d-%d" % (self.page, id(flowable))
        self.canv.bookmarkPage(clave)
        self.notify("TOCEntry", (nivel, flowable.getPlainText(),
                                 self.page, clave))


def main() -> int:
    print("  Leyendo el proyecto...")
    relato = relato_completo()
    print("  %d elementos que componer" % len(relato))

    # Primera composición: sirve para contar las páginas. Se tira el
    # resultado; lo único que interesa es el total.
    print("  Componiendo (1/2) para contar las páginas...")
    tanteo = ManualTecnico(os.devnull)
    tanteo.multiBuild(relato_completo())
    total = tanteo.page

    print("  Componiendo (2/2) con «Página X de %d»..." % total)
    definitivo = ManualTecnico(DESTINO, total_paginas=total)
    definitivo.multiBuild(relato_completo())

    peso = os.path.getsize(DESTINO) / 1024.0 / 1024.0
    print()
    print("  %s" % DESTINO)
    print("  %d páginas · %.1f MB" % (definitivo.page, peso))
    return 0


if __name__ == "__main__":
    sys.exit(main())
