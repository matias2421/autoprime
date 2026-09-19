"""Genera el libro de Excel del reporte de ventas.

Se usa XlsxWriter y no openpyxl porque aquí solo se escribe, nunca se lee un
libro existente, y XlsxWriter escribe más rápido y con menos memoria: va
volcando el archivo en vez de mantener el libro entero en RAM.

Lo que distingue este Excel de un CSV con otra extensión es que los importes
salen como NÚMEROS con formato de moneda, no como texto ya formateado. Si
salieran como «$ 3.200.000.000,00», quien lo abra no puede sumarlos, ni
ordenarlos, ni meterlos en una tabla dinámica —que es justo para lo que se
pide el Excel en vez del PDF—.

SOBRE LA SEGURIDAD DE ESTE ARCHIVO
----------------------------------
Todo texto que escribió una persona pasa por `texto_para_excel` antes de
entrar en una celda, y el libro se abre con `strings_to_formulas` apagado.
Las dos cosas hacen falta y ninguna sobra: sin la segunda, XlsxWriter
convertía una cadena que empieza por `=` en una fórmula VIVA dentro del
archivo; sin la primera, Excel reinterpreta al abrir lo que empieza por
`+`, `-` o `@` aunque se haya guardado como texto. Ver `seguridad.py`.
"""

import io
from datetime import date

import xlsxwriter

from app.core.tiempo import ahora
from app.reportes.seguridad import texto_para_excel

# Ancho de columna en «caracteres», que es como los mide Excel.
ANCHOS_DETALLE = [16, 18, 30, 26, 9, 13, 16, 16, 16, 16]

MONEDA = '"$" #,##0'
MONEDA_CENTIMOS = '"$" #,##0.00'


