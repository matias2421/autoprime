"""Genera el libro de Excel del reporte de ventas.

Se usa XlsxWriter y no openpyxl porque aquí solo se escribe, nunca se lee un
libro existente, y XlsxWriter escribe más rápido y con menos memoria: va
volcando el archivo en vez de mantener el libro entero en RAM.

Lo que distingue este Excel de un CSV con otra extensión es que los importes
salen como NÚMEROS con formato de moneda, no como texto ya formateado. Si
salieran como «$ 3.200.000.000,00», quien lo abra no puede sumarlos, ni
ordenarlos, ni meterlos en una tabla dinámica —que es justo para lo que se
pide el Excel en vez del PDF—.
"""

import io
from datetime import date

import xlsxwriter

from app.core.tiempo import ahora

# Ancho de columna en «caracteres», que es como los mide Excel.
ANCHOS_DETALLE = [16, 18, 30, 26, 9, 13, 16, 16, 16, 16]


def _formatos(libro) -> dict:
    """Los formatos del libro. Se crean una vez y se reutilizan.

    XlsxWriter guarda un formato por cada llamada a `add_format`, y crearlos
    dentro del bucle de filas produce un libro con miles de formatos
    idénticos que Excel tarda en abrir.
    """
    return {
        "titulo": libro.add_format(
            {"bold": True, "font_size": 16, "font_color": "#111114"}
        ),
        "subtitulo": libro.add_format({"font_size": 10, "font_color": "#55555c"}),
        "seccion": libro.add_format(
            {"bold": True, "font_size": 11, "font_color": "#3d6274"}
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
        "texto": libro.add_format({"border": 1, "border_color": "#d5d5db"}),
        "entero": libro.add_format(
            {"border": 1, "border_color": "#d5d5db", "num_format": "#,##0"}
        ),
        "dinero": libro.add_format(
            {
                "border": 1,
                "border_color": "#d5d5db",
                # Formato colombiano. El punto de miles y la coma decimal los
                # pone Excel según la configuración regional de quien abra el
                # archivo; aquí se declara la forma, no los separadores.
                "num_format": '"$" #,##0.00',
            }
        ),
        "fecha": libro.add_format(
            {
                "border": 1,
                "border_color": "#d5d5db",
                "num_format": "dd/mm/yyyy hh:mm",
            }
        ),
        "dia": libro.add_format(
            {"border": 1, "border_color": "#d5d5db", "num_format": "dd/mm/yyyy"}
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
                "num_format": '"$" #,##0',
            }
        ),
    }


