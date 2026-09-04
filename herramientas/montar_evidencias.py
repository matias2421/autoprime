# -*- coding: utf-8 -*-
"""Incrusta las capturas en el documento de verificación de los 26 requisitos.

Las imágenes van dentro del propio HTML, en base64, y no como archivos aparte:
así el documento es una sola pieza que se puede enviar, abrir sin la carpeta al
lado o imprimir a PDF sin que se rompan las rutas.

Antes de incrustarlas las reduce, porque una captura de 1440 px pesa medio mega
y veintiséis de esas harían un documento que no hay quien mueva.

    backend/venv/Scripts/python herramientas/montar_evidencias.py
"""

import base64
import io as _io
import os
import re
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPTURAS = os.path.join(RAIZ, "evidencias", "capturas")
PLANTILLA = os.path.join(RAIZ, "evidencias", "verificacion.html")

ANCHO_MAXIMO = 1120

# Requisito -> archivo y pie de foto.
FICHAS = {
    "01": ("req-01-portada", "La portada servida por Vite, consumiendo la API."),
    "02": ("req-02-estructura", "Árbol del proyecto y del paquete `app`."),
    "03": ("req-03-entorno", "Versión de Python y dependencias del entorno."),
    "04": ("req-04-tablas", "Las siete tablas del esquema."),
    "05": ("req-05-tabla-usuarios", "Campos de `usuarios`; la contraseña es `password_hash`."),
    "06": ("req-06-esquemas", "Los esquemas de Pydantic publicados en la documentación."),
    "07": ("req-07-salud", "La API responde tras consultar la base de verdad."),
    "08": ("req-08-revalidacion", "Alta duplicada pedida sin pasar por el formulario."),
    "09": ("req-09-registro", "Formulario de alta de cliente."),
    "10": ("req-10-login", "Formulario de acceso."),
    "11": ("req-11-jwt", "El token descodificado: usuario, rol y caducidad."),
    "12": ("req-12-roles", "Un cliente pidiendo la lista de usuarios."),
    "13": ("req-13-hooks", "Hooks propios y uso de los de React."),
    "14": ("req-14-catalogo", "Catálogo servido por `GET /api/productos`."),
    "15": ("req-15-recuperar", "Primer paso de la recuperación."),
    "16": ("req-16-crud-usuarios", "Alta desde el panel, con selección de rol."),
    "17": ("req-17-panel-admin", "Panel de administración."),
    "18": ("req-18-panel-empleado", "Panel de empleado."),
    "19": ("req-19-panel-cliente", "Panel de cliente."),
    "20": ("req-20-navbar", "El nombre y el rol, en la navegación."),
    "21": ("req-21-validacion", "Aviso mientras se escribe, sin llegar a enviar."),
    "22": ("req-22-hash", "Hashes bcrypt: misma longitud, valores distintos."),
    "23": ("req-23-entorno", "Plantilla publicada y `.env` real ignorado."),
    "24": ("req-24-whatsapp", "El botón flotante, abajo a la derecha."),
    "25": ("req-25-swagger", "Documentación interactiva en `/docs`."),
    "26": ("req-26-pruebas", "Las 81 comprobaciones por HTTP."),
}

ESTILOS = """
  /* --- Capturas --- */
  .evidencia { margin: 0.35rem 0 0; }

  .evidencia img {
    display: block;
    width: 100%;
    height: auto;
    border: 1px solid var(--linea);
    background: var(--negro);
  }

  .evidencia figcaption {
    margin-top: 0.6rem;
    font-size: 0.8rem;
    color: var(--plomo);
    display: flex;
    gap: 0.6rem;
    align-items: baseline;
  }

  .evidencia figcaption b {
    font-family: var(--mono);
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accion);
    white-space: nowrap;
  }
"""


