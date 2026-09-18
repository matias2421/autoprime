"""Genera los PDF: la factura y el reporte de ventas.

Se usa reportlab y no un navegador sin cabeza. La versión con Chrome produce
un PDF más bonito con menos esfuerzo, pero exige un Chrome instalado en el
servidor: funcionaría en el portátil y fallaría en Render, que es donde
corre esto de verdad. reportlab es Python puro y no depende de nada del
sistema, así que el documento sale igual en los dos sitios.

Todo se arma en memoria y se devuelve como `bytes`. Escribir en disco
obligaría a decidir dónde, a limpiarlo después y a confiar en que el disco
del contenedor —que es efímero— siga ahí en la siguiente petición.
"""

import io
from datetime import date

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
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

E = estilos()


# --------------------------------------------------------------------------
#  Marco: la banda de cabecera y el pie con el número de página
# --------------------------------------------------------------------------
def _marco(titulo: str):
    """Devuelve el dibujante de cabecera y pie que reportlab llama por página.

    Va como función que fabrica otra porque el título cambia según el
    documento, y reportlab llama al dibujante sin pasarle nada más que el
    lienzo y la página.
    """

    def dibujar(lienzo, documento):
        ancho, alto = documento.pagesize
        lienzo.saveState()

        # Banda superior. Es la única tinta densa del documento: 12 mm de
        # alto, no una página entera.
        lienzo.setFillColor(TINTA)
        lienzo.rect(0, alto - 14 * mm, ancho, 14 * mm, stroke=0, fill=1)

        lienzo.setFillColor(PAPEL)
        lienzo.setFont("Helvetica-Bold", 11)
        lienzo.drawString(MARGEN, alto - 9.4 * mm, EMPRESA["nombre"].upper())

        lienzo.setFont("Helvetica", 7.5)
        lienzo.setFillColor(ACENTO_TENUE)
        lienzo.drawString(
            MARGEN + 26 * mm, alto - 9.4 * mm, EMPRESA["lema"]
        )
        lienzo.drawRightString(ancho - MARGEN, alto - 9.4 * mm, titulo)

        # Pie: quién emitió, cuándo y qué página. Sin el total de páginas no
        # se puede saber si falta la última, que es justo lo que hay que
        # poder saber de un documento contable impreso.
        lienzo.setFillColor(TINTA_SUAVE)
        lienzo.setFont("Helvetica", 7)
        lienzo.drawString(
            MARGEN,
            10 * mm,
            f"{EMPRESA['nombre']} · {EMPRESA['nit']} · {EMPRESA['contacto']}",
        )
        lienzo.drawRightString(ancho - MARGEN, 10 * mm, f"Página {documento.page}")

        lienzo.setStrokeColor(LINEA)
        lienzo.setLineWidth(0.5)
        lienzo.line(MARGEN, 13 * mm, ancho - MARGEN, 13 * mm)

        lienzo.restoreState()

    return dibujar


def _documento(titulo: str, apaisado: bool = False) -> tuple:
    buffer = io.BytesIO()
    tamano = landscape(A4) if apaisado else A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=tamano,
        leftMargin=MARGEN,
        rightMargin=MARGEN,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title=titulo,
        author=EMPRESA["nombre"],
    )
    return doc, buffer


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


