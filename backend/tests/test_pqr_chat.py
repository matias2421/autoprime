# -*- coding: utf-8 -*-
"""PQR y el asistente.

El chat se prueba con el proveedor sustituido. Llamar a Groq de verdad en
cada corrida ataría las pruebas a que haya red, a que la cuota alcance y a
que el modelo conteste lo mismo dos veces —que es justo lo que un modelo no
garantiza—. Lo que sí se comprueba aquí es lo nuestro: que la ficha que se le
manda lleve los datos reales, que la pregunta se guarde aunque el proveedor
falle, y que el freno y los permisos hagan su trabajo.
"""

import httpx
import pytest

from app.core import asistente, limitador


@pytest.fixture(autouse=True)
def freno_limpio():
    """El limitador vive en memoria del proceso; sin esto, una prueba que lo
    agota deja frenada a la siguiente."""
    limitador.reiniciar()
    yield
    limitador.reiniciar()


class TestPqr:
    async def test_radicar_asigna_numero_y_estado(self, cliente, como):
        respuesta = await cliente.post(
            "/api/pqr",
            headers=como("cliente"),
            json={
                "tipo": "reclamo",
                "asunto": "El vehiculo llego con un rayon",
                "descripcion": "Recibi el vehiculo ayer y tiene un rayon que no "
                               "estaba en las fotos de la entrega.",
            },
        )
        assert respuesta.status_code == 201

        registro = respuesta.json()["pqr"]
        assert registro["numero"].startswith("P-")
        assert registro["estado"] == "pendiente"
        assert registro["respuesta"] is None

    @pytest.mark.parametrize(
        "cuerpo",
        [
            {"tipo": "queja", "asunto": "corto", "descripcion": "muy corta"},
            {"tipo": "felicitacion", "asunto": "Un asunto valido",
             "descripcion": "Una descripcion suficientemente larga para pasar."},
        ],
    )
    async def test_cuerpos_invalidos(self, cliente, como, cuerpo):
        respuesta = await cliente.post("/api/pqr", headers=como("cliente"), json=cuerpo)
        assert respuesta.status_code == 422

    async def test_quien_radica_sale_del_token(self, cliente, como, datos):
        """El estado y el número los pone el sistema; si el estado viniera del
        cuerpo, se podría radicar una queja ya marcada como respondida."""
        respuesta = await cliente.post(
            "/api/pqr",
            headers=como("cliente"),
            json={
                "tipo": "peticion",
                "asunto": "Un asunto suficientemente largo",
                "descripcion": "Una descripcion con mas de veinte caracteres.",
                "estado": "cerrada",
            },
        )
        registro = respuesta.json()["pqr"]
        assert registro["usuarioId"] == datos["usuarios"]["cliente"].id
        assert registro["estado"] == "pendiente"

    async def test_responder_deja_firma(self, cliente, como, datos):
        registro = await _radicar(cliente, como)
        respuesta = await cliente.patch(
            f"/api/pqr/{registro['id']}/responder",
            headers=como("administrador"),
            json={"respuesta": "Programamos el retoque sin costo en el taller."},
        )
        assert respuesta.status_code == 200

        actualizada = respuesta.json()["pqr"]
        assert actualizada["estado"] == "respondida"
        assert actualizada["responsable"] is not None

    async def test_una_cerrada_ya_no_se_responde(self, cliente, como):
        registro = await _radicar(cliente, como)
        await cliente.patch(
            f"/api/pqr/{registro['id']}/estado",
            headers=como("administrador"), json={"estado": "cerrada"},
        )

        respuesta = await cliente.patch(
            f"/api/pqr/{registro['id']}/responder",
            headers=como("administrador"),
            json={"respuesta": "Una respuesta que ya no deberia entrar."},
        )
        assert respuesta.status_code == 409
        assert respuesta.json()["codigo"] == "pqr_no_modificable"

    async def test_la_bandeja_pone_lo_pendiente_primero(self, cliente, como):
        """Ordenada solo por fecha, un reclamo sin atender acaba enterrado
        bajo veinte casos cerrados."""
        vieja = await _radicar(cliente, como, asunto="La primera que se radico")
        await _radicar(cliente, como, asunto="La segunda, mas reciente")

        await cliente.patch(
            f"/api/pqr/{vieja['id']}/estado",
            headers=como("administrador"), json={"estado": "cerrada"},
        )

        listado = (
            await cliente.get("/api/pqr", headers=como("administrador"))
        ).json()["pqr"]

        assert listado[0]["estado"] == "pendiente"
        assert listado[-1]["estado"] == "cerrada"


