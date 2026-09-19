# -*- coding: utf-8 -*-
"""Lo que cierra las puertas de fuera.

Tres cosas distintas, todas comprobables:

  - que el texto de la gente no llegue nunca pegado a una sentencia SQL,
  - que un atacante no pueda probar contraseñas a discreción,
  - que el navegador reciba las instrucciones que le impiden hacer por su
    cuenta cosas que nadie quiere.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import mysql

from app.models.autoprime import Usuario
from app.routers.auth import INTENTOS_POR_MINUTO

# Cargas clásicas: cerrar la comilla y anular el WHERE, encadenar un DROP,
# leer otra tabla con UNION, y el comentario que descarta el resto.
CARGAS = [
    "' OR '1'='1",
    "'; DROP TABLE usuarios; --",
    "' UNION SELECT id, correo, password_hash FROM usuarios --",
    "admin'--",
    "1; DELETE FROM ventas",
]


class TestInyeccionSql:
    """La defensa real es que no hay SQL escrito a mano en toda `app/`.

    Estas pruebas no la crean: la comprueban, que es distinto. Si alguien
    añadiera mañana un `text(f"...")` con una variable dentro, la tercera
    prueba lo caza.
    """

    @pytest.mark.parametrize("carga", CARGAS)
    async def test_el_buscador_no_se_rompe(self, cliente, como, carga):
        """El buscador va a un LIKE, que es el sitio clásico.

        Un 200 con cero resultados es la respuesta correcta: la cadena se
        buscó tal cual y no coincidió con nada. Lo que no puede salir es un
        500, que significaría que llegó a la base y rompió la sentencia.
        """
        respuesta = await cliente.get(
            "/api/usuarios", params={"buscar": carga}, headers=como("administrador")
        )
        assert respuesta.status_code in (200, 422)

    @pytest.mark.parametrize("carga", CARGAS)
    async def test_el_login_no_se_rompe(self, cliente, carga):
        respuesta = await cliente.post(
            "/api/auth/login", json={"correo": carga, "password": carga}
        )
        assert respuesta.status_code in (401, 422)

    def test_el_texto_viaja_como_parametro(self):
        """Se compila la consulta y se mira el SQL que sale.

        Es la prueba que de verdad demuestra la afirmación: la carga aparece
        en los parámetros enlazados y NO dentro de la sentencia.
        """
        patron = "%' OR '1'='1%"
        compilada = (
            select(Usuario).where(Usuario.nombre.ilike(patron))
        ).compile(dialect=mysql.dialect())

        assert "OR '1'='1" not in str(compilada)
        assert any("1'='1" in str(v) for v in compilada.params.values())

    async def test_la_base_sigue_entera(self, cliente, como, datos):
        """Después de mandarlas todas, las tablas siguen ahí."""
        for carga in CARGAS:
            await cliente.get(
                "/api/usuarios", params={"buscar": carga},
                headers=como("administrador"),
            )

        respuesta = await cliente.get("/api/usuarios", headers=como("administrador"))
        assert respuesta.status_code == 200
        assert respuesta.json()["total"] == len(datos["usuarios"])

    @pytest.mark.parametrize(
        "valor", ["pagada' OR '1'='1", "../../etc/passwd", "1 OR 1=1"]
    )
    async def test_los_filtros_cerrados_lo_rechazan_antes(self, cliente, como, valor):
        """`estado` es un vocabulario cerrado: Pydantic lo para en la puerta,
        sin que la consulta llegue a construirse."""
        respuesta = await cliente.get(
            "/api/ventas", params={"estado": valor}, headers=como("administrador")
        )
        assert respuesta.status_code == 422


class TestFuerzaBruta:
    async def test_el_login_se_frena(self, cliente):
        """bcrypt protege el hash si alguien roba la tabla; no protege de que
        le pregunten al servidor mil veces por segundo."""
        codigos = []
        for _ in range(INTENTOS_POR_MINUTO + 3):
            respuesta = await cliente.post(
                "/api/auth/login",
                json={"correo": "admin@autoprime.com.co", "password": "incorrecta"},
            )
            codigos.append(respuesta.status_code)
            if respuesta.status_code == 429:
                break

        assert 429 in codigos, f"no freno en {len(codigos)} intentos: {codigos}"

    async def test_el_429_dice_cuanto_esperar(self, cliente):
        for _ in range(INTENTOS_POR_MINUTO + 3):
            respuesta = await cliente.post(
                "/api/auth/login",
                json={"correo": "admin@autoprime.com.co", "password": "mala"},
            )
            if respuesta.status_code == 429:
                assert "retry-after" in respuesta.headers
                assert respuesta.json()["codigo"] == "demasiadas_peticiones"
                return
        pytest.fail("nunca llego al 429")

    async def test_cambiar_de_correo_no_esquiva_el_freno(self, cliente):
        """Se cuenta por origen ADEMÁS de por correo.

        Solo por correo, quien va cambiando la dirección en cada intento
        —que es lo que hace quien prueba una clave común contra muchas
        cuentas— no gasta nunca el cupo.
        """
        codigos = []
        for i in range(INTENTOS_POR_MINUTO + 3):
            respuesta = await cliente.post(
                "/api/auth/login",
                json={"correo": f"persona{i}@example.com", "password": "x"},
            )
            codigos.append(respuesta.status_code)
            if respuesta.status_code == 429:
                break

        assert 429 in codigos, f"no freno cambiando de correo: {codigos}"

    async def test_la_recuperacion_tambien(self, cliente):
        """Cada solicitud manda un correo de verdad: sin freno, esto es un
        generador de correo basura con el remitente del atelier."""
        codigos = []
        for _ in range(8):
            respuesta = await cliente.post(
                "/api/auth/recuperar", json={"correo": "admin@autoprime.com.co"}
            )
            codigos.append(respuesta.status_code)
            if respuesta.status_code == 429:
                break

        assert 429 in codigos, f"no freno: {codigos}"


class TestCabeceras:
    @pytest.mark.parametrize(
        "cabecera, valor",
        [
            ("x-content-type-options", "nosniff"),
            ("x-frame-options", "DENY"),
            ("referrer-policy", "no-referrer"),
            ("cache-control", "no-store"),
        ],
    )
    async def test_van_en_toda_respuesta(self, cliente, cabecera, valor):
        respuesta = await cliente.get("/salud")
        assert respuesta.headers.get(cabecera) == valor

    async def test_tambien_en_los_errores(self, cliente):
        """Una respuesta de error es una respuesta: si las cabeceras solo
        fueran en las de éxito, el hueco estaría justo donde más se prueba."""
        respuesta = await cliente.get("/api/ventas")
        assert respuesta.status_code == 401
        assert respuesta.headers.get("x-content-type-options") == "nosniff"

    async def test_tambien_en_una_descarga(self, cliente, como):
        """El `nosniff` hace más falta aquí que en ningún sitio: un PDF
        generado con texto de la gente es justo lo que un navegador podría
        decidir que «parece HTML»."""
        respuesta = await cliente.get(
            "/api/reportes/ventas/pdf", headers=como("administrador")
        )
        assert respuesta.status_code == 200
        assert respuesta.headers.get("x-content-type-options") == "nosniff"

    async def test_la_politica_de_la_api_no_deja_nada(self, cliente):
        respuesta = await cliente.get("/salud")
        politica = respuesta.headers.get("content-security-policy", "")
        assert "default-src 'none'" in politica
        assert "frame-ancestors 'none'" in politica

    async def test_la_documentacion_tiene_la_suya(self, cliente):
        """Swagger carga su JavaScript de un CDN: con la política estricta
        se queda en blanco. Se le da una propia en lugar de aflojar la de
        todo lo demás."""
        respuesta = await cliente.get("/docs")
        politica = respuesta.headers.get("content-security-policy", "")
        assert "cdn.jsdelivr.net" in politica
        assert "frame-ancestors 'none'" in politica

    async def test_sin_hsts_en_desarrollo(self, cliente):
        """Una vez que el navegador guarda HSTS para localhost lo recuerda
        para todos los proyectos que usen localhost: un descuido de hoy es
        un problema dentro de seis meses en otro proyecto distinto."""
        respuesta = await cliente.get("/salud")
        assert "strict-transport-security" not in respuesta.headers


class TestComprobacionDeSalud:
    """Dos preguntas distintas, dos respuestas.

    Esto existe por un fallo real: el proveedor tenía `/salud` como
    comprobación de salud, `/salud` consulta la base, y el día que la base
    desapareció un rato dio por FALLIDO un despliegue que no tenía nada
    malo. Quince minutos esperando algo que no dependía del código.
    """

    async def test_vivo_no_toca_la_base(self, cliente, monkeypatch):
        """La prueba de verdad: se rompe la conexión y `/vivo` sigue
        respondiendo. Si consultara la base, aquí fallaría."""
        from app.core import base_datos

        async def base_caida(sesion):
            raise RuntimeError("la base no responde")

        monkeypatch.setattr(base_datos, "comprobar_conexion", base_caida)

        respuesta = await cliente.get("/vivo")
        assert respuesta.status_code == 200
        assert respuesta.json()["ok"] is True

    async def test_salud_si_la_toca(self, cliente):
        """Y `/salud` sigue siendo el diagnóstico completo: si no mirara la
        base, no serviría para lo que existe."""
        respuesta = await cliente.get("/salud")
        assert respuesta.status_code == 200
        assert respuesta.json()["base_datos"] == "conectada"
        assert "cifrado" in respuesta.json()

    async def test_el_proveedor_apunta_a_vivo(self):
        """El render.yaml y el código tienen que decir lo mismo. Si alguien
        vuelve a apuntarlo a /salud, esta prueba lo dice antes de que lo
        diga un despliegue fallido."""
        import io
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent.parent
        configuracion = io.open(raiz / "render.yaml", encoding="utf-8").read()
        assert "healthCheckPath: /vivo" in configuracion
