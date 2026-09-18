"""Paginación, compartida por todos los listados que pueden crecer.

Los listados del cuarto avance devolvían la tabla entera. Con diez vehículos
y tres usuarios eso no se nota, pero ventas y mensajes de chat crecen sin
techo: el día que haya diez mil filas, `GET /api/ventas` se trae diez mil
filas, las serializa y las manda por la red para pintar veinte.

El tope de `por_pagina` no es decoración: sin él, `?porPagina=999999` deja el
problema exactamente donde estaba, solo que ahora por petición del cliente.
"""

from typing import Annotated

from fastapi import Depends, Query

from app.schemas.comunes import Esquema

POR_PAGINA_POR_DEFECTO = 20
POR_PAGINA_MAXIMO = 100


class Pagina(Esquema):
    """Lo que necesita el frontend para dibujar el paginador."""

    pagina: int
    por_pagina: int
    total: int
    paginas: int


class ParametrosPagina:
    """Dependencia con `?pagina=` y `?porPagina=`.

    Es una clase y no una función porque así el desplazamiento se calcula una
    sola vez, aquí, y ningún endpoint tiene que acordarse de multiplicar.
    """

    def __init__(
        self,
        pagina: Annotated[int, Query(ge=1, description="Número de página")] = 1,
        por_pagina: Annotated[
            int,
            Query(
                ge=1,
                le=POR_PAGINA_MAXIMO,
                alias="porPagina",
                description=f"Filas por página (máximo {POR_PAGINA_MAXIMO})",
            ),
        ] = POR_PAGINA_POR_DEFECTO,
    ):
        self.pagina = pagina
        self.por_pagina = por_pagina
        self.limite = por_pagina
        self.desplazamiento = (pagina - 1) * por_pagina

    def resultado(self, total: int) -> Pagina:
        # Una lista vacía tiene cero páginas, no una página vacía.
        paginas = (total + self.por_pagina - 1) // self.por_pagina
        return Pagina(
            pagina=self.pagina,
            por_pagina=self.por_pagina,
            total=total,
            paginas=paginas,
        )


PaginaDep = Annotated[ParametrosPagina, Depends()]
