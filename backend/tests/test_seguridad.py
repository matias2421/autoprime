# -*- coding: utf-8 -*-
"""Quién puede hacer qué.

Estas son las pruebas que más importa que existan. Un error de cálculo en un
reporte se ve y se corrige; un endpoint que deja a un cliente leer las ventas
de todo el negocio no se ve nunca, porque la interfaz no le enseña el botón.
El botón no es la defensa: la defensa está aquí.
"""

import pytest


class TestAutenticacion:
    async def test_sin_token_responde_401(self, cliente):
        respuesta = await cliente.get("/api/ventas")
        assert respuesta.status_code == 401
        assert respuesta.json()["codigo"] == "no_autenticado"

    async def test_el_401_dice_como_autenticarse(self, cliente):
        """La norma HTTP exige indicar el esquema; sin eso un cliente
        genérico no sabe que debe pedir un token en vez de rendirse."""
        respuesta = await cliente.get("/api/ventas")
        assert respuesta.headers.get("www-authenticate") == "Bearer"

    async def test_token_invalido_responde_401(self, cliente):
        respuesta = await cliente.get(
            "/api/ventas", headers={"Authorization": "Bearer basura"}
        )
        assert respuesta.status_code == 401

    async def test_el_token_de_recuperacion_no_sirve_para_entrar(
        self, cliente, datos
    ):
        """Lleva la misma firma y el mismo usuario, así que sin comprobar el
        tipo serviría para iniciar sesión en vez de solo para cambiar la
        contraseña: un enlace de correo se convertiría en una llave."""
        from app.core.seguridad import crear_token_recuperacion

        usuario = datos["usuarios"]["cliente"]
        token = crear_token_recuperacion(usuario.id, usuario.password_hash)

        respuesta = await cliente.get(
            "/api/auth/perfil", headers={"Authorization": f"Bearer {token}"}
        )
        assert respuesta.status_code == 401


class TestRoles:
    @pytest.mark.parametrize(
        "ruta",
        ["/api/reportes/panel", "/api/usuarios/clientes"],
    )
    async def test_un_cliente_no_entra_a_lo_del_personal(self, cliente, como, ruta):
        respuesta = await cliente.get(ruta, headers=como("cliente"))
        assert respuesta.status_code == 403
        assert respuesta.json()["codigo"] == "permiso_denegado"

    async def test_un_empleado_no_borra_ventas(self, cliente, como, datos):
        venta = await _crear_venta(cliente, como, datos)
        respuesta = await cliente.delete(
            f"/api/ventas/{venta['id']}", headers=como("empleado")
        )
        assert respuesta.status_code == 403

    async def test_el_admin_si(self, cliente, como, datos):
        venta = await _crear_venta(cliente, como, datos)
        respuesta = await cliente.delete(
            f"/api/ventas/{venta['id']}", headers=como("administrador")
        )
        assert respuesta.status_code == 204
        assert respuesta.content == b""

    async def test_un_empleado_no_lista_usuarios(self, cliente, como):
        """El listado completo es del administrador. Un empleado tiene su
        propio endpoint con menos datos."""
        respuesta = await cliente.get("/api/usuarios", headers=como("empleado"))
        assert respuesta.status_code == 403


class TestAislamientoEntreCuentas:
    async def test_un_cliente_solo_ve_sus_ventas(self, cliente, como, datos):
        """El personal registra una venta a su propio nombre; el cliente no
        debe verla en su listado."""
        await _crear_venta(cliente, como, datos, comprador=None)

        respuesta = await cliente.get("/api/ventas", headers=como("cliente"))
        assert respuesta.status_code == 200
        assert respuesta.json()["total"] == 0

    async def test_un_cliente_no_abre_la_venta_de_otro(self, cliente, como, datos):
        venta = await _crear_venta(cliente, como, datos, comprador=None)
        respuesta = await cliente.get(
            f"/api/ventas/{venta['id']}", headers=como("cliente")
        )
        assert respuesta.status_code == 403

    async def test_un_cliente_no_radica_a_nombre_de_otro(self, cliente, como, datos):
        """El comprador sale del token. Aceptarlo del cuerpo dejaría comprar
        a nombre de cualquiera."""
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={
                "usuarioId": datos["usuarios"]["administrador"].id,
                "lineas": [{"servicioId": datos["servicios"][0].id}],
            },
        )
        assert respuesta.status_code == 403

    async def test_un_cliente_no_lee_la_pqr_de_otro(self, cliente, como):
        """En un canal de quejas, el contenido ajeno es el dato más delicado
        que hay."""
        creada = await cliente.post(
            "/api/pqr",
            headers=como("empleado"),
            json={
                "tipo": "queja",
                "asunto": "Un asunto suficientemente largo",
                "descripcion": "Una descripcion con mas de veinte caracteres.",
            },
        )
        assert creada.status_code == 201

        respuesta = await cliente.get(
            f"/api/pqr/{creada.json()['pqr']['id']}", headers=como("cliente")
        )
        assert respuesta.status_code == 403