# --------------------------------------------------------------------------
#  Factura
# --------------------------------------------------------------------------
def factura_pdf(factura) -> bytes:
    """La factura de una venta, lista para imprimir o adjuntar."""
    doc, buffer = _documento(f"Factura {factura.numero}")
    venta = factura.venta
    comprador = venta.cliente if venta else None

    piezas = [
        Paragraph(f"Factura {factura.numero}", E["titulo"]),
        Paragraph(
            f"Emitida el {factura.fecha_emision:%d/%m/%Y a las %H:%M}"
            f"  ·  Venta {venta.numero if venta else '—'}"
            f"  ·  Estado: {factura.estado}",
            E["subtitulo"],
        ),
        Spacer(1, 10 * mm),
    ]

    # Emisor y cliente, uno al lado del otro.
    izquierda = (
        f"<b>{EMPRESA['nombre']}</b><br/>{EMPRESA['nit']}<br/>"
        f"{EMPRESA['direccion']}<br/>{EMPRESA['contacto']}"
    )
    if comprador:
        derecha = (
            f"<b>{comprador.nombre} {comprador.apellido}</b><br/>"
            f"{comprador.tipo_documento} {comprador.numero_documento}<br/>"
            f"{comprador.direccion}<br/>{comprador.correo} · {comprador.telefono}"
        )
    else:
        derecha = "<b>Cliente no disponible</b>"

    partes = Table(
        [
            [
                Paragraph("EMITIDA POR", E["celda"]),
                Paragraph("FACTURADA A", E["celda"]),
            ],
            [Paragraph(izquierda, E["celda"]), Paragraph(derecha, E["celda"])],
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    partes.setStyle(
        TableStyle(
            [
                ("TEXTCOLOR", (0, 0), (-1, 0), ACENTO),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACENTO),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    piezas += [partes, Spacer(1, 10 * mm)]

    # Detalle.
    filas = [["#", "Descripción", "Cant.", "Precio unitario", "Subtotal"]]
    for i, linea in enumerate(factura.lineas, start=1):
        filas.append(
            [
                str(i),
                Paragraph(linea.descripcion, E["celda"]),
                numero(linea.cantidad),
                pesos(linea.precio_unitario),
                pesos(linea.subtotal),
            ]
        )

    tabla = Table(
        filas, colWidths=[10 * mm, 74 * mm, 16 * mm, 40 * mm, 34 * mm], repeatRows=1
    )
    tabla.setStyle(_estilo_tabla([2, 3, 4], len(filas)))
    piezas.append(tabla)
    piezas.append(Spacer(1, 6 * mm))

    # Totales, alineados a la derecha bajo el detalle.
    totales = Table(
        [
            ["Subtotal", pesos(factura.subtotal)],
            ["IVA (19%)", pesos(factura.impuestos)],
            ["Total", pesos(factura.total)],
        ],
        colWidths=[40 * mm, 34 * mm],
        hAlign="RIGHT",
    )
    totales.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, -2), TINTA_SUAVE),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 11),
                ("TEXTCOLOR", (0, -1), (-1, -1), TINTA),
                ("LINEABOVE", (0, -1), (-1, -1), 0.8, ACENTO),
                ("TOPPADDING", (0, -1), (-1, -1), 6),
                # Aire entre el rotulo y la cifra: las dos columnas van
                # alineadas a la derecha y sin esto se tocan.
                ("RIGHTPADDING", (0, 0), (0, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    piezas.append(totales)

    if factura.estado == "anulada":
        piezas += [
            Spacer(1, 8 * mm),
            Paragraph(
                "<b>DOCUMENTO ANULADO.</b> Esta factura fue anulada y no tiene "
                "validez para efectos de pago.",
                E["cuerpo"],
            ),
        ]

    piezas += [
        Spacer(1, 12 * mm),
        Paragraph(
            "Documento generado electrónicamente por el sistema AutoPrime. "
            "Conserve esta factura como soporte de su compra.",
            E["pie"],
        ),
    ]

    marco = _marco(f"Factura {factura.numero}")
    doc.build(piezas, onFirstPage=marco, onLaterPages=marco)
    return buffer.getvalue()


# --------------------------------------------------------------------------
#  Reporte de ventas
# --------------------------------------------------------------------------
def _titulo_periodo(desde: date, hasta: date) -> str:
    if desde == hasta:
        return f"Reporte diario de ventas · {desde:%d/%m/%Y}"
    return f"Reporte de ventas · {desde:%d/%m/%Y} a {hasta:%d/%m/%Y}"


def reporte_ventas_pdf(datos: dict) -> bytes:
    """El reporte del periodo: cifras, series y el detalle de cada venta.

    Va apaisado porque la tabla de detalle tiene siete columnas y en vertical
    obligaría a partir la descripción en tres líneas.
    """
    desde, hasta = datos["desde"], datos["hasta"]
    titulo = _titulo_periodo(desde, hasta)
    doc, buffer = _documento(titulo, apaisado=True)

    piezas = [
        Paragraph(titulo, E["titulo"]),
        Paragraph(
            f"Generado el {ahora():%d/%m/%Y a las %H:%M}"
            + (f"  ·  {datos['alcance']}" if datos.get("alcance") else ""),
            E["subtitulo"],
        ),
        Spacer(1, 8 * mm),
    ]

    # --- Tarjetas de cabecera ---
    resumen = datos["resumen"]
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
    tabla_tarjetas = Table(
        tarjetas, colWidths=[38 * mm] * 4 + [55 * mm, 55 * mm], hAlign="LEFT"
    )
    tabla_tarjetas.setStyle(
        TableStyle(
            [
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
        )
    )
    piezas += [tabla_tarjetas, Spacer(1, 4 * mm)]

    # --- Serie diaria ---
    serie = [d for d in datos["por_dia"] if d["ventas"]]
    if serie:
        filas = [["Fecha", "Ventas", "Ingresos"]]
        for dia in serie:
            filas.append(
                [
                    date.fromisoformat(dia["fecha"]).strftime("%d/%m/%Y"),
                    numero(dia["ventas"]),
                    pesos(dia["ingresos"]),
                ]
            )
        tabla = Table(filas, colWidths=[40 * mm, 26 * mm, 46 * mm], repeatRows=1,
                      hAlign="LEFT")
        tabla.setStyle(_estilo_tabla([1, 2], len(filas)))
        piezas.append(
            KeepTogether(
                [Paragraph("Movimiento por día", E["seccion"]), tabla]
            )
        )

    # --- Vehículos más vendidos ---
    if datos["top_vehiculos"]:
        filas = [["Vehículo", "Unidades", "Importe"]]
        for v in datos["top_vehiculos"]:
            filas.append(
                [
                    Paragraph(v["descripcion"], E["celda"]),
                    numero(v["unidades"]),
                    pesos(v["importe"]),
                ]
            )
        tabla = Table(filas, colWidths=[110 * mm, 26 * mm, 46 * mm], repeatRows=1,
                      hAlign="LEFT")
        tabla.setStyle(_estilo_tabla([1, 2], len(filas)))
        piezas.append(
            KeepTogether(
                [Paragraph("Vehículos más vendidos", E["seccion"]), tabla]
            )
        )

    # --- Detalle ---
    piezas.append(Paragraph("Detalle de ventas", E["seccion"]))
    if datos["ventas"]:
        filas = [
            ["Número", "Fecha", "Cliente", "Líneas", "Estado", "Factura", "Total"]
        ]
        for v in datos["ventas"]:
            cliente = f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else "—"
            filas.append(
                [
                    v.numero,
                    v.fecha.strftime("%d/%m/%Y %H:%M"),
                    Paragraph(cliente, E["celda"]),
                    numero(len(v.lineas)),
                    v.estado,
                    v.factura.numero if v.factura else "—",
                    pesos(v.total),
                ]
            )
        tabla = Table(
            filas,
            colWidths=[30 * mm, 32 * mm, 60 * mm, 16 * mm, 24 * mm, 30 * mm, 42 * mm],
            repeatRows=1,
            hAlign="LEFT",
        )
        tabla.setStyle(_estilo_tabla([3, 6], len(filas)))
        piezas.append(tabla)
    else:
        piezas.append(
            Paragraph(
                "No se registraron ventas en el periodo seleccionado.", E["cuerpo"]
            )
        )

    marco = _marco(titulo)
    doc.build(piezas, onFirstPage=marco, onLaterPages=marco)
    return buffer.getvalue()
