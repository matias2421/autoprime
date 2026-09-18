# -*- coding: utf-8 -*-
"""Deja lista una base de datos vacía: esquema, catálogo y usuarios.

Sirve tanto para MySQL local como para una base remota de un proveedor. Es lo
que hace falta para arrancar en Aiven, Render o donde sea, porque allí no hay
consola de MySQL a mano ni Node instalado para el sembrador del avance
anterior.

    venv\\Scripts\\python preparar_base.py
    venv\\Scripts\\python preparar_base.py --reiniciar

Se conecta con lo que diga la configuración: `DATABASE_URL` si está puesta, y
si no, las piezas sueltas del `.env`. Nunca pide credenciales por argumento,
para que no acaben en el historial de la consola.
"""

import argparse
import os
import re
import sys

import bcrypt
from sqlalchemy import create_engine, text

from app.core.configuracion import configuracion

RAIZ = os.path.dirname(os.path.abspath(__file__))
ESQUEMA = os.path.join(RAIZ, "sql", "autoprime.sql")

# En el orden en que hay que vaciarlas, aunque se desactiven las claves ajenas.
TABLAS = ["citas", "rol_permiso", "usuarios", "productos", "servicios",
          "permisos", "roles"]

USUARIOS = [
    {
        "nombre": "Jose Matias", "apellido": "Agudelo Bolivar",
        "tipo_documento": "CC", "numero_documento": "1088111222",
        "direccion": "Av. Las Americas 45-12", "telefono": "3001112233",
        "correo": "admin@autoprime.com.co", "password": "Admin2026!",
        "rol": "administrador",
    },
    {
        "nombre": "Carolina", "apellido": "Rivera Osorio",
        "tipo_documento": "CC", "numero_documento": "1088333444",
        "direccion": "Carrera 12 34-56", "telefono": "3002223344",
        "correo": "empleado@autoprime.com.co", "password": "Empleado2026!",
        "rol": "empleado",
    },
    {
        "nombre": "Andres", "apellido": "Zapata Molina",
        "tipo_documento": "CC", "numero_documento": "1088555666",
        "direccion": "Calle 45 12-30, Barrio Centro", "telefono": "3003334455",
        "correo": "cliente@autoprime.com.co", "password": "Cliente2026!",
        "rol": "cliente",
    },
]


def sentencias(sql: str):
    """Trocea el guion en sentencias, respetando las comillas.

    Partir por `;` a secas rompería cualquier texto que llevara uno dentro, y
    las descripciones del catálogo son prosa. Este recorrido salta lo que esté
    entrecomillado y los comentarios de línea.
    """
    actual, comilla, salida = [], None, []
    i = 0
    while i < len(sql):
        c = sql[i]

        if comilla:
            actual.append(c)
            if c == "\\":                       # escape dentro de la cadena
                if i + 1 < len(sql):
                    actual.append(sql[i + 1])
                    i += 2
                    continue
            elif c == comilla:
                comilla = None
        elif c in ("'", '"'):
            comilla = c
            actual.append(c)
        elif c == "-" and sql[i:i + 2] == "--":
            salto = sql.find("\n", i)
            i = len(sql) if salto == -1 else salto + 1
            continue
        elif c == ";":
            trozo = "".join(actual).strip()
            if trozo:
                salida.append(trozo)
            actual = []
        else:
            actual.append(c)
        i += 1

    resto = "".join(actual).strip()
    if resto:
        salida.append(resto)
    return salida


