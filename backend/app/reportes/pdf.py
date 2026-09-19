"""Genera los PDF: la factura y el reporte de ventas.

Se usa reportlab y no un navegador sin cabeza. La versión con Chrome produce
un PDF más bonito con menos esfuerzo, pero exige un Chrome instalado en el
servidor: funcionaría en el portátil y fallaría en Render, que es donde
corre esto de verdad. reportlab es Python puro y no depende de nada del
sistema, así que el documento sale igual en los dos sitios.

Todo se arma en memoria y se devuelve como `bytes`. Escribir en disco
obligaría a decidir dónde, a limpiarlo después y a confiar en que el disco
del contenedor —que es efímero— siga ahí en la siguiente petición.

DOS COSAS QUE SE ARREGLARON AQUÍ
--------------------------------
**El texto ajeno se escapa.** `Paragraph` interpreta un dialecto de marcado,
así que una descripción con un `<b>` sin cerrar no se pintaba: levantaba un
`ValueError` y tumbaba la generación. Esa factura quedaba sin poder
descargarse nunca, y como el reporte lista nombres de cliente —que elige
quien se registra—, bastaba un nombre con una etiqueta abierta para dejar
al negocio sin poder generar su reporte. Ver `seguridad.py`.

**El pie dice «Página X de Y».** Antes decía solo «Página X», aunque el
comentario de al lado ya explicaba por qué hacía falta el total: sin él, no
hay forma de saber si a un documento impreso le falta la última hoja. Se
cumple con un lienzo que cuenta las páginas en una primera pasada y escribe
el pie en la segunda.
"""

import io
from datetime import date

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as lienzo_pdf
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.tiempo import ahora
from app.reportes.estilo import (
    ACENTO,
    ACENTO_TENUE,
    EMPRESA,
    LINEA,
    MARGEN,
    PAPEL,
    TINTA,
    TINTA_SUAVE,
    estilos,
    numero,
    pesos,
)
from app.reportes.letras import en_letras
from app.reportes.seguridad import recortar, texto_para_pdf

E = estilos()


# --------------------------------------------------------------------------
#  Marco: banda de cabecera y pie con «Página X de Y»
# --------------------------------------------------------------------------
class LienzoNumerado(lienzo_pdf.Canvas):
    """Un lienzo que sabe cuántas páginas tiene el documento.

    reportlab dibuja cada página y la suelta, así que mientras compone la
    página 1 todavía no sabe si habrá una 2. El truco estándar es guardar el
    estado de cada página en lugar de escribirla, y al cerrar —cuando el
    total ya se conoce— recorrerlas escribiendo el pie.

    Cuesta una segunda pasada sobre las páginas ya compuestas, no sobre el
    contenido: no se vuelve a consultar nada ni a rehacer la maqueta.
    """

    def __init__(self, *args, titulo: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._titulo = titulo
        self._paginas = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._encabezado()
            self._pie(total)
            super().showPage()
        super().save()

    # ------------------------------------------------------------------
    def _encabezado(self):
        ancho, alto = self._pagesize
        self.saveState()

        # Banda superior. Es la única tinta densa del documento: 14 mm de
        # alto, no una página entera. Ver `estilo.py`.
        self.setFillColor(TINTA)
        self.rect(0, alto - 14 * mm, ancho, 14 * mm, stroke=0, fill=1)

        self.setFillColor(PAPEL)
        self.setFont("Helvetica-Bold", 11)
        self.drawString(MARGEN, alto - 9.4 * mm, EMPRESA["nombre"].upper())

        self.setFont("Helvetica", 7.5)
        self.setFillColor(ACENTO_TENUE)
        self.drawString(MARGEN + 26 * mm, alto - 9.4 * mm, EMPRESA["lema"])
        self.drawRightString(ancho - MARGEN, alto - 9.4 * mm, self._titulo)

        self.restoreState()

    def _pie(self, total: int):
        ancho, _ = self._pagesize
        self.saveState()

        self.setStrokeColor(LINEA)
        self.setLineWidth(0.5)
        self.line(MARGEN, 13 * mm, ancho - MARGEN, 13 * mm)

        self.setFillColor(TINTA_SUAVE)
        self.setFont("Helvetica", 7)
        self.drawString(
            MARGEN, 10 * mm,
            f"{EMPRESA['nombre']} · {EMPRESA['nit']} · {EMPRESA['contacto']}",
        )
        self.drawRightString(
            ancho - MARGEN, 10 * mm, f"Página {self._pageNumber} de {total}"
        )

        self.restoreState()


def _documento(titulo: str, apaisado: bool = False) -> tuple:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4) if apaisado else A4,
        leftMargin=MARGEN,
        rightMargin=MARGEN,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title=titulo,
        author=EMPRESA["nombre"],
        subject="Documento generado por el sistema AutoPrime",
    )
    return doc, buffer


