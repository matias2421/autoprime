"""Envío de correo por SMTP.

Se usa `smtplib` de la biblioteca estándar en lugar de una dependencia nueva:
el proyecto envía un único tipo de mensaje y no necesita plantillas, colas ni
proveedores intercambiables.

Si no hay servidor configurado, el mensaje no se pierde en silencio: el enlace
se escribe en el registro del servidor con un aviso. Así el flujo se puede
probar antes de tener buzón, y queda evidente que era una configuración
pendiente y no un fallo del código.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import quote

from app.core.configuracion import configuracion

logger = logging.getLogger("autoprime.correo")


def _enlace_recuperacion(token: str) -> str:
    """Arma la dirección que abrirá quien reciba el correo.

    El token va en la cadena de consulta porque es lo que el enlace de un
    correo puede transportar; por eso mismo vive minutos y sirve una sola vez.
    """
    return f"{configuracion.url_frontend.rstrip('/')}/restablecer?token={quote(token)}"


def _mensaje_recuperacion(destinatario: str, nombre: str, enlace: str) -> EmailMessage:
    """Construye el correo con sus dos versiones, texto y HTML.

    El texto plano no es un descarte: hay clientes que no muestran HTML y
    filtros de correo que desconfían de los mensajes que solo lo traen.
    """
    mensaje = EmailMessage()
    mensaje["Subject"] = "Restablece tu contraseña de AutoPrime"
    mensaje["From"] = configuracion.remitente_correo
    mensaje["To"] = destinatario

    minutos = configuracion.minutos_expiracion_recuperacion

    mensaje.set_content(
        f"""Hola {nombre}:

Recibimos una solicitud para restablecer la contraseña de tu cuenta en
AutoPrime. Abre esta dirección para crear una nueva:

{enlace}

El enlace caduca en {minutos} minutos y sirve una sola vez.

Si no fuiste tú, no hace falta que hagas nada: mientras no abras el enlace,
tu contraseña sigue siendo la misma.

— AutoPrime, atelier automotriz
"""
    )

    mensaje.add_alternative(
        f"""<html>
  <body style="margin:0;padding:32px 16px;background:#020204;
               font-family:Helvetica,Arial,sans-serif;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"
           width="100%" style="max-width:520px;margin:0 auto;
                               background:#0d0d13;border:1px solid #22222b;">
      <tr>
        <td style="padding:32px 32px 24px;">
          <p style="margin:0 0 24px;font-size:11px;letter-spacing:2px;
                    text-transform:uppercase;color:#829fb0;">AutoPrime</p>

          <h1 style="margin:0 0 16px;font-size:24px;font-weight:normal;
                     color:#ffffff;">Restablece tu contraseña</h1>

          <p style="margin:0 0 16px;font-size:15px;line-height:1.6;
                    color:#b6b6b6;">
            Hola {nombre}: recibimos una solicitud para cambiar la contraseña
            de tu cuenta. Pulsa el botón para crear una nueva.
          </p>

          <p style="margin:0 0 24px;">
            <a href="{enlace}"
               style="display:inline-block;padding:14px 28px;
                      background:#3d6274;color:#ffffff;text-decoration:none;
                      font-size:14px;letter-spacing:1px;
                      text-transform:uppercase;">Crear contraseña nueva</a>
          </p>

          <p style="margin:0 0 24px;font-size:13px;line-height:1.6;
                    color:#8f8f93;">
            El enlace caduca en {minutos} minutos y sirve una sola vez.
            Si el botón no funciona, copia esta dirección en tu navegador:<br>
            <span style="color:#829fb0;word-break:break-all;">{enlace}</span>
          </p>

          <p style="margin:0;padding-top:20px;border-top:1px solid #22222b;
                    font-size:13px;line-height:1.6;color:#8f8f93;">
            Si no fuiste tú, no hace falta que hagas nada: mientras no abras
            el enlace, tu contraseña sigue siendo la misma.
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>""",
        subtype="html",
    )

    return mensaje


def _entregar(mensaje: EmailMessage) -> None:
    """Abre la conexión con el servidor y entrega el mensaje.

    El puerto decide el modo: 465 va cifrado desde el saludo inicial, y
    cualquier otro —587 es el habitual— empieza en claro y sube a TLS con
    STARTTLS. El tiempo límite evita que un servidor que no responde deje la
    tarea colgada indefinidamente.
    """
    contexto = ssl.create_default_context()
    host = configuracion.smtp_host
    puerto = configuracion.smtp_puerto

    if puerto == 465:
        with smtplib.SMTP_SSL(host, puerto, context=contexto, timeout=20) as servidor:
            servidor.login(configuracion.smtp_usuario, configuracion.smtp_password)
            servidor.send_message(mensaje)
    else:
        with smtplib.SMTP(host, puerto, timeout=20) as servidor:
            servidor.starttls(context=contexto)
            servidor.login(configuracion.smtp_usuario, configuracion.smtp_password)
            servidor.send_message(mensaje)


def enviar_enlace_recuperacion(destinatario: str, nombre: str, token: str) -> None:
    """Envía el correo con el enlace para restablecer la contraseña.

    Pensada para ejecutarse como tarea de fondo: la respuesta al navegador no
    debe esperar a que el servidor de correo conteste, que puede tardar
    segundos. Por eso tampoco propaga la excepción —ya no hay a quién
    devolvérsela— y deja constancia en el registro.
    """
    enlace = _enlace_recuperacion(token)

    if not configuracion.correo_configurado:
        logger.warning(
            "SMTP sin configurar: el correo para %s no se envio. Enlace: %s",
            destinatario,
            enlace,
        )
        return

    try:
        _entregar(_mensaje_recuperacion(destinatario, nombre, enlace))
        logger.info("Enlace de recuperacion enviado a %s", destinatario)
    except (smtplib.SMTPException, OSError) as error:
        # Un fallo aquí no se le cuenta a quien lo pidió: decir "ese correo no
        # existe en nuestro servidor" revelaría lo mismo que el endpoint evita
        # revelar. Queda en el registro para quien administre el sistema.
        logger.error("No se pudo enviar el correo a %s: %s", destinatario, error)
