"""Configuración leída del entorno.

Nada de credenciales en el código: todo llega por variables de entorno o por
el fichero `.env`, que queda fuera del repositorio. En un servidor no hay
`.env` que valga —Render, Aiven y compañía inyectan variables— y por eso todo
lo que cambia entre el portátil y el despliegue vive aquí.
"""

import logging
import ssl
import tempfile
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("autoprime")

# El PEM escrito a disco vive lo que vive el proceso; se guarda aqui para
# no crear un archivo nuevo en cada conexion.
_CERTIFICADO_TEMPORAL: str | None = None
_AVISADO_SIN_CERTIFICADO = False


def _avisar_sin_certificado() -> None:
    """Avisa una vez, no en cada conexion del pool."""
    global _AVISADO_SIN_CERTIFICADO
    if _AVISADO_SIN_CERTIFICADO:
        return
    _AVISADO_SIN_CERTIFICADO = True
    logger.warning(
        "La conexion con la base va cifrada pero SIN verificar el servidor: "
        "falta el certificado. Pon DB_SSL_CA (ruta) o DB_SSL_CA_CONTENIDO "
        "(el PEM pegado) para completar la verificacion."
    )


class Configuracion(BaseSettings):
    """Ajustes de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Aplicación ---
    nombre_app: str = "AutoPrime API"
    version: str = "2.0.0"
    entorno: str = "desarrollo"  # desarrollo | produccion

    # Orígenes que pueden llamar a la API, separados por comas.
    #
    # Va como texto y no como lista a propósito: pydantic espera JSON para los
    # campos de tipo lista, y escribir `["https://..."]` en el panel de un
    # proveedor es fácil de equivocar y el error que devuelve no ayuda nada.
    # Vite cambia de puerto cuando el anterior está ocupado, así que en local
    # se admiten los tres primeros que suele elegir.
    origenes_permitidos: str = (
        "http://localhost:5173,http://localhost:5174,http://localhost:5175"
    )

    # --- Base de datos ---
    #
    # Dos formas de configurarla, y la primera gana:
    #
    # 1. `DATABASE_URL` con la cadena entera. Es lo que dan Aiven, Render y
    #    casi cualquier proveedor: se copia y se pega, sin desmontarla.
    # 2. Las piezas sueltas, que es lo cómodo en local contra XAMPP.
    database_url: str = ""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "autoprime"

    # Certificado de la autoridad que firma el servidor, si el proveedor lo
    # ofrece (Aiven lo deja descargar). Con él la conexión va cifrada *y*
    # verificada; sin él, PyMySQL negocia TLS igualmente en modo preferente,
    # pero sin comprobar contra quién habla.
    db_ssl_ca: str = ""

    # --- Seguridad ---
    # `secret_key` va sin valor por defecto a propósito: si falta, la
    # aplicación no arranca. Una clave por defecto en el código acabaría
    # llegando a producción y permitiría a cualquiera firmar tokens válidos.
    secret_key: str
    algoritmo_jwt: str = "HS256"
    horas_expiracion_token: int = 8
    rondas_bcrypt: int = 10

    # El enlace para restablecer la contraseña vive minutos, no horas: es
    # una credencial de un solo uso y cuanto menos tiempo exista, mejor.
    minutos_expiracion_recuperacion: int = 30

    # --- Correo saliente ---
    # Dirección pública del frontend: con ella se arma el enlace que viaja en
    # el correo, así que en un despliegue real apunta al dominio, no a
    # localhost.
    url_frontend: str = "http://localhost:5173"

    # Vacío significa "sin servidor de correo": entonces el enlace se escribe
    # en el registro en lugar de enviarse, para que el flujo siga siendo
    # probable antes de configurar el buzón.
    smtp_host: str = ""
    smtp_puerto: int = 587
    smtp_usuario: str = ""
    smtp_password: str = ""
    smtp_remitente: str = ""

    # --- Asistente (Groq) ---
    #
    # La clave NO tiene valor por defecto ni aparece en el codigo: se lee del
    # entorno y punto. Si falta, el chat responde que el asistente no esta
    # disponible y ofrece dejar una PQR; el resto de la API sigue funcionando.
    # Es la diferencia entre una funcion que se degrada y un despliegue que
    # no arranca.
    #
    # Groq habla el mismo protocolo que OpenAI, asi que la URL es lo unico
    # que cambia si algun dia se sustituye el proveedor.
    groq_api_key: str = ""
    groq_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_modelo: str = "openai/gpt-oss-20b"

    # Un modelo que tarda mas de esto ya perdio la conversacion: mas vale
    # decir que no esta disponible que dejar a alguien mirando tres puntos.
    groq_timeout: float = 20.0

    # Techo de la respuesta. Un chat de atencion no necesita ensayos.
    groq_max_tokens: int = 700

    # Cuantos mensajes previos se le reenvian al modelo. El historial entero
    # crece sin limite y cada peticion lo paga entero; con los ultimos basta
    # para que la conversacion tenga sentido.
    mensajes_de_contexto: int = 10

    # --- Servicios externos ---
    #
    # Calendario de festivos de Colombia. Se usa para no ofrecer citas en
    # dias en que el taller no abre.
    url_festivos: str = "https://date.nager.at/api/v3/PublicHolidays"
    festivos_timeout: float = 8.0

    # ------------------------------------------------------------------
    @property
    def origenes(self) -> list[str]:
        """Los orígenes permitidos, ya troceados."""
        return [o.strip() for o in self.origenes_permitidos.split(",") if o.strip()]

    @property
    def correo_configurado(self) -> bool:
        """Si falta cualquiera de las tres piezas, no hay envío posible."""
        return bool(self.smtp_host and self.smtp_usuario and self.smtp_password)

    @property
    def remitente_correo(self) -> str:
        """Quién firma el mensaje; por defecto, la cuenta que lo envía."""
        return (
            self.smtp_remitente
            or self.smtp_usuario
            or "no-responder@autoprime.com.co"
        )

    @property
    def url_base_datos(self) -> str:
        """Cadena de conexión de la API, que habla con la base en asíncrono."""
        return self._con_driver("mysql+aiomysql")

    @property
    def url_base_datos_sincrona(self) -> str:
        """La misma base, pero para los scripts de línea de órdenes.

        Preparar la base o sembrarla son tareas de una sola pasada: no ganan
        nada siendo asíncronas y sí pierden en claridad. Comparten destino con
        la API y solo cambian de driver.
        """
        return self._con_driver("mysql+pymysql")

    def _con_driver(self, driver: str) -> str:
        if self.database_url:
            return self._normalizar(self.database_url, driver)

        # La contraseña se escapa porque las que generan los proveedores
        # llevan símbolos que, sin escapar, parten la URL en dos.
        return (
            f"{driver}://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @staticmethod
    def _normalizar(cruda: str, driver: str = "mysql+aiomysql") -> str:
        """Deja una URI de proveedor en la forma que entiende SQLAlchemy.

        Las cadenas que reparten Aiven o Render vienen pensadas para el cliente
        de línea de órdenes: empiezan por `mysql://` y traen parámetros como
        `ssl-mode=REQUIRED`. SQLAlchemy necesita saber qué driver usar, y
        PyMySQL no conoce esos parámetros: si le llegan, revientan la conexión
        con un error que no menciona la causa. Así que se cambia el esquema y
        se descarta todo lo que no sea suyo.
        """
        partes = urlsplit(cruda)

        # Se impone el driver que toca, venga como venga: las URIs de los
        # proveedores dicen `mysql://` a secas, y las copiadas de un ejemplo
        # pueden traer ya un driver que no es el que queremos aquí.
        esquema = driver if partes.scheme.startswith(("mysql", "mariadb")) else partes.scheme

        consulta = [(c, v) for c, v in parse_qsl(partes.query) if c == "charset"]
        if not consulta:
            consulta.append(("charset", "utf8mb4"))

        return urlunsplit(
            (esquema, partes.netloc, partes.path, urlencode(consulta), "")
        )

    # ------------------------------ Cifrado ---------------------------------
    #
    # Aqui habia una suposicion, y era falsa. El codigo anterior decia: «sin
    # certificado no se fuerza nada, el driver negocia TLS de todos modos».
    # No lo hace. Preguntandoselo a la propia base —`SHOW STATUS LIKE
    # 'Ssl_cipher'`— el resultado con certificado era TLS_AES_256_GCM_SHA384
    # y sin el, cadena vacia: EN CLARO.
    #
    # Y en Render no se ponia el certificado, porque `ca.pem` es un archivo
    # local que no viaja al repositorio. Es decir: en el portatil iba cifrado
    # y en produccion —el unico sitio donde la conexion cruza internet de
    # verdad, de Oregon a Aiven— viajaban en claro las credenciales y todas
    # las filas. Justo al reves de lo que hacia falta.
    #
    # De ahi las tres reglas de abajo, en orden:
    #
    #   1. Con certificado: TLS verificado. Lo mejor, y es lo que se usa
    #      cuando `DB_SSL_CA` apunta a un archivo o `DB_SSL_CA_CONTENIDO`
    #      trae el PEM pegado en una variable de entorno.
    #   2. Sin certificado pero contra un servidor remoto: TLS igualmente,
    #      sin verificar quien esta al otro lado. No es lo ideal, pero cifra;
    #      y un despliegue mal configurado tiene que fallar hacia el lado
    #      seguro, no hacia el comodo.
    #   3. Contra localhost: sin TLS. El MySQL de XAMPP no lo ofrece, y el
    #      trafico no sale de la maquina.

    # El PEM pegado tal cual, para proveedores donde no se puede subir un
    # archivo. Render lo guarda cifrado y no pasa por el repositorio.
    db_ssl_ca_contenido: str = ""

    @property
    def es_base_local(self) -> bool:
        anfitrion = (urlsplit(self.database_url).hostname or self.db_host or "").lower()
        return anfitrion in ("localhost", "127.0.0.1", "::1", "")

    def _ruta_certificado(self) -> str:
        """Devuelve la ruta del CA, escribiendo el PEM a disco si hace falta.

        El archivo temporal se crea una sola vez por proceso: hacerlo en cada
        conexion llenaria el disco del contenedor de copias identicas.
        """
        if self.db_ssl_ca:
            return self.db_ssl_ca
        if not self.db_ssl_ca_contenido:
            return ""

        global _CERTIFICADO_TEMPORAL
        if _CERTIFICADO_TEMPORAL is None:
            archivo = tempfile.NamedTemporaryFile(
                mode="w", suffix=".pem", delete=False, encoding="utf-8"
            )
            # Algunos paneles pegan el PEM con \\n literales en
            # vez de saltos de linea de verdad. Sin deshacerlos, el certificado
            # no parsea y el error habla de ASN.1, no de la variable mal pegada.
            archivo.write(
                self.db_ssl_ca_contenido.replace("\\n", "\n")
            )
            archivo.close()
            _CERTIFICADO_TEMPORAL = archivo.name
        return _CERTIFICADO_TEMPORAL

    @property
    def conexion_args(self) -> dict:
        """Opciones de TLS para el driver asincrono de la API.

        aiomysql y PyMySQL no lo piden igual: PyMySQL acepta rutas sueltas
        (`ssl_ca`, `ssl_verify_cert`) y aiomysql quiere un contexto ya armado.
        Pasarle a uno lo del otro no da un error claro, asi que cada cual
        recibe lo suyo.
        """
        certificado = self._ruta_certificado()

        if certificado:
            contexto = ssl.create_default_context(cafile=certificado)
            contexto.check_hostname = True
            contexto.verify_mode = ssl.CERT_REQUIRED
            return {"ssl": contexto}

        if self.es_base_local:
            return {}

        _avisar_sin_certificado()
        contexto = ssl.create_default_context()
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
        return {"ssl": contexto}

    @property
    def conexion_args_sincrona(self) -> dict:
        """Lo mismo, en la forma que entiende PyMySQL, para los scripts."""
        certificado = self._ruta_certificado()

        if certificado:
            return {
                "ssl_ca": certificado,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
            }

        if self.es_base_local:
            return {}

        _avisar_sin_certificado()
        return {"ssl": {"check_hostname": False}}


configuracion = Configuracion()
