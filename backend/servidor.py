# -*- coding: utf-8 -*-
"""Arranca la API en local. En Windows, además, la arregla.

    venv\\Scripts\\python servidor.py

El problema que resuelve: en Windows, el bucle de eventos que asyncio elige por
defecto —`ProactorEventLoop`— no consigue levantar una conexión TLS con la base
de datos. Falla con `[WinError 87] El parámetro no es correcto`, que no dice
nada de TLS ni de nada, y SQLAlchemy lo envuelve en un «Can't connect to MySQL
server» que apunta en la dirección equivocada: parece la base caída cuando en
realidad está perfectamente.

Con `SelectorEventLoop` funciona. Y hay que elegirlo *antes* de que uvicorn
cree el suyo: para cuando importa `app.main`, el bucle ya existe y cambiar la
política no sirve de nada. De ahí este arrancador en vez de un apaño dentro de
la aplicación.

En Linux no pasa, así que en Render se sigue lanzando uvicorn directamente y
este archivo no interviene. Solo hace falta para desarrollar en Windows contra
una base remota; contra el MySQL de XAMPP, que va sin cifrar, tampoco.
"""

import asyncio
import sys
import warnings

if sys.platform == "win32":
    # `set_event_loop_policy` está marcada para desaparecer en Python 3.16.
    # Se silencia el aviso a conciencia: hoy es la única forma de elegir el
    # bucle, porque uvicorn no acepta que se le pase uno.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402 — después de fijar la política, a propósito


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    print(f"  bucle : {'Selector (Windows)' if sys.platform == 'win32' else 'por defecto'}")
    print(f"  puerto: {puerto}")
    print()

    uvicorn.run("app.main:app", host="127.0.0.1", port=puerto, reload=True)