class TestPrecios:
    async def test_el_precio_lo_pone_el_catalogo_no_el_cliente(
        self, cliente, como, datos
    ):
        """Si el importe viniera del cuerpo, cualquiera con Postman se
        compraría un Phantom por mil pesos."""
        coche = datos["productos"][0]
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"productoId": coche.id, "precioUnitario": 1000}]},
        )
        assert respuesta.status_code == 201

        linea = respuesta.json()["venta"]["lineas"][0]
        assert linea["precioUnitario"] == coche.precio

    async def test_el_personal_si_puede_fijarlo(self, cliente, como, datos):
        """Es una operación de mostrador: hay piezas sin precio de lista y
        ventas negociadas."""
        pieza = datos["productos"][1]
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("administrador"),
            json={"lineas": [{"productoId": pieza.id, "precioUnitario": 9_000_000_000}]},
        )
        assert respuesta.status_code == 201
        assert respuesta.json()["venta"]["lineas"][0]["precioUnitario"] == 9_000_000_000

    async def test_una_pieza_bajo_consulta_no_se_compra_sola(
        self, cliente, como, datos
    ):
        pieza = datos["productos"][1]
        respuesta = await cliente.post(
            "/api/ventas",
            headers=como("cliente"),
            json={"lineas": [{"productoId": pieza.id}]},
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "precio_bajo_consulta"


async def _crear_venta(cliente, como, datos, comprador="cliente"):
    """Ayuda: registra una venta de un servicio y devuelve su cuerpo."""
    cuerpo = {"lineas": [{"servicioId": datos["servicios"][0].id}]}
    if comprador:
        cuerpo["usuarioId"] = datos["usuarios"][comprador].id

    respuesta = await cliente.post(
        "/api/ventas", headers=como("administrador"), json=cuerpo
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["venta"]


class TestElConflictoDiceQueCampo:
    """Un 409 tiene que decir CUÁL de los datos choca.

    Esto existe por un fallo que se vio en el formulario de registro: el
    servidor contestaba «ya existe una cuenta con ese correo» sin decir que
    el problema era el correo, así que el formulario no tenía forma de saber
    qué casilla marcar y las dejaba todas en verde junto al aviso. Quien lo
    rellenaba veía un error y ni un solo campo señalado.

    El nombre va como lo usa el cliente (`numeroDocumento`), igual que los
    detalles de validación: si no coincide, el formulario no lo encuentra y
    es como si no se hubiera enviado.
    """

    async def _registro(self, cliente, **cambios):
        cuerpo = {
            "nombre": "Prueba", "apellido": "Conflicto",
            "tipoDocumento": "CC", "numeroDocumento": "1088777666",
            "direccion": "Calle 1 # 2-3", "telefono": "3001112233",
            "correo": "prueba.conflicto@example.com", "password": "Prueba2026!",
        }
        cuerpo.update(cambios)
        return await cliente.post("/api/auth/registro", json=cuerpo)

    async def test_el_correo_duplicado_senala_el_correo(self, cliente, datos):
        existente = datos["usuarios"]["cliente"].correo

        respuesta = await self._registro(cliente, correo=existente)

        assert respuesta.status_code == 409
        cuerpo = respuesta.json()
        assert cuerpo["codigo"] == "correo_ya_registrado"
        assert cuerpo["detalles"] == [
            {"campo": "correo", "problema": cuerpo["mensaje"]}
        ]

    async def test_el_documento_duplicado_senala_el_documento(self, cliente, datos):
        usuario = datos["usuarios"]["cliente"]

        respuesta = await self._registro(
            cliente,
            correo="otro.correo.libre@example.com",
            tipoDocumento=usuario.tipo_documento,
            numeroDocumento=usuario.numero_documento,
        )

        assert respuesta.status_code == 409
        cuerpo = respuesta.json()
        assert cuerpo["codigo"] == "documento_ya_registrado"
        # En camelCase, que es como lo nombra el formulario.
        assert cuerpo["detalles"][0]["campo"] == "numeroDocumento"

    def test_un_conflicto_sin_campo_no_inventa_ninguno(self):
        """No todos los choques se pueden atribuir a una casilla —una franja
        de cita ya tomada, por ejemplo—. Cuando no se puede, `detalles` va
        vacío: señalar un campo al azar sería peor que no señalar ninguno."""
        from app.errores import ConflictoDeNegocio, FranjaOcupada

        assert ConflictoDeNegocio.campo is None
        assert FranjaOcupada.campo is None