def reporte_ventas_excel(datos: dict) -> bytes:
    """Devuelve el .xlsx como bytes: tres hojas y una gráfica."""
    buffer = io.BytesIO()
    libro = xlsxwriter.Workbook(
        buffer, {"in_memory": True, "default_date_format": "dd/mm/yyyy"}
    )
    f = _formatos(libro)

    desde, hasta = datos["desde"], datos["hasta"]
    periodo = (
        f"{desde:%d/%m/%Y}" if desde == hasta else f"{desde:%d/%m/%Y} a {hasta:%d/%m/%Y}"
    )

    # ---------------------------------------------------------------- resumen
    hoja = libro.add_worksheet("Resumen")
    hoja.hide_gridlines(2)
    hoja.set_column(0, 5, 20)

    hoja.write(0, 0, "AutoPrime · Reporte de ventas", f["titulo"])
    hoja.write(1, 0, f"Periodo: {periodo}", f["subtitulo"])
    hoja.write(
        2, 0, f"Generado el {ahora():%d/%m/%Y a las %H:%M}", f["subtitulo"]
    )
    if datos.get("alcance"):
        hoja.write(3, 0, datos["alcance"], f["subtitulo"])

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

    # Movimiento por día, con la gráfica al lado.
    hoja.write(9, 0, "Movimiento por día", f["seccion"])
    for columna, rotulo in enumerate(["Fecha", "Ventas", "Ingresos"]):
        hoja.write(10, columna, rotulo, f["cabecera"])

    fila = 11
    for dia in datos["por_dia"]:
        hoja.write_datetime(fila, 0, date.fromisoformat(dia["fecha"]), f["dia"])
        hoja.write_number(fila, 1, dia["ventas"], f["entero"])
        hoja.write_number(fila, 2, float(dia["ingresos"]), f["dinero"])
        fila += 1

    if datos["por_dia"]:
        ultima = fila - 1
        grafica = libro.add_chart({"type": "column"})
        grafica.add_series(
            {
                "name": "Ingresos",
                "categories": ["Resumen", 11, 0, ultima, 0],
                "values": ["Resumen", 11, 2, ultima, 2],
                "fill": {"color": "#3d6274"},
            }
        )
        grafica.set_title({"name": f"Ingresos por día · {periodo}"})
        grafica.set_legend({"none": True})
        grafica.set_y_axis({"num_format": '"$" #,##0'})
        grafica.set_size({"width": 620, "height": 320})
        hoja.insert_chart(10, 4, grafica)

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
    for v in datos["ventas"]:
        cliente = f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else "—"
        vendedor = f"{v.vendedor.nombre} {v.vendedor.apellido}" if v.vendedor else "Web"
        hoja.write(fila, 0, v.numero, f["texto"])
        hoja.write_datetime(fila, 1, v.fecha, f["fecha"])
        hoja.write(fila, 2, cliente, f["texto"])
        hoja.write(fila, 3, vendedor, f["texto"])
        hoja.write_number(fila, 4, len(v.lineas), f["entero"])
        hoja.write(fila, 5, v.estado, f["texto"])
        hoja.write(fila, 6, v.factura.numero if v.factura else "—", f["texto"])
        hoja.write_number(fila, 7, float(v.subtotal), f["dinero"])
        hoja.write_number(fila, 8, float(v.impuestos), f["dinero"])
        hoja.write_number(fila, 9, float(v.total), f["dinero"])
        fila += 1

    if fila > 1:
        # El autofiltro y los paneles fijos son lo que convierte una tabla
        # larga en algo consultable: la cabecera se queda a la vista al bajar.
        hoja.autofilter(0, 0, fila - 1, len(encabezados) - 1)
        hoja.freeze_panes(1, 0)
    else:
        hoja.write(1, 0, "Sin ventas en el periodo seleccionado.", f["texto"])

    # ------------------------------------------------------------------ lineas
    hoja = libro.add_worksheet("Líneas")
    hoja.hide_gridlines(2)
    hoja.set_column(0, 0, 16)
    hoja.set_column(1, 1, 46)
    hoja.set_column(2, 5, 16)

    encabezados = ["Venta", "Descripción", "Cantidad", "Precio unitario",
                   "Descuento", "Subtotal"]
    for columna, rotulo in enumerate(encabezados):
        hoja.write(0, columna, rotulo, f["cabecera"])

    fila = 1
    for v in datos["ventas"]:
        for linea in v.lineas:
            hoja.write(fila, 0, v.numero, f["texto"])
            hoja.write(fila, 1, linea.descripcion, f["texto"])
            hoja.write_number(fila, 2, linea.cantidad, f["entero"])
            hoja.write_number(fila, 3, float(linea.precio_unitario), f["dinero"])
            hoja.write_number(fila, 4, float(linea.descuento), f["dinero"])
            hoja.write_number(fila, 5, float(linea.subtotal), f["dinero"])
            fila += 1

    if fila > 1:
        hoja.autofilter(0, 0, fila - 1, len(encabezados) - 1)
        hoja.freeze_panes(1, 0)
    else:
        hoja.write(1, 0, "Sin líneas en el periodo seleccionado.", f["texto"])

    libro.close()
    return buffer.getvalue()
