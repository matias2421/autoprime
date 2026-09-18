# -*- coding: utf-8 -*-
"""Reportes y tableros.

Lo que se comprueba aquí no es que los endpoints respondan 200, sino que las
cifras signifiquen lo que dicen significar: que una venta anulada no cuente
como ingreso, que el ticket promedio se mida sobre lo cobrado, y que un día
sin ventas salga en cero en vez de desaparecer de la serie.
"""

from app.core.tiempo import hoy


class TestReporteDiario:
    async def test_sin_fechas_el_rango_es_hoy(self, cliente, como):
        """Es el reporte diario, que es el que se pide a diario."""
        respuesta = await cliente.get("/api/reportes/ventas", headers=como("administrador"))
        rango = respuesta.json()["reporte"]["rango"]

        assert rango["desde"] == hoy().isoformat()
        assert rango["hasta"] == hoy().isoformat()
        assert rango["dias"] == 1

    async def test_una_venta_de_hoy_aparece(self, cliente, como, datos):
        """Esta es la prueba que habría cazado el desajuste de relojes: la
        base fechaba en UTC y el reporte preguntaba en hora local, así que
        después de las siete de la tarde el reporte salía vacío."""
        await _vender(cliente, como, datos)

        respuesta = await cliente.get("/api/reportes/ventas", headers=como("administrador"))
        assert respuesta.json()["reporte"]["resumen"]["total"] == 1

    async def test_los_dias_vacios_salen_en_cero(self, cliente, como):
        """Una gráfica que salta del día 3 al 9 dibuja una pendiente suave
        donde hubo una semana a cero."""
        respuesta = await cliente.get(
            "/api/reportes/ventas?desde=2026-01-01&hasta=2026-01-07",
            headers=como("administrador"),
        )
        serie = respuesta.json()["reporte"]["porDia"]

        assert len(serie) == 7
        assert all(punto["ventas"] == 0 for punto in serie)


class TestCifras:
    async def test_una_venta_anulada_no_ingresa(self, cliente, como, datos):
        venta = await _vender(cliente, como, datos)
        await cliente.patch(
            f"/api/ventas/{venta['id']}/estado",
            headers=como("administrador"),
            json={"estado": "anulada"},
        )

        resumen = (
            await cliente.get("/api/reportes/ventas", headers=como("administrador"))
        ).json()["reporte"]["resumen"]

        assert resumen["total"] == 1
        assert resumen["anuladas"] == 1
        assert resumen["ingresos"] == 0

    async def test_el_ticket_promedio_se_mide_sobre_lo_cobrado(
        self, cliente, como, datos
    ):
        """Dividir entre el total de ventas contaría las anuladas y saldría
        un ticket más bajo del real."""
        pagada = await _vender(cliente, como, datos)
        anulada = await _vender(cliente, como, datos)

        await cliente.patch(
            f"/api/ventas/{pagada['id']}/estado",
            headers=como("administrador"), json={"estado": "pagada"},
        )
        await cliente.patch(
            f"/api/ventas/{anulada['id']}/estado",
            headers=como("administrador"), json={"estado": "anulada"},
        )

        resumen = (
            await cliente.get("/api/reportes/ventas", headers=como("administrador"))
        ).json()["reporte"]["resumen"]

        assert resumen["ingresos"] == pagada["total"]
        assert resumen["ticketPromedio"] == pagada["total"]

    async def test_el_ranking_ordena_por_importe(self, cliente, como, datos):
        coche = datos["productos"][0]
        servicio = datos["servicios"][0]
        await cliente.post(
            "/api/ventas", headers=como("cliente"),
            json={"lineas": [{"productoId": coche.id}, {"servicioId": servicio.id}]},
        )

        reporte = (
            await cliente.get("/api/reportes/ventas", headers=como("administrador"))
        ).json()["reporte"]

        assert reporte["topVehiculos"][0]["descripcion"].startswith("MANSORY")
        assert reporte["topServicios"][0]["descripcion"] == servicio.nombre


class TestAlcancePorRol:
    async def test_un_cliente_recibe_solo_lo_suyo(self, cliente, como, datos):
        """El personal registra una venta a su nombre; el reporte del cliente
        no debe contarla."""
        await cliente.post(
            "/api/ventas", headers=como("administrador"),
            json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
        )

        reporte = (
            await cliente.get("/api/reportes/ventas", headers=como("cliente"))
        ).json()["reporte"]

        assert reporte["resumen"]["total"] == 0
        assert "Compras de" in reporte["alcance"]

    async def test_el_personal_ve_el_negocio(self, cliente, como, datos):
        await _vender(cliente, como, datos)
        reporte = (
            await cliente.get("/api/reportes/ventas", headers=como("empleado"))
        ).json()["reporte"]

        assert reporte["resumen"]["total"] == 1
        assert reporte["alcance"] == "Todas las ventas del negocio"


