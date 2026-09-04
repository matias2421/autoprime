# -*- coding: utf-8 -*-
"""Comprueba la configuración de correo saliente y manda un mensaje de prueba.

Configurar SMTP suele costar más de lo que parece: el servidor contesta con
códigos escuetos y siempre puede fallar por cuatro o cinco motivos distintos.
Este script traduce cada uno a lo que hay que corregir, para no ir cambiando
cosas del `.env` a ciegas.

    venv\\Scripts\\python probar_correo.py
    venv\\Scripts\\python probar_correo.py otra.direccion@ejemplo.com

Sin argumento, el mensaje se envía a la propia cuenta configurada.
"""

import smtplib
import socket
import ssl
import sys
from email.message import EmailMessage
from email.utils import parseaddr

from app.core.configuracion import configuracion


def titulo(texto: str) -> None:
    print()
    print("=" * 70)
    print(f" {texto}")
    print("=" * 70)


def revisar_configuracion() -> bool:
    """Enseña lo que hay en el `.env`, sin descubrir la contraseña."""
    titulo("CONFIGURACION LEIDA")

    clave = configuracion.smtp_password
    print(f"  SMTP_HOST      : {configuracion.smtp_host or '(vacio)'}")
    print(f"  SMTP_PUERTO    : {configuracion.smtp_puerto}")
    print(f"  SMTP_USUARIO   : {configuracion.smtp_usuario or '(vacio)'}")
    # La contraseña no se imprime; solo su longitud, que ya delata los dos
    # errores mas comunes: dejarla vacia o pegarla con los espacios que
    # Google muestra al generarla.
    print(f"  SMTP_PASSWORD  : {'*' * len(clave)} ({len(clave)} caracteres)")
    print(f"  Remitente      : {configuracion.remitente_correo}")
    print(f"  URL_FRONTEND   : {configuracion.url_frontend}")

    if not configuracion.correo_configurado:
        print()
        print("  SIN CONFIGURAR. Faltan datos en backend/.env.")
        print("  Mientras tanto la API no falla: escribe el enlace de")
        print("  recuperacion en su registro en lugar de enviarlo.")
        return False

    if " " in clave:
        print()
        print("  AVISO: la contrasena tiene espacios. Google la muestra en")
        print("  grupos de cuatro por comodidad, pero hay que pegarla junta.")

    # Enviar en nombre de una direccion ajena es lo que hace posible el correo
    # falsificado, asi que los proveedores no lo permiten: Gmail reescribe la
    # cabecera a la cuenta autenticada y quien recibe ve esa, no la declarada.
    # Sin este aviso, el sintoma seria un correo que "llega mal" sin motivo.
    direccion = parseaddr(configuracion.remitente_correo)[1].lower()
    if direccion and direccion != configuracion.smtp_usuario.lower():
        print()
        print("  AVISO: SMTP_REMITENTE apunta a una direccion distinta de la")
        print(f"  cuenta autenticada ({configuracion.smtp_usuario}).")
        print()
        print(f"    declarado : {direccion}")
        print(f"    real      : {configuracion.smtp_usuario}")
        print()
        print("  Gmail reescribira el remitente a la cuenta autenticada, salvo")
        print("  que esa direccion este dada de alta como alias verificado en")
        print("  Gmail > Configuracion > Cuentas > Enviar como.")
        print()
        print("  Para que el correo salga de verdad desde otra direccion hay")
        print("  que autenticarse con ella: crear esa cuenta, activarle la")
        print("  verificacion en dos pasos y usar SU contrasena de aplicacion.")
        print()
        print("  Si solo se busca que en la bandeja se lea 'AutoPrime', basta")
        print("  con el nombre delante de la direccion propia:")
        print(f"    SMTP_REMITENTE=AutoPrime <{configuracion.smtp_usuario}>")

    return True


def enviar(destinatario: str) -> bool:
    """Intenta la entrega real y explica el fallo si lo hay."""
    titulo(f"ENVIANDO A {destinatario}")

    mensaje = EmailMessage()
    mensaje["Subject"] = "Prueba de correo de AutoPrime"
    mensaje["From"] = configuracion.remitente_correo
    mensaje["To"] = destinatario
    mensaje.set_content(
        "Si estas leyendo esto, el servidor de correo de AutoPrime funciona.\n\n"
        "Ya puedes usar la recuperacion de contrasena: el enlace llegara por\n"
        "esta misma via.\n\n-- AutoPrime"
    )

    contexto = ssl.create_default_context()
    host, puerto = configuracion.smtp_host, configuracion.smtp_puerto

    try:
        if puerto == 465:
            print(f"  Conectando a {host}:{puerto} (SSL directo)...")
            servidor = smtplib.SMTP_SSL(host, puerto, context=contexto, timeout=20)
        else:
            print(f"  Conectando a {host}:{puerto} (STARTTLS)...")
            servidor = smtplib.SMTP(host, puerto, timeout=20)

        with servidor:
            if puerto != 465:
                servidor.starttls(context=contexto)
                print("  Canal cifrado.")
            servidor.login(configuracion.smtp_usuario, configuracion.smtp_password)
            print("  Autenticado.")
            servidor.send_message(mensaje)
            print("  Mensaje entregado al servidor.")

    except smtplib.SMTPAuthenticationError as error:
        print(f"\n  FALLO DE AUTENTICACION: {error.smtp_code} {error.smtp_error}")
        print("\n  Con Gmail esto casi siempre significa una de dos cosas:")
        print("   - Se puso la contrasena de la cuenta y no una de aplicacion.")
        print("   - La verificacion en dos pasos no esta activada, y sin ella")
        print("     Google ni siquiera deja generar contrasenas de aplicacion")
        print("     (la pagina responde 'no disponible para tu cuenta').")
        print("\n  Se arregla en myaccount.google.com/security, activando la")
        print("  verificacion en dos pasos, y luego en /apppasswords.")
        return False

    except (socket.gaierror, ConnectionRefusedError) as error:
        print(f"\n  NO SE PUDO CONECTAR: {error}")
        print("\n  Revisa SMTP_HOST. Para Gmail es smtp.gmail.com.")
        print("  Comprueba tambien que haya conexion a internet.")
        return False

    except (TimeoutError, socket.timeout):
        print("\n  EL SERVIDOR NO CONTESTO A TIEMPO.")
        print("\n  Suele ser el puerto: 587 con STARTTLS o 465 con SSL.")
        print("  Algunas redes tambien bloquean el correo saliente.")
        return False

    except ssl.SSLError as error:
        print(f"\n  FALLO DE CIFRADO: {error}")
        print("\n  Puerto y modo no encajan: 465 va cifrado desde el saludo")
        print("  inicial y 587 empieza en claro y sube con STARTTLS.")
        return False

    except (smtplib.SMTPException, OSError) as error:
        print(f"\n  FALLO: {type(error).__name__}: {error}")
        return False

    return True


def principal() -> int:
    if not revisar_configuracion():
        return 1

    destinatario = sys.argv[1] if len(sys.argv) > 1 else configuracion.smtp_usuario

    if not enviar(destinatario):
        return 1

    titulo("TODO CORRECTO")
    print(f"  Revisa la bandeja de {destinatario}.")
    print("  Si no aparece, mira en correo no deseado.")
    print()
    print("  La recuperacion de contrasena ya enviara el enlace por esta via.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