class TestFichaDelAsistente:
    """Lo que se le pone delante al modelo.

    Es la defensa entera contra que se invente datos: no se le pide que no
    mienta, se le quitan los huecos.
    """

    def test_la_ficha_lleva_los_precios_reales(self, datos):
        ficha = asistente.construir_ficha(datos["productos"], datos["servicios"])

        assert "3.200.000.000" in ficha
        assert "Phantom VIII" in ficha
        assert "Peritaje de 120 puntos" in ficha

    def test_marca_lo_que_va_bajo_consulta(self, datos):
        ficha = asistente.construir_ficha(datos["productos"], datos["servicios"])
        assert "precio bajo consulta" in ficha

    def test_lleva_el_contacto_de_verdad(self, datos):
        """El modelo se inventó un teléfono cuando no se lo dieron."""
        ficha = asistente.construir_ficha(datos["productos"], datos["servicios"])
        assert "+57 604 444 5566" in ficha
        assert "contacto@autoprime.com.co" in ficha

    def test_las_instrucciones_prohiben_inventar(self):
        instrucciones = asistente.INSTRUCCIONES.lower()
        assert "no lo inventes" in instrucciones or "inventes" in instrucciones
        assert "pqr" in instrucciones


class TestChat:
    async def test_el_estado_es_publico(self, cliente):
        respuesta = await cliente.get("/api/chat/estado")
        assert respuesta.status_code == 200
        assert "disponible" in respuesta.json()

    async def test_un_visitante_abre_conversacion(self, cliente):
        respuesta = await cliente.post("/api/chat/conversaciones", json={})
        assert respuesta.status_code == 201
        assert respuesta.json()["conversacion"]["usuarioId"] is None

    async def test_una_conversacion_anonima_no_se_relee(self, cliente):
        """Los identificadores son consecutivos: un GET con un número al azar
        leería la conversación de otra persona."""
        creada = await cliente.post("/api/chat/conversaciones", json={})
        hilo = creada.json()["conversacion"]["id"]

        respuesta = await cliente.get(f"/api/chat/conversaciones/{hilo}")
        assert respuesta.status_code == 403

    async def test_con_sesion_queda_asociada(self, cliente, como, datos):
        creada = await cliente.post(
            "/api/chat/conversaciones", headers=como("cliente"), json={}
        )
        assert creada.json()["conversacion"]["usuarioId"] == datos["usuarios"]["cliente"].id

    async def test_nadie_mas_escribe_en_un_hilo_ajeno(self, cliente, como):
        creada = await cliente.post(
            "/api/chat/conversaciones", headers=como("cliente"), json={}
        )
        hilo = creada.json()["conversacion"]["id"]

        respuesta = await cliente.post(
            f"/api/chat/conversaciones/{hilo}/mensajes",
            headers=como("administrador"),
            json={"contenido": "Hola"},
        )
        assert respuesta.status_code == 403

    async def test_responde_y_guarda_el_par(self, cliente, monkeypatch):
        async def respuesta_falsa(ficha, historial):
            # De paso se comprueba que al modelo le llega la ficha, no solo
            # la pregunta suelta.
            assert "Phantom VIII" in ficha
            assert historial[-1]["content"] == "Cuanto cuesta el Phantom?"
            return "El MANSORY Phantom VIII cuesta $3.200.000.000 COP."

        monkeypatch.setattr(asistente, "responder", respuesta_falsa)

        creada = await cliente.post("/api/chat/conversaciones", json={})
        hilo = creada.json()["conversacion"]["id"]

        respuesta = await cliente.post(
            f"/api/chat/conversaciones/{hilo}/mensajes",
            json={"contenido": "Cuanto cuesta el Phantom?"},
        )
        assert respuesta.status_code == 200

        chat = respuesta.json()["chat"]
        assert chat["pregunta"]["rol"] == "usuario"
        assert chat["respuesta"]["rol"] == "asistente"
        assert "3.200.000.000" in chat["respuesta"]["contenido"]

    async def test_si_el_proveedor_cae_la_pregunta_no_se_pierde(
        self, cliente, como, monkeypatch
    ):
        """Se guarda antes de llamar al proveedor: se puede reintentar sin
        volver a escribirla."""
        from app.errores import ServicioExternoCaido

        async def se_cae(ficha, historial):
            raise ServicioExternoCaido("asistente", "prueba")

        monkeypatch.setattr(asistente, "responder", se_cae)

        creada = await cliente.post(
            "/api/chat/conversaciones", headers=como("cliente"), json={}
        )
        hilo = creada.json()["conversacion"]["id"]

        respuesta = await cliente.post(
            f"/api/chat/conversaciones/{hilo}/mensajes",
            headers=como("cliente"),
            json={"contenido": "Una pregunta que no llega a contestarse"},
        )
        assert respuesta.status_code == 503
        assert respuesta.json()["codigo"] == "servicio_externo_caido"

        leida = await cliente.get(
            f"/api/chat/conversaciones/{hilo}", headers=como("cliente")
        )
        mensajes = leida.json()["conversacion"]["mensajes"]
        assert len(mensajes) == 1
        assert mensajes[0]["rol"] == "usuario"

    @pytest.mark.parametrize("contenido", ["", "x" * 2000])
    async def test_mensajes_fuera_de_medida(self, cliente, contenido):
        creada = await cliente.post("/api/chat/conversaciones", json={})
        hilo = creada.json()["conversacion"]["id"]

        respuesta = await cliente.post(
            f"/api/chat/conversaciones/{hilo}/mensajes", json={"contenido": contenido}
        )
        assert respuesta.status_code == 422

    async def test_el_freno_corta_el_bucle(self, cliente):
        """El chat es el único endpoint público que cuesta dinero por uso."""
        codigos = []
        for _ in range(10):
            respuesta = await cliente.post("/api/chat/conversaciones", json={})
            codigos.append(respuesta.status_code)
            if respuesta.status_code == 429:
                assert "retry-after" in respuesta.headers
                assert respuesta.json()["codigo"] == "demasiadas_peticiones"
                break

        assert 429 in codigos