def aplicables(sql: str):
    """Descarta lo que solo tiene sentido contra un MySQL propio.

    `DROP DATABASE`, `CREATE DATABASE` y `USE` fallan en un proveedor
    gestionado: allí la base viene creada y la cuenta no tiene permiso para
    tocar otras. La conexión ya apunta a la que toca, así que sobran.
    """
    descartar = re.compile(r"^\s*(DROP\s+DATABASE|CREATE\s+DATABASE|USE)\b",
                           re.IGNORECASE)
    return [s for s in sentencias(sql) if not descartar.match(s)]


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument(
        "--reiniciar", action="store_true",
        help="vacía las tablas antes de crearlas, por si ya existían",
    )
    opciones = analizador.parse_args()

    # De la URL solo se enseña el destino: la contraseña va dentro.
    destino = configuracion.url_base_datos_sincrona.split("@")[-1]
    print(f"  Base de datos : {destino}")
    print(f"  TLS verificado: {'sí' if configuracion.db_ssl_ca else 'no (modo preferente)'}")
    print()

    # Este script va en sincrono a proposito: es una tarea de una sola pasada
    # y no gana nada con el bucle de eventos. La API si es asincrona, asi que
    # aqui se piden la URL y las opciones de TLS en su forma sincrona.
    motor = create_engine(
        configuracion.url_base_datos_sincrona,
        connect_args=configuracion.conexion_args_sincrona,
        pool_pre_ping=True,
    )

    try:
        with motor.begin() as conexion:
            if opciones.reiniciar:
                print("  Vaciando las tablas existentes...")
                conexion.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
                for tabla in TABLAS:
                    conexion.exec_driver_sql(f"DROP TABLE IF EXISTS {tabla}")
                conexion.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")

            print("  Creando esquema y catálogo...")
            with open(ESQUEMA, encoding="utf-8") as f:
                guion = f.read()

            for sentencia in aplicables(guion):
                conexion.exec_driver_sql(sentencia)

            # --- Usuarios, con la contraseña ya hasheada ---
            print("  Creando los usuarios de prueba...")
            roles = dict(
                conexion.exec_driver_sql("SELECT nombre, id FROM roles").fetchall()
            )

            for u in USUARIOS:
                clave = bcrypt.hashpw(
                    u["password"].encode("utf-8"),
                    bcrypt.gensalt(rounds=configuracion.rondas_bcrypt),
                ).decode("utf-8")

                conexion.execute(
                    text(
                        "INSERT INTO usuarios (nombre, apellido, tipo_documento,"
                        " numero_documento, direccion, telefono, correo,"
                        " password_hash, rol_id)"
                        " VALUES (:nombre, :apellido, :tipo_documento,"
                        " :numero_documento, :direccion, :telefono, :correo,"
                        " :password_hash, :rol_id)"
                        " ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)"
                    ),
                    {
                        **{c: u[c] for c in (
                            "nombre", "apellido", "tipo_documento",
                            "numero_documento", "direccion", "telefono", "correo",
                        )},
                        "password_hash": clave,
                        "rol_id": roles[u["rol"]],
                    },
                )

    except Exception as error:  # noqa: BLE001 — se traduce y se sale
        print()
        print(f"  FALLO: {type(error).__name__}")
        print(f"  {str(error)[:300]}")
        print()
        if "Unknown database" in str(error):
            print("  La base no existe. En un proveedor gestionado se crea desde")
            print("  su panel, no desde aquí, y la URL debe apuntar a ella.")
        elif "Access denied" in str(error):
            print("  Usuario o contraseña incorrectos en DATABASE_URL.")
        elif "already exists" in str(error):
            print("  Ya hay tablas creadas. Vuelve a lanzarlo con --reiniciar")
            print("  si quieres rehacerlas desde cero.")
        return 1

    # --- Comprobación de lo que ha quedado ---
    print()
    with motor.connect() as conexion:
        for tabla in reversed(TABLAS):
            n = conexion.exec_driver_sql(
                f"SELECT COUNT(*) FROM {tabla}"
            ).scalar()
            print(f"    {tabla:<14} {n:>4} filas")

    print()
    print("  Lista. Cuentas de prueba:")
    for u in USUARIOS:
        print(f"    {u['rol']:<15} {u['correo']:<30} {u['password']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
