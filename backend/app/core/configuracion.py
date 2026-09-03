"""Configuración leída del entorno.

Nada de credenciales en el código: todo llega por variables de entorno o por
el fichero `.env`, que queda fuera del repositorio.
"""

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

    # Vite cambia de puerto cuando el anterior está ocupado, así que se
    # admiten los tres primeros que suele elegir.
    origenes_permitidos: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]

    # --- Base de datos (MySQL / MariaDB de XAMPP) ---
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "autoprime"

    # --- Seguridad ---
    # `secret_key` va sin valor por defecto a propósito: si falta, la
    # aplicación no arranca. Una clave por defecto en el código acabaría
    # llegando a producción y permitiría a cualquiera firmar tokens válidos.
    secret_key: str
    algoritmo_jwt: str = "HS256"
    horas_expiracion_token: int = 8
    rondas_bcrypt: int = 10

    @property
    def url_base_datos(self) -> str:
        """Cadena de conexión de SQLAlchemy, armada con las piezas de arriba."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


configuracion = Configuracion()