def _construir(doc, piezas, buffer, titulo: str) -> bytes:
    def fabricar(*args, **kwargs):
        return LienzoNumerado(*args, titulo=titulo, **kwargs)

    doc.build(piezas, canvasmaker=fabricar)
    return buffer.getvalue()


def _parrafo(texto, estilo):
    """Un párrafo con texto de origen ajeno, ya escapado."""
    return Paragraph(texto_para_pdf(texto), estilo)


def _estilo_tabla(columnas_derecha: list[int], filas: int) -> TableStyle:
    """Cabecera con fondo de acento, cuerpo con reglas finas y filas alternas.

    Las filas alternas no son adorno: en una tabla de ocho columnas son lo
    que impide leer el importe de la fila de al lado.
    """
    ordenes = [
        ("BACKGROUND", (0, 0), (-1, 0), ACENTO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), TINTA),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col in columnas_derecha:
        ordenes.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    for fila in range(2, filas, 2):
        ordenes.append(("BACKGROUND", (0, fila), (-1, fila), ACENTO_TENUE))
    return TableStyle(ordenes)


def _grafica_barras(serie, ancho_mm: float = 240, alto_mm: float = 55):
    """Los ingresos por día, dibujados dentro del propio PDF.

    El reporte en pantalla tiene su gráfica y el Excel la suya; el PDF era
    el único de los tres que salía solo con tablas. Quien lo imprime para
    una reunión se queda sin la única lectura que se hace de un vistazo.
    """
    if not serie:
        return None

    dibujo = Drawing(ancho_mm * mm, alto_mm * mm)
    grafica = VerticalBarChart()
    grafica.x = 10 * mm
    grafica.y = 10 * mm
    grafica.width = ancho_mm * mm - 16 * mm
    grafica.height = alto_mm * mm - 16 * mm
    grafica.data = [[float(d["ingresos"]) for d in serie]]

    grafica.bars[0].fillColor = ACENTO
    grafica.bars[0].strokeColor = None
    grafica.barSpacing = 1
    grafica.groupSpacing = 3

    grafica.valueAxis.valueMin = 0
    grafica.valueAxis.labels.fontName = "Helvetica"
    grafica.valueAxis.labels.fontSize = 6
    grafica.valueAxis.labelTextFormat = lambda v: (
        f"${v / 1_000_000_000:.0f} mil M" if v >= 1_000_000_000
        else f"${v / 1_000_000:.0f} M" if v >= 1_000_000
        else f"{v:.0f}"
    )

    # Con sesenta días no caben sesenta fechas: se rotulan las que quepan.
    paso = max(1, len(serie) // 12)
    grafica.categoryAxis.categoryNames = [
        date.fromisoformat(d["fecha"]).strftime("%d/%m") if i % paso == 0 else ""
        for i, d in enumerate(serie)
    ]
    grafica.categoryAxis.labels.fontName = "Helvetica"
    grafica.categoryAxis.labels.fontSize = 6
    grafica.categoryAxis.labels.angle = 90
    grafica.categoryAxis.labels.dy = -6

    dibujo.add(grafica)
    return dibujo


# --------------------------------------------------------------------------
#  Factura
# --------------------------------------------------------------------------
def factura_pdf(factura) -> bytes:
    """La factura de una venta, lista para imprimir o adjuntar."""
    titulo = f"Factura {factura.numero}"
    doc, buffer = _documento(titulo)
    venta = factura.venta
    comprador = venta.cliente if venta else None
    anulada = factura.estado == "anulada"

    piezas = [
        _parrafo(titulo, E["titulo"]),
        _parrafo(
            f"Emitida el {factura.fecha_emision:%d/%m/%Y a las %H:%M}"
            f"  ·  Venta {venta.numero if venta else '—'}",
            E["subtitulo"],
        ),
        Spacer(1, 6 * mm),
    ]

    # Estado del pago, en una banda propia.
    #
    # Antes iba de seguido en el subtítulo, y era la única línea del
    # documento que cambia lo que el papel significa: una factura emitida se
    # cobra y una anulada no vale. Eso no puede leerse de refilón.
    estado_venta = venta.estado if venta else "—"
    if anulada:
        franja, fondo, texto_estado = (
            "#8a1c1c", "#fadbd8",
            "DOCUMENTO ANULADO · esta factura no tiene validez para pago",
        )
    elif estado_venta == "pagada":
        franja, fondo, texto_estado = ("#0b6b3a", "#d8f3e3", "PAGADA")
    else:
        franja, fondo, texto_estado = (
            "#7a5200", "#fdf0d0", "PENDIENTE DE PAGO",
        )

    from reportlab.lib import colors

    banda = Table([[texto_estado]], colWidths=[170 * mm])
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fondo)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(franja)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(franja)),
    ]))
    piezas += [banda, Spacer(1, 8 * mm)]

    # Emisor y cliente, uno al lado del otro.
    izquierda = (
        f"<b>{texto_para_pdf(EMPRESA['nombre'])}</b><br/>"
        f"{texto_para_pdf(EMPRESA['nit'])}<br/>"
        f"{texto_para_pdf(EMPRESA['direccion'])}<br/>"
        f"{texto_para_pdf(EMPRESA['contacto'])}<br/>"
        "Régimen común · No responsable de IVA en ventas de vehículos usados"
    )
    if comprador:
        derecha = (
            f"<b>{texto_para_pdf(comprador.nombre)} "
            f"{texto_para_pdf(comprador.apellido)}</b><br/>"
            f"{texto_para_pdf(comprador.tipo_documento)} "
            f"{texto_para_pdf(comprador.numero_documento)}<br/>"
            f"{texto_para_pdf(comprador.direccion)}<br/>"
            f"{texto_para_pdf(comprador.correo)} · "
            f"{texto_para_pdf(comprador.telefono)}"
        )
    else:
        derecha = "<b>Cliente no disponible</b>"

    partes = Table(
        [
            [Paragraph("EMITIDA POR", E["celda"]), Paragraph("FACTURADA A", E["celda"])],
            [Paragraph(izquierda, E["celda"]), Paragraph(derecha, E["celda"])],
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    partes.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, 0), ACENTO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACENTO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    piezas += [partes, Spacer(1, 10 * mm)]

    # Detalle.
    filas = [["#", "Descripción", "Cant.", "Precio unitario", "Subtotal"]]
    for i, linea in enumerate(factura.lineas, start=1):
        filas.append([
            str(i),
            _parrafo(recortar(linea.descripcion, 90), E["celda"]),
            numero(linea.cantidad),
            pesos(linea.precio_unitario),
            pesos(linea.subtotal),
        ])

    tabla = Table(
        filas, colWidths=[10 * mm, 74 * mm, 16 * mm, 40 * mm, 34 * mm],
        repeatRows=1, hAlign="LEFT",
    )
    tabla.setStyle(_estilo_tabla([2, 3, 4], len(filas)))
    piezas += [tabla, Spacer(1, 6 * mm)]

    totales = Table(
        [
            ["Subtotal", pesos(factura.subtotal)],
            ["IVA (19%)", pesos(factura.impuestos)],
            ["Total", pesos(factura.total)],
        ],
        colWidths=[40 * mm, 34 * mm],
        hAlign="RIGHT",
    )
    totales.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -2), TINTA_SUAVE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("TEXTCOLOR", (0, -1), (-1, -1), TINTA),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, ACENTO),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        # Aire entre el rótulo y la cifra: las dos columnas van alineadas a
        # la derecha y sin esto se tocan.
        ("RIGHTPADDING", (0, 0), (0, -1), 10),
    ]))
    piezas.append(totales)

    # El total en letras.
    #
    # Es lo que lleva cualquier factura del país, y no por formalismo: un
    # cero de más en «$32.000.000» no salta a la vista, y en «TREINTA Y DOS
    # MILLONES» sí. Las dos cifras dicen lo mismo y quien lee las compara
    # sin darse cuenta.
    piezas += [
        Spacer(1, 6 * mm),
        Table(
            [[Paragraph(
                f"<b>SON:</b> {texto_para_pdf(en_letras(factura.total))}",
                E["celda"],
            )]],
            colWidths=[170 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), ACENTO_TENUE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]),
            hAlign="LEFT",
        ),
    ]

    # Pie legal, con el código de verificación.
    #
    # El código es el número de factura más el identificador de la venta: no
    # es criptografía, es lo que permite a quien recibe el papel encontrar el
    # registro exacto sin teclear un id interno que no aparece en ninguna
    # parte del documento.
    piezas += [
        Spacer(1, 10 * mm),
        _parrafo(
            f"Código de verificación: {factura.numero}-{factura.venta_id:06d}"
            f"  ·  Generado el {ahora():%d/%m/%Y a las %H:%M}",
            E["pie"],
        ),
        _parrafo(
            "Documento generado electrónicamente por el sistema AutoPrime. "
            "Conserve esta factura como soporte de su compra. "
            "Para cualquier reclamación, radique una PQR desde el sitio "
            "indicando el código de verificación.",
            E["pie"],
        ),
    ]

    return _construir(doc, piezas, buffer, titulo)