def incrustar(nombre: str) -> tuple[str, int, int]:
    """Reduce la captura y la devuelve como URI de datos."""
    ruta = os.path.join(CAPTURAS, f"{nombre}.png")
    imagen = Image.open(ruta).convert("RGB")

    if imagen.width > ANCHO_MAXIMO:
        alto = round(imagen.height * ANCHO_MAXIMO / imagen.width)
        imagen = imagen.resize((ANCHO_MAXIMO, alto), Image.LANCZOS)

    # Las fichas de consola son texto sobre fondo liso: en PNG con paleta
    # quedan nítidas y pesan poco. Las pantallas llevan fotografía y degradados,
    # donde el PNG se dispara y el JPEG no se nota.
    colores = imagen.getcolors(maxcolors=6000)
    if colores is not None:
        buffer = _io.BytesIO()
        imagen.quantize(colors=64, method=Image.MEDIANCUT).save(
            buffer, "PNG", optimize=True
        )
        tipo = "png"
    else:
        buffer = _io.BytesIO()
        imagen.save(buffer, "JPEG", quality=86, optimize=True, progressive=True)
        tipo = "jpeg"

    crudo = buffer.getvalue()
    uri = f"data:image/{tipo};base64,{base64.b64encode(crudo).decode()}"
    return uri, len(crudo), imagen.height


def main() -> int:
    if not os.path.isfile(PLANTILLA):
        print(f"  Falta {PLANTILLA}")
        return 1

    documento = _io.open(PLANTILLA, encoding="utf-8").read()

    # Se quitan las evidencias de una pasada anterior antes de volver a poner
    # las de ahora: así el montaje se puede repetir tantas veces como haga
    # falta sin ir acumulando copias de cada imagen.
    documento, quitadas = re.subn(
        r'\s*<figure class="evidencia">.*?</figure>\s*',
        "\n        ",
        documento,
        flags=re.DOTALL,
    )
    if quitadas:
        print(f"  Se retiran {quitadas} evidencias de la pasada anterior")
        print()

    if ".evidencia img" not in documento:
        documento = documento.replace(
            "  /* --- Cierre --- */", ESTILOS + "\n  /* --- Cierre --- */", 1
        )

    total = 0
    puestas = 0

    for numero, (archivo, pie) in sorted(FICHAS.items()):
        if not os.path.isfile(os.path.join(CAPTURAS, f"{archivo}.png")):
            print(f"  REQ-{numero}: falta {archivo}.png")
            continue

        uri, peso, alto = incrustar(archivo)
        total += peso

        figura = (
            f'\n          <figure class="evidencia">\n'
            f'            <img src="{uri}" alt="Evidencia del requisito {numero}: {pie}"\n'
            f'                 width="{ANCHO_MAXIMO}" height="{alto}" loading="lazy">\n'
            f"            <figcaption><b>Evidencia</b><span>{pie}</span></figcaption>\n"
            f"          </figure>\n        "
        )

        # La figura va como última hija de `.cuerpo`, no dentro de la rejilla
        # de pistas: ahí sería una celda más y la captura saldría a media
        # anchura, que es lo que pasó en el primer montaje. El ancla es el
        # primer `</div>` seguido de `</article>`, que solo puede ser el
        # cierre de `.cuerpo`.
        patron = re.compile(
            r'(<p class="numero">REQ-' + numero + r"</p>.*?)(</div>\s*</article>)",
            re.DOTALL,
        )
        documento, n = patron.subn(lambda m: m.group(1) + figura + m.group(2),
                                   documento, count=1)
        if n:
            puestas += 1
            print(f"  REQ-{numero}  {archivo}.png  {peso / 1024:>6.0f} KB")
        else:
            print(f"  REQ-{numero}: no se encontró dónde insertar")

    _io.open(PLANTILLA, "w", encoding="utf-8").write(documento)

    print()
    print(f"  {puestas} evidencias incrustadas")
    print(f"  imágenes: {total / 1024 / 1024:.1f} MB  ->  documento: "
          f"{os.path.getsize(PLANTILLA) / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
