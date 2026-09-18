# -*- coding: utf-8 -*-
"""Ventas y facturación: las reglas del dominio, no solo los códigos HTTP."""

from decimal import Decimal

import pytest


class TestRegistro:
    async def test_el_total_lleva_el_iva(self, cliente, como, datos):
        coche = datos["productos"][0]
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"productoId": coche.id}]},
        )
        venta = respuesta.json()["venta"]

        assert venta["subtotal"] == coche.precio
        assert venta["impuestos"] == float(Decimal(coche.precio) * Decimal("0.19"))
        assert venta["total"] == venta["subtotal"] + venta["impuestos"]

    async def test_el_consecutivo_tiene_forma(self, cliente, como, datos):
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
        )
        numero = respuesta.json()["venta"]["numero"]
        assert numero.startswith("V-")
        assert len(numero) == len("V-2026-00001")

    async def test_dos_ventas_seguidas_no_repiten_numero(
        self, cliente, como, datos
    ):
        """El consecutivo sale del id que asigna la base. Si saliera de un
        `MAX(numero)` leído antes de insertar, dos ventas pedirían el mismo."""
        numeros = set()
        for _ in range(3):
            respuesta = await cliente.post(
                "/api/ventas",
                headers=como("cliente"),
                json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
            )
            numeros.add(respuesta.json()["venta"]["numero"])
        assert len(numeros) == 3

    async def test_el_numero_provisional_no_se_escapa(self, cliente, como, datos):
        """Entre el INSERT y el COMMIT la fila lleva un número temporal. No
        puede llegar a verlo nadie."""
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
        )
        assert not respuesta.json()["venta"]["numero"].startswith("tmp-")

    async def test_la_cantidad_multiplica(self, cliente, como, datos):
        servicio = datos["servicios"][0]
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"servicioId": servicio.id, "cantidad": 3}]},
        )
        assert respuesta.json()["venta"]["lineas"][0]["subtotal"] == servicio.precio * 3

    async def test_una_venta_de_web_no_tiene_vendedor(self, cliente, como, datos):
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
        )
        assert respuesta.json()["venta"]["vendedorId"] is None

    async def test_una_de_mostrador_si(self, cliente, como, datos):
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("empleado"),
            json={
                "usuarioId": datos["usuarios"]["cliente"].id,
                "lineas": [{"servicioId": datos["servicios"][0].id}],
            },
        )
        venta = respuesta.json()["venta"]
        assert venta["usuarioId"] == datos["usuarios"]["cliente"].id
        assert venta["vendedorId"] == datos["usuarios"]["empleado"].id


class TestValidaciones:
    @pytest.mark.parametrize(
        "cuerpo, motivo",
        [
            ({"lineas": []}, "una venta sin lineas no es una venta"),
            ({"lineas": [{}]}, "una linea sin producto ni servicio"),
            ({"lineas": [{"productoId": 1, "servicioId": 1}]}, "las dos cosas a la vez"),
            ({"lineas": [{"servicioId": 1, "cantidad": 0}]}, "cantidad cero"),
        ],
    )
    async def test_cuerpos_invalidos(self, cliente, como, cuerpo, motivo):
        respuesta = await cliente.post("/api/ventas", headers=como("cliente"), json=cuerpo)
        assert respuesta.status_code == 422, motivo

    async def test_el_422_dice_que_campo(self, cliente, como):
        """El formulario necesita saber qué input marcar, no solo que algo
        estaba mal."""
        respuesta = await cliente.post(
            "/api/ventas", headers=como("cliente"), json={"lineas": []}
        )
        detalles = respuesta.json()["detalles"]
        assert detalles and all("campo" in d and "problema" in d for d in detalles)

    async def test_vehiculo_inexistente_es_404(self, cliente, como):
        respuesta = await cliente.post(
            "/api/ventas", headers=como("administrador"),
            json={"lineas": [{"productoId": 99999}]},
        )
        assert respuesta.status_code == 404