# --------------------------------------------------------------------------
#  Reporte de ventas
# --------------------------------------------------------------------------
def _titulo_periodo(desde: date, hasta: date) -> str:
    if desde == hasta:
        return f"Reporte diario de ventas · {desde:%d/%m/%Y}"
    return f"Reporte de ventas · {desde:%d/%m/%Y} a {hasta:%d/%m/%Y}"


def _variacion(actual: float, anterior: float) -> str:
    """El cambio frente al periodo anterior, ya redactado."""
    if not anterior:
        return "sin base de comparación"
    cambio = (actual - anterior) / anterior * 100
    signo = "+" if cambio >= 0 else ""
    return f"{signo}{cambio:.1f}% frente al periodo anterior"


def reporte_ventas_pdf(datos: dict) -> bytes:
    """El reporte del periodo: cifras, gráfica, series y el detalle.

    Va apaisado porque la tabla de detalle tiene siete columnas y en vertical
    obligaría a partir la descripción en tres líneas.
    """
    desde, hasta = datos["desde"], datos["hasta"]
    titulo = _titulo_periodo(desde, hasta)
    doc, buffer = _documento(titulo, apaisado=True)

    piezas = [
        _parrafo(titulo, E["titulo"]),
        _parrafo(
            f"Generado el {ahora():%d/%m/%Y a las %H:%M}"
            + (f"  ·  {datos['alcance']}" if datos.get("alcance") else ""),
            E["subtitulo"],
        ),
        Spacer(1, 8 * mm),
    ]

    # --- Tarjetas de cabecera ---
    resumen = datos["resumen"]
    comparacion = datos.get("comparacion")

    tarjetas = [
        ["Ventas", "Pagadas", "Pendientes", "Anuladas", "Ingresos", "Ticket promedio"],
        [
            numero(resumen["total"]),
            numero(resumen["pagadas"]),
            numero(resumen["pendientes"]),
            numero(resumen["anuladas"]),
            pesos(resumen["ingresos"]),
            pesos(resumen["ticket_promedio"]),
        ],
    ]

    # Tercera fila con la variación, solo si hay con qué comparar.
    #
    # «$50 mil M» no dice si el mes fue bueno. Al lado de lo que se hizo el
    # periodo anterior, sí: es la primera pregunta de cualquiera que abre un
    # reporte, y hasta ahora había que ir a buscar el reporte viejo.
    if comparacion:
        tarjetas.append([
            _variacion(resumen["total"], comparacion["total"]),
            "", "", "",
            _variacion(float(resumen["ingresos"]), float(comparacion["ingresos"])),
            _variacion(
                float(resumen["ticket_promedio"]),
                float(comparacion["ticket_promedio"]),
            ),
        ])

    tabla_tarjetas = Table(
        tarjetas, colWidths=[38 * mm] * 4 + [55 * mm, 55 * mm], hAlign="LEFT"
    )
    ordenes_tarjetas = [
        ("BACKGROUND", (0, 0), (-1, -1), ACENTO_TENUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACENTO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 13),
        ("TEXTCOLOR", (0, 1), (-1, 1), TINTA),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.6, PAPEL),
    ]
    if comparacion:
        ordenes_tarjetas += [
            ("FONTNAME", (0, 2), (-1, 2), "Helvetica"),
            ("FONTSIZE", (0, 2), (-1, 2), 6.5),
            ("TEXTCOLOR", (0, 2), (-1, 2), TINTA_SUAVE),
            ("BOTTOMPADDING", (0, 2), (-1, 2), 6),
        ]
    tabla_tarjetas.setStyle(TableStyle(ordenes_tarjetas))
    piezas += [tabla_tarjetas, Spacer(1, 6 * mm)]

    # --- Gráfica ---
    serie = datos["por_dia"]
    grafica = _grafica_barras(serie)
    if grafica is not None and any(d["ingresos"] for d in serie):
        piezas.append(KeepTogether([
            _parrafo("Ingresos por día", E["seccion"]),
            grafica,
        ]))

    # --- Serie diaria en tabla ---
    con_movimiento = [d for d in serie if d["ventas"]]
    if con_movimiento:
        filas = [["Fecha", "Ventas", "Cobrado"]]
        for dia in con_movimiento:
            filas.append([
                date.fromisoformat(dia["fecha"]).strftime("%d/%m/%Y"),
                numero(dia["ventas"]),
                pesos(dia["ingresos"]),
            ])
        # Fila de total: la tabla de arriba ya se miró, y sin el total hay
        # que sumarla a mano para comprobar que cuadra con la tarjeta.
        filas.append([
            "Total del periodo",
            numero(sum(d["ventas"] for d in con_movimiento)),
            pesos(sum(float(d["ingresos"]) for d in con_movimiento)),
        ])

        tabla = Table(filas, colWidths=[40 * mm, 26 * mm, 46 * mm], repeatRows=1,
                      hAlign="LEFT")
        estilo = _estilo_tabla([1, 2], len(filas))
        estilo.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        estilo.add("LINEABOVE", (0, -1), (-1, -1), 0.8, ACENTO)
        estilo.add("BACKGROUND", (0, -1), (-1, -1), PAPEL)
        tabla.setStyle(estilo)
        piezas.append(KeepTogether([
            _parrafo("Movimiento por día", E["seccion"]),
            # Sin esta linea, una fila que dice «1 venta, $0» parece un error
            # de cuentas. No lo es: esa venta esta pendiente de cobro o
            # anulada, y la columna mide lo que entro en caja.
            _parrafo(
                "«Ventas» cuenta todas las del dia; «Cobrado» solo lo que "
                "entro en caja, asi que un dia puede tener ventas y cero "
                "cobrado si estan pendientes o anuladas.",
                E["pie"],
            ),
            tabla,
        ]))

    # --- Rankings, uno al lado del otro ---
    def bloque_ranking(titulo_bloque, conceptos, unidad):
        filas = [[titulo_bloque, "Uds.", "Importe"]]
        for c in conceptos:
            filas.append([
                _parrafo(recortar(c["descripcion"], 46), E["celda"]),
                numero(c["unidades"]),
                pesos(c["importe"]),
            ])
        if not conceptos:
            filas.append([_parrafo(f"Ningún {unidad} en el periodo.", E["celda"]),
                          "", ""])
        tabla = Table(filas, colWidths=[64 * mm, 18 * mm, 40 * mm], repeatRows=1)
        tabla.setStyle(_estilo_tabla([1, 2], len(filas)))
        return tabla

    piezas.append(Spacer(1, 4 * mm))
    piezas.append(KeepTogether([
        _parrafo("Lo que más se vendió", E["seccion"]),
        Table(
            [[
                bloque_ranking("Vehículo", datos.get("top_vehiculos") or [], "vehículo"),
                bloque_ranking("Servicio", datos.get("top_servicios") or [], "servicio"),
            ]],
            colWidths=[124 * mm, 124 * mm],
            hAlign="LEFT",
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
            ]),
        ),
    ]))

    # --- Detalle ---
    piezas.append(_parrafo("Detalle de ventas", E["seccion"]))
    if datos["ventas"]:
        filas = [["Número", "Fecha", "Cliente", "Líneas", "Estado", "Factura", "Total"]]
        for v in datos["ventas"]:
            cliente = f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else "—"
            filas.append([
                v.numero,
                v.fecha.strftime("%d/%m/%Y %H:%M"),
                _parrafo(recortar(cliente, 38), E["celda"]),
                numero(len(v.lineas)),
                v.estado,
                v.factura.numero if v.factura else "—",
                pesos(v.total),
            ])

        filas.append([
            # `Paragraph` a pelo y no `_parrafo`: este marcado es mio, no de
            # nadie de fuera. Pasandolo por el escape salia «<b>Total</b>»
            # escrito tal cual en la ultima fila del reporte.
            "", "", Paragraph("<b>Total</b>", E["celda"]),
            numero(sum(len(v.lineas) for v in datos["ventas"])),
            "", "",
            pesos(sum(float(v.total) for v in datos["ventas"])),
        ])

        tabla = Table(
            filas,
            colWidths=[30 * mm, 32 * mm, 60 * mm, 16 * mm, 24 * mm, 30 * mm, 42 * mm],
            repeatRows=1,
            hAlign="LEFT",
        )
        estilo = _estilo_tabla([3, 6], len(filas))
        estilo.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
        estilo.add("LINEABOVE", (0, -1), (-1, -1), 0.8, ACENTO)
        estilo.add("BACKGROUND", (0, -1), (-1, -1), PAPEL)
        tabla.setStyle(estilo)
        piezas.append(tabla)

        piezas += [
            Spacer(1, 4 * mm),
            _parrafo(
                "El total de esta tabla incluye las ventas anuladas, que "
                "aparecen en el histórico pero no en los ingresos de la "
                "cabecera.",
                E["pie"],
            ),
        ]
    else:
        piezas.append(
            _parrafo("No se registraron ventas en el periodo seleccionado.",
                     E["cuerpo"])
        )

    return _construir(doc, piezas, buffer, titulo)
