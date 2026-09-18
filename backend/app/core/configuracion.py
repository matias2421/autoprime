"""Configuración leída del entorno.

Nada de credenciales en el código: todo llega por variables de entorno o por
el fichero `.env`, que queda fuera del repositorio. En un servidor no hay
`.env` que valga —Render, Aiven y compañía inyectan variables— y por eso todo
lo que cambia entre el portátil y el despliegue vive aquí.
"""

from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


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
        """Cadena de conexión de SQLAlchemy."""
        if self.database_url:
            return self._normalizar(self.database_url)

        # La contraseña se escapa porque las que generan los proveedores
        # llevan símbolos que, sin escapar, parten la URL en dos.
        return (
            f"mysql+pymysql://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @staticmethod
    def _normalizar(cruda: str) -> str:
        """Deja una URI de proveedor en la forma que entiende SQLAlchemy.

        Las cadenas que reparten Aiven o Render vienen pensadas para el cliente
        de línea de órdenes: empiezan por `mysql://` y traen parámetros como
        `ssl-mode=REQUIRED`. SQLAlchemy necesita saber qué driver usar, y
        PyMySQL no conoce esos parámetros: si le llegan, revientan la conexión
        con un error que no menciona la causa. Así que se cambia el esquema y
        se descarta todo lo que no sea suyo.
        """
        partes = urlsplit(cruda)

        esquema = partes.scheme
        if esquema in ("mysql", "mariadb"):
            esquema = "mysql+pymysql"

        consulta = [(c, v) for c, v in parse_qsl(partes.query) if c == "charset"]
        if not consulta:
            consulta.append(("charset", "utf8mb4"))

        return urlunsplit(
            (esquema, partes.netloc, partes.path, urlencode(consulta), "")
        )

    @property
    def conexion_args(self) -> dict:
        """Opciones que se pasan al driver, no a SQLAlchemy."""
        if not self.db_ssl_ca:
            # Sin certificado no se fuerza nada: PyMySQL intenta TLS de todos
            # modos y lo consigue con cualquier proveedor serio.
            return {}

        return {
            "ssl_ca": self.db_ssl_ca,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        }


configuracion = Configuracion()