def _formatos(libro) -> dict:
    """Los formatos del libro. Se crean una vez y se reutilizan.

    XlsxWriter guarda un formato por cada llamada a `add_format`, y crearlos
    dentro del bucle de filas produce un libro con miles de formatos
    idénticos que Excel tarda en abrir.
    """
    base_borde = {"border": 1, "border_color": "#d5d5db"}

    return {
        "titulo": libro.add_format(
            {"bold": True, "font_size": 16, "font_color": "#111114"}
        ),
        "subtitulo": libro.add_format({"font_size": 10, "font_color": "#55555c"}),
        "seccion": libro.add_format(
            {"bold": True, "font_size": 11, "font_color": "#3d6274"}
        ),
        "nota": libro.add_format(
            {"font_size": 9, "font_color": "#8a8a92", "italic": True}
        ),
        "cabecera": libro.add_format(
            {
                "bold": True,
                "font_color": "#ffffff",
                "bg_color": "#3d6274",
                "border": 1,
                "border_color": "#3d6274",
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "texto": libro.add_format(base_borde),
        "entero": libro.add_format({**base_borde, "num_format": "#,##0"}),
        "dinero": libro.add_format({**base_borde, "num_format": MONEDA_CENTIMOS}),
        "porcentaje": libro.add_format({**base_borde, "num_format": "0.0%"}),
        "fecha": libro.add_format({**base_borde, "num_format": "dd/mm/yyyy hh:mm"}),
        "dia": libro.add_format({**base_borde, "num_format": "dd/mm/yyyy"}),

        # Fila de totales: la que se mira primero al abrir una tabla larga.
        "total_texto": libro.add_format(
            {**base_borde, "bold": True, "bg_color": "#e8eef1", "top": 2,
             "top_color": "#3d6274"}
        ),
        "total_entero": libro.add_format(
            {**base_borde, "bold": True, "bg_color": "#e8eef1", "top": 2,
             "top_color": "#3d6274", "num_format": "#,##0"}
        ),
        "total_dinero": libro.add_format(
            {**base_borde, "bold": True, "bg_color": "#e8eef1", "top": 2,
             "top_color": "#3d6274", "num_format": MONEDA_CENTIMOS}
        ),

        "tarjeta_rotulo": libro.add_format(
            {
                "bold": True,
                "font_size": 9,
                "font_color": "#3d6274",
                "bg_color": "#e8eef1",
                "align": "center",
                "border": 1,
                "border_color": "#ffffff",
            }
        ),
        "tarjeta_cifra": libro.add_format(
            {
                "bold": True,
                "font_size": 14,
                "bg_color": "#e8eef1",
                "align": "center",
                "border": 1,
                "border_color": "#ffffff",
                "num_format": "#,##0",
            }
        ),
        "tarjeta_dinero": libro.add_format(
            {
                "bold": True,
                "font_size": 14,
                "bg_color": "#e8eef1",
                "align": "center",
                "border": 1,
                "border_color": "#ffffff",
                "num_format": MONEDA,
            }
        ),
    }


def _escribir_texto(hoja, fila, columna, valor, formato):
    """Escribe texto de origen ajeno, ya neutralizado.

    Existe para que no haya que acordarse: si una celda de texto se escribe
    con `hoja.write` a secas, se escapa del filtro y vuelve el problema.
    """
    hoja.write_string(fila, columna, texto_para_excel(valor), formato)


def reporte_ventas_excel(datos: dict) -> bytes:
    """Devuelve el .xlsx como bytes: cuatro hojas y dos gráficas."""
    buffer = io.BytesIO()
    libro = xlsxwriter.Workbook(
        buffer,
        {
            "in_memory": True,
            "default_date_format": "dd/mm/yyyy",
            # Sin esto, una cadena que empieza por `=` se guarda como
            # fórmula viva. Ver la cabecera del módulo.
            "strings_to_formulas": False,
            "strings_to_urls": False,
        },
    )
    libro.set_properties({
        "title": "AutoPrime · Reporte de ventas",
        "company": "AutoPrime",
        "comments": "Generado automáticamente por la API de AutoPrime.",
    })
    f = _formatos(libro)

    desde, hasta = datos["desde"], datos["hasta"]
    periodo = (
        f"{desde:%d/%m/%Y}" if desde == hasta else f"{desde:%d/%m/%Y} a {hasta:%d/%m/%Y}"
    )
    ventas = datos["ventas"]

    # ---------------------------------------------------------------- resumen
    hoja = libro.add_worksheet("Resumen")
    hoja.hide_gridlines(2)
    hoja.set_column(0, 5, 20)

    hoja.write(0, 0, "AutoPrime · Reporte de ventas", f["titulo"])
    hoja.write(1, 0, f"Periodo: {periodo}", f["subtitulo"])
    hoja.write(2, 0, f"Generado el {ahora():%d/%m/%Y a las %H:%M}", f["subtitulo"])
    if datos.get("alcance"):
        _escribir_texto(hoja, 3, 0, datos["alcance"], f["subtitulo"])

    resumen = datos["resumen"]
    rotulos = ["Ventas", "Pagadas", "Pendientes", "Anuladas", "Ingresos", "Ticket prom."]
    cifras = [
        resumen["total"],
        resumen["pagadas"],
        resumen["pendientes"],
        resumen["anuladas"],
        float(resumen["ingresos"]),
        float(resumen["ticket_promedio"]),
    ]
    for columna, (rotulo, cifra) in enumerate(zip(rotulos, cifras)):
        formato = f["tarjeta_dinero"] if columna >= 4 else f["tarjeta_cifra"]
        hoja.write(5, columna, rotulo, f["tarjeta_rotulo"])
        hoja.write_number(6, columna, cifra, formato)
    hoja.set_row(6, 26)

    # Comparación con el periodo anterior, si viene calculada.
    #
    # Una cifra suelta no dice si el mes fue bueno. «$50 mil M» solo
    # significa algo al lado de lo que se hizo el mes pasado, y esa
    # comparación es la primera pregunta de cualquiera que abra un reporte.
    comparacion = datos.get("comparacion")
    if comparacion:
        hoja.write(8, 0, "Frente al periodo anterior", f["seccion"])
        hoja.write(9, 0, "Concepto", f["cabecera"])
        hoja.write(9, 1, "Periodo actual", f["cabecera"])
        hoja.write(9, 2, "Periodo anterior", f["cabecera"])
        hoja.write(9, 3, "Variación", f["cabecera"])

        filas_comparacion = [
            ("Ventas", resumen["total"], comparacion["total"], f["entero"]),
            ("Ingresos", float(resumen["ingresos"]),
             float(comparacion["ingresos"]), f["dinero"]),
            ("Ticket promedio", float(resumen["ticket_promedio"]),
             float(comparacion["ticket_promedio"]), f["dinero"]),
        ]
        for i, (concepto, actual, anterior, formato) in enumerate(filas_comparacion):
            fila = 10 + i
            _escribir_texto(hoja, fila, 0, concepto, f["texto"])
            hoja.write_number(fila, 1, actual, formato)
            hoja.write_number(fila, 2, anterior, formato)
            if anterior:
                hoja.write_number(fila, 3, (actual - anterior) / anterior,
                                  f["porcentaje"])
            else:
                _escribir_texto(hoja, fila, 3, "sin base", f["texto"])

        inicio_serie = 15
    else:
        inicio_serie = 9

    # Movimiento por día, con la gráfica al lado.
    hoja.write(inicio_serie, 0, "Movimiento por día", f["seccion"])
    cabecera_serie = inicio_serie + 1
    for columna, rotulo in enumerate(["Fecha", "Ventas", "Ingresos"]):
        hoja.write(cabecera_serie, columna, rotulo, f["cabecera"])

    fila = cabecera_serie + 1
    primera_serie = fila
    for dia in datos["por_dia"]:
        hoja.write_datetime(fila, 0, date.fromisoformat(dia["fecha"]), f["dia"])
        hoja.write_number(fila, 1, dia["ventas"], f["entero"])
        hoja.write_number(fila, 2, float(dia["ingresos"]), f["dinero"])
        fila += 1

    if datos["por_dia"]:
        ultima = fila - 1

        # Los totales van como FÓRMULA, no como un número ya sumado.
        #
        # Quien abra el archivo y filtre o edite una fila ve el total
        # recalcularse. Con el número escrito a mano, la tabla y su total
        # empiezan a contradecirse en cuanto alguien toca algo, y no hay
        # manera de saber cuál de los dos miente.
        _escribir_texto(hoja, fila, 0, "Total del periodo", f["total_texto"])
        hoja.write_formula(
            fila, 1, f"=SUM(B{primera_serie + 1}:B{ultima + 1})", f["total_entero"]
        )
        hoja.write_formula(
            fila, 2, f"=SUM(C{primera_serie + 1}:C{ultima + 1})", f["total_dinero"]
        )

        grafica = libro.add_chart({"type": "column"})
        grafica.add_series({
            "name": "Ingresos",
            "categories": ["Resumen", primera_serie, 0, ultima, 0],
            "values": ["Resumen", primera_serie, 2, ultima, 2],
            "fill": {"color": "#3d6274"},
        })
        grafica.set_title({"name": f"Ingresos por día · {periodo}"})
        grafica.set_legend({"none": True})
        grafica.set_y_axis({"num_format": MONEDA})
        grafica.set_size({"width": 620, "height": 300})
        hoja.insert_chart(cabecera_serie, 4, grafica)

        # Segunda gráfica: el número de ventas, que es otra pregunta.
        # Un mes puede ingresar más con menos ventas —una sola pieza cara— y
        # con una única gráfica de dinero eso no se ve.
        conteo = libro.add_chart({"type": "line"})
        conteo.add_series({
            "name": "Ventas",
            "categories": ["Resumen", primera_serie, 0, ultima, 0],
            "values": ["Resumen", primera_serie, 1, ultima, 1],
            "line": {"color": "#8a5a3c", "width": 2},
            "marker": {"type": "circle", "size": 5},
        })
        conteo.set_title({"name": "Número de ventas por día"})
        conteo.set_legend({"none": True})
        conteo.set_size({"width": 620, "height": 240})
        hoja.insert_chart(cabecera_serie + 17, 4, conteo)

    # ---------------------------------------------------------------- detalle
    hoja = libro.add_worksheet("Detalle")
    hoja.hide_gridlines(2)
    for columna, ancho in enumerate(ANCHOS_DETALLE):
        hoja.set_column(columna, columna, ancho)

    encabezados = [
        "Número", "Fecha", "Cliente", "Vendedor", "Líneas", "Estado",
        "Factura", "Subtotal", "IVA", "Total",
    ]
    for columna, rotulo in enumerate(encabezados):
        hoja.write(0, columna, rotulo, f["cabecera"])

    fila = 1
    for v in ventas:
        cliente = f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else "—"
        vendedor = f"{v.vendedor.nombre} {v.vendedor.apellido}" if v.vendedor else "Web"
        _escribir_texto(hoja, fila, 0, v.numero, f["texto"])
        hoja.write_datetime(fila, 1, v.fecha, f["fecha"])
        _escribir_texto(hoja, fila, 2, cliente, f["texto"])
        _escribir_texto(hoja, fila, 3, vendedor, f["texto"])
        hoja.write_number(fila, 4, len(v.lineas), f["entero"])
        _escribir_texto(hoja, fila, 5, v.estado, f["texto"])
        _escribir_texto(hoja, fila, 6, v.factura.numero if v.factura else "—", f["texto"])
        hoja.write_number(fila, 7, float(v.subtotal), f["dinero"])
        hoja.write_number(fila, 8, float(v.impuestos), f["dinero"])
        hoja.write_number(fila, 9, float(v.total), f["dinero"])
        fila += 1

    if fila > 1:
        # SUBTOTAL(109, ...) y no SUM: ignora las filas que el autofiltro
        # esconde. Al filtrar por «pagada», el total pasa a ser el de lo
        # pagado, que es lo que uno espera al filtrar.
        _escribir_texto(hoja, fila, 0, "Total", f["total_texto"])
        for columna in range(1, 7):
            _escribir_texto(hoja, fila, columna, "", f["total_texto"])
        hoja.write_formula(fila, 4, f"=SUBTOTAL(109,E2:E{fila})", f["total_entero"])
        for columna, letra in ((7, "H"), (8, "I"), (9, "J")):
            hoja.write_formula(
                fila, columna, f"=SUBTOTAL(109,{letra}2:{letra}{fila})",
                f["total_dinero"],
            )

        hoja.autofilter(0, 0, fila - 1, len(encabezados) - 1)
        hoja.freeze_panes(1, 0)

        # El estado se colorea solo. En una tabla de treinta filas, buscar
        # las anuladas a ojo es leerlas una por una.
        for estado, color, fondo in (
            ("pagada", "#0b6b3a", "#d8f3e3"),
            ("pendiente", "#7a5200", "#fdf0d0"),
            ("anulada", "#8a1c1c", "#fadbd8"),
        ):
            hoja.conditional_format(1, 5, fila - 1, 5, {
                "type": "cell", "criteria": "==", "value": f'"{estado}"',
                "format": libro.add_format({
                    "font_color": color, "bg_color": fondo, "bold": True,
                    "border": 1, "border_color": "#d5d5db",
                }),
            })

        # Barras dentro de la celda del total: el tamaño relativo de cada
        # venta se ve sin tener que comparar cifras de doce dígitos.
        hoja.conditional_format(1, 9, fila - 1, 9, {
            "type": "data_bar", "bar_color": "#3d6274", "bar_solid": True,
        })
    else:
        _escribir_texto(hoja, 1, 0, "Sin ventas en el periodo seleccionado.",
                        f["texto"])

    # ------------------------------------------------------------------ lineas
    hoja = libro.add_worksheet("Líneas")
    hoja.hide_gridlines(2)
    hoja.set_column(0, 0, 16)
    hoja.set_column(1, 1, 46)
    hoja.set_column(2, 6, 16)

    encabezados = ["Venta", "Descripción", "Tipo", "Cantidad", "Precio unitario",
                   "Descuento", "Subtotal"]
    for columna, rotulo in enumerate(encabezados):
        hoja.write(0, columna, rotulo, f["cabecera"])

    fila = 1
    for v in ventas:
        for linea in v.lineas:
            _escribir_texto(hoja, fila, 0, v.numero, f["texto"])
            _escribir_texto(hoja, fila, 1, linea.descripcion, f["texto"])
            _escribir_texto(
                hoja, fila, 2,
                "Vehículo" if linea.producto_id else "Servicio", f["texto"],
            )
            hoja.write_number(fila, 3, linea.cantidad, f["entero"])
            hoja.write_number(fila, 4, float(linea.precio_unitario), f["dinero"])
            hoja.write_number(fila, 5, float(linea.descuento), f["dinero"])
            hoja.write_number(fila, 6, float(linea.subtotal), f["dinero"])
            fila += 1

    if fila > 1:
        _escribir_texto(hoja, fila, 0, "Total", f["total_texto"])
        for columna in (1, 2):
            _escribir_texto(hoja, fila, columna, "", f["total_texto"])
        hoja.write_formula(fila, 3, f"=SUBTOTAL(109,D2:D{fila})", f["total_entero"])
        for columna, letra in ((4, "E"), (5, "F"), (6, "G")):
            hoja.write_formula(
                fila, columna, f"=SUBTOTAL(109,{letra}2:{letra}{fila})",
                f["total_dinero"],
            )
        hoja.autofilter(0, 0, fila - 1, len(encabezados) - 1)
        hoja.freeze_panes(1, 0)
    else:
        _escribir_texto(hoja, 1, 0, "Sin líneas en el periodo seleccionado.",
                        f["texto"])

    # ------------------------------------------------------------------ rankings
    #
    # Hoja nueva. Antes los rankings solo estaban en el PDF, que no se puede
    # ordenar ni sumar: quien quisiera trabajar con ellos tenía que
    # teclearlos a mano desde el documento impreso.
    hoja = libro.add_worksheet("Ranking")
    hoja.hide_gridlines(2)
    hoja.set_column(0, 0, 42)
    hoja.set_column(1, 3, 18)

    fila = 0
    for titulo, conceptos in (
        ("Vehículos más vendidos", datos.get("top_vehiculos") or []),
        ("Servicios más vendidos", datos.get("top_servicios") or []),
    ):
        hoja.write(fila, 0, titulo, f["seccion"])
        fila += 1
        for columna, rotulo in enumerate(
            ["Concepto", "Unidades", "Importe", "% del total"]
        ):
            hoja.write(fila, columna, rotulo, f["cabecera"])
        fila += 1

        total_bloque = sum(float(c["importe"]) for c in conceptos) or 1
        primera = fila
        for concepto in conceptos:
            _escribir_texto(hoja, fila, 0, concepto["descripcion"], f["texto"])
            hoja.write_number(fila, 1, concepto["unidades"], f["entero"])
            hoja.write_number(fila, 2, float(concepto["importe"]), f["dinero"])
            hoja.write_number(
                fila, 3, float(concepto["importe"]) / total_bloque, f["porcentaje"]
            )
            fila += 1

        if conceptos:
            hoja.conditional_format(primera, 2, fila - 1, 2, {
                "type": "data_bar", "bar_color": "#3d6274", "bar_solid": True,
            })
        else:
            _escribir_texto(hoja, fila, 0, "Sin movimiento en el periodo.",
                            f["texto"])
            fila += 1

        fila += 2

    hoja.write(fila, 0, "Los porcentajes son sobre el importe de cada ranking, "
                        "no sobre el total del periodo.", f["nota"])

    libro.close()
    return buffer.getvalue()