class TestProveedor:
    """El trato con Groq, sin llamar a Groq."""

    async def test_un_429_del_proveedor_no_sale_como_500(self, monkeypatch):
        from app.errores import ServicioExternoCaido

        class RespuestaFalsa:
            status_code = 429
            text = "rate limited"

        async def post_falso(self, *args, **kwargs):
            return RespuestaFalsa()

        monkeypatch.setattr(httpx.AsyncClient, "post", post_falso)
        monkeypatch.setattr(
            asistente.configuracion, "groq_api_key", "gsk_de_prueba", raising=False
        )

        with pytest.raises(ServicioExternoCaido) as fallo:
            await asistente.responder("ficha", [{"role": "user", "content": "hola"}])
        assert "cuota" in str(fallo.value)

    async def test_sin_clave_no_se_llama_a_nadie(self, monkeypatch):
        from app.errores import ServicioExternoCaido

        monkeypatch.setattr(
            asistente.configuracion, "groq_api_key", "", raising=False
        )
        with pytest.raises(ServicioExternoCaido):
            await asistente.responder("ficha", [{"role": "user", "content": "hola"}])


async def _radicar(cliente, como, asunto="Un asunto suficientemente largo"):
    respuesta = await cliente.post(
        "/api/pqr",
        headers=como("cliente"),
        json={
            "tipo": "reclamo",
            "asunto": asunto,
            "descripcion": "Una descripcion con mas de veinte caracteres.",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["pqr"]