class TestCatalogo:
    async def test_vender_saca_el_coche_del_catalogo(self, cliente, como, datos):
        """Mientras se cobra, el coche está reservado: no puede vendérsele a
        otra persona."""
        coche = datos["productos"][0]
        await cliente.post(
            "/api/ventas", headers=como("cliente"),
            json={"lineas": [{"productoId": coche.id}]},
        )

        ficha = await cliente.get(f"/api/productos/{coche.id}")
        assert ficha.json()["producto"]["estado"] == "vendido"

    async def test_no_se_vende_dos_veces(self, cliente, como, datos):
        coche = datos["productos"][0]
        cuerpo = {"lineas": [{"productoId": coche.id}]}
        await cliente.post("/api/ventas", headers=como("cliente"), json=cuerpo)

        segunda = await cliente.post(
            "/api/ventas", headers=como("administrador"), json=cuerpo
        )
        assert segunda.status_code == 409
        assert segunda.json()["codigo"] == "vehiculo_no_disponible"

    async def test_anular_lo_devuelve(self, cliente, como, datos):
        coche = datos["productos"][0]
        venta = (
            await cliente.post(
                "/api/ventas", headers=como("cliente"),
                json={"lineas": [{"productoId": coche.id}]},
            )
        ).json()["venta"]

        await cliente.patch(
            f"/api/ventas/{venta['id']}/estado",
            headers=como("administrador"),
            json={"estado": "anulada"},
        )

        ficha = await cliente.get(f"/api/productos/{coche.id}")
        assert ficha.json()["producto"]["estado"] == "disponible"


class TestFacturacion:
    async def test_una_venta_una_factura(self, cliente, como, datos):
        venta = await _venta(cliente, como, datos)
        primera = await cliente.post(
            f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
        )
        assert primera.status_code == 201

        segunda = await cliente.post(
            f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
        )
        assert segunda.status_code == 409
        assert segunda.json()["codigo"] == "venta_ya_facturada"

    async def test_la_factura_copia_el_detalle(self, cliente, como, datos):
        """Copiarlo, y no apuntar a la venta, es lo que permite corregir una
        cosa sin falsear la otra."""
        venta = await _venta(cliente, como, datos)
        factura = (
            await cliente.post(
                f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
            )
        ).json()["factura"]

        assert len(factura["lineas"]) == len(venta["lineas"])
        assert factura["total"] == venta["total"]
        assert factura["clienteCorreo"] == "cliente@autoprime.com.co"

    async def test_no_se_factura_una_venta_anulada(self, cliente, como, datos):
        venta = await _venta(cliente, como, datos)
        await cliente.patch(
            f"/api/ventas/{venta['id']}/estado",
            headers=como("administrador"),
            json={"estado": "anulada"},
        )

        respuesta = await cliente.post(
            f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "venta_no_facturable"

    async def test_una_venta_facturada_no_se_borra(self, cliente, como, datos):
        """La factura consumió un número del consecutivo. Un consecutivo con
        huecos no sirve para lo único que hace falta."""
        venta = await _venta(cliente, como, datos)
        await cliente.post(
            f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
        )

        respuesta = await cliente.delete(
            f"/api/ventas/{venta['id']}", headers=como("administrador")
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "venta_con_factura"

    async def test_el_pdf_es_un_pdf(self, cliente, como, datos):
        venta = await _venta(cliente, como, datos)
        factura = (
            await cliente.post(
                f"/api/facturas/venta/{venta['id']}", headers=como("administrador")
            )
        ).json()["factura"]

        respuesta = await cliente.get(
            f"/api/facturas/{factura['id']}/pdf", headers=como("cliente")
        )
        assert respuesta.status_code == 200
        assert respuesta.content[:5] == b"%PDF-"
        assert factura["numero"] in respuesta.headers["content-disposition"]


class TestPaginacion:
    async def test_el_total_no_es_el_de_la_pagina(self, cliente, como, datos):
        """Contar `len()` de lo devuelto haría que la última página dijera
        que el total es tres."""
        for _ in range(5):
            await cliente.post(
                "/api/ventas", headers=como("cliente"),
                json={"lineas": [{"servicioId": datos["servicios"][0].id}]},
            )

        respuesta = await cliente.get(
            "/api/ventas?porPagina=2", headers=como("administrador")
        )
        cuerpo = respuesta.json()
        assert len(cuerpo["ventas"]) == 2
        assert cuerpo["total"] == 5
        assert cuerpo["pagina"]["paginas"] == 3

    async def test_hay_tope(self, cliente, como):
        """Sin tope, `?porPagina=999999` deja el problema donde estaba."""
        respuesta = await cliente.get(
            "/api/ventas?porPagina=5000", headers=como("administrador")
        )
        assert respuesta.status_code == 422


async def _venta(cliente, como, datos):
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