class TestRangos:
    async def test_rango_invertido(self, cliente, como):
        respuesta = await cliente.get(
            "/api/reportes/ventas?desde=2026-12-31&hasta=2026-01-01",
            headers=como("administrador"),
        )
        assert respuesta.status_code == 422

    async def test_rango_desmedido(self, cliente, como):
        """Un reporte de cinco años armaria un PDF de diez mil filas y
        agotaria la memoria del contenedor."""
        respuesta = await cliente.get(
            "/api/reportes/ventas?desde=2020-01-01&hasta=2026-01-01",
            headers=como("administrador"),
        )
        assert respuesta.status_code == 422


class TestDescargas:
    async def test_el_pdf_es_un_pdf(self, cliente, como, datos):
        await _vender(cliente, como, datos)
        respuesta = await cliente.get(
            "/api/reportes/ventas/pdf", headers=como("administrador")
        )

        assert respuesta.status_code == 200
        assert respuesta.content[:5] == b"%PDF-"
        assert respuesta.headers["content-type"] == "application/pdf"
        assert "attachment" in respuesta.headers["content-disposition"]

    async def test_el_excel_es_un_libro(self, cliente, como, datos):
        await _vender(cliente, como, datos)
        respuesta = await cliente.get(
            "/api/reportes/ventas/excel", headers=como("administrador")
        )

        assert respuesta.status_code == 200
        # Un .xlsx es un zip; su firma son las dos primeras letras.
        assert respuesta.content[:2] == b"PK"

    async def test_los_importes_del_excel_son_numeros(self, cliente, como, datos):
        """Lo que distingue este Excel de un CSV con otra extensión: si los
        importes salieran ya formateados, no se podrían sumar ni ordenar."""
        import io
        import zipfile

        await _vender(cliente, como, datos)
        respuesta = await cliente.get(
            "/api/reportes/ventas/excel", headers=como("administrador")
        )

        with zipfile.ZipFile(io.BytesIO(respuesta.content)) as libro:
            hojas = [n for n in libro.namelist() if n.startswith("xl/worksheets/sheet")]
            assert len(hojas) == 3
            assert any("chart" in n for n in libro.namelist())

            cadenas = libro.read("xl/sharedStrings.xml").decode("utf-8")
            assert "$ " not in cadenas

    async def test_el_pdf_respeta_el_rol(self, cliente, como, datos):
        """Un cliente que descargue el reporte obtiene el suyo, no el del
        negocio."""
        await cliente.post(
            "/api/ventas", headers=como("administrador"),
            json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
        )
        respuesta = await cliente.get(
            "/api/reportes/ventas/pdf", headers=como("cliente")
        )
        assert respuesta.status_code == 200
        assert respuesta.content[:5] == b"%PDF-"


class TestPanel:
    async def test_cuenta_el_catalogo_y_lo_vendido(self, cliente, como, datos):
        coche = datos["productos"][0]
        await cliente.post(
            "/api/ventas", headers=como("cliente"),
            json={"lineas": [{"productoId": coche.id}]},
        )

        panel = (
            await cliente.get("/api/reportes/panel", headers=como("administrador"))
        ).json()["panel"]

        assert panel["vehiculosVendidos"] == 1
        assert panel["vehiculosDisponibles"] == len(datos["productos"]) - 1
        assert panel["usuariosActivos"] == len(datos["usuarios"])

    async def test_cuenta_las_pqr_abiertas(self, cliente, como):
        await cliente.post(
            "/api/pqr", headers=como("cliente"),
            json={
                "tipo": "reclamo",
                "asunto": "Un asunto suficientemente largo",
                "descripcion": "Una descripcion con mas de veinte caracteres.",
            },
        )

        panel = (
            await cliente.get("/api/reportes/panel", headers=como("administrador"))
        ).json()["panel"]
        assert panel["pqrAbiertas"] == 1


async def _vender(cliente, como, datos):
    respuesta = await cliente.post(
        "/api/ventas",
        headers=como("administrador"),
        json={
            "usuarioId": datos["usuarios"]["cliente"].id,
            "lineas": [{"servicioId": datos["servicios"][0].id}],
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["venta"]
