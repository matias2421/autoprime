# -*- coding: utf-8 -*-
"""El importe en letras de las facturas.

Esta tabla no es decorativa: encontró dos errores reales en la primera
versión. Con 1.200.000.000 —la escala del catálogo de AutoPrime— el
conversor reventaba con un IndexError, porque los millones también tienen
miles y se estaban deletreando como si no pasaran de 999. Y escribía «UNO
PESOS» en vez de «UN PESO».

Las dos habrían salido en la primera factura que alguien descargara.
"""

import pytest

from app.reportes.letras import en_letras


@pytest.mark.parametrize(
    "importe, esperado",
    [
        (0, "CERO PESOS M/CTE"),

        # Singular: el sustantivo va en singular y «uno» se apocopa.
        (1, "UN PESO M/CTE"),
        (2, "DOS PESOS M/CTE"),

        # El tramo que se escribe junto, y el que lleva «y».
        (15, "QUINCE PESOS M/CTE"),
        (16, "DIECISÉIS PESOS M/CTE"),
        (21, "VEINTIÚN PESOS M/CTE"),
        (30, "TREINTA PESOS M/CTE"),
        (31, "TREINTA Y UN PESOS M/CTE"),
        (99, "NOVENTA Y NUEVE PESOS M/CTE"),

        # «Cien» a secas, «ciento» con algo detrás.
        (100, "CIEN PESOS M/CTE"),
        (101, "CIENTO UN PESOS M/CTE"),
        (200, "DOSCIENTOS PESOS M/CTE"),
        (999, "NOVECIENTOS NOVENTA Y NUEVE PESOS M/CTE"),

        # Miles: «mil» sin «uno» delante.
        (1_000, "MIL PESOS M/CTE"),
        (1_001, "MIL UN PESOS M/CTE"),
        (2_000, "DOS MIL PESOS M/CTE"),
        (21_000, "VEINTIÚN MIL PESOS M/CTE"),
        (100_000, "CIEN MIL PESOS M/CTE"),
        (350_000, "TRESCIENTOS CINCUENTA MIL PESOS M/CTE"),

        # Millones: plural del sustantivo y el «de» de la cifra redonda.
        (1_000_000, "UN MILLÓN DE PESOS M/CTE"),
        (2_000_000, "DOS MILLONES DE PESOS M/CTE"),
        (2_500_000, "DOS MILLONES QUINIENTOS MIL PESOS M/CTE"),
        (21_000_000, "VEINTIÚN MILLONES DE PESOS M/CTE"),

        # La escala del catálogo. Aquí reventaba la primera version.
        (1_200_000_000, "MIL DOSCIENTOS MILLONES DE PESOS M/CTE"),
        (3_200_000_000, "TRES MIL DOSCIENTOS MILLONES DE PESOS M/CTE"),
        (16_000_000_000, "DIECISÉIS MIL MILLONES DE PESOS M/CTE"),

        # Un total con IVA, que es lo que sale de verdad en una factura.
        (3_808_416_500,
         "TRES MIL OCHOCIENTOS OCHO MILLONES CUATROCIENTOS DIECISÉIS MIL "
         "QUINIENTOS PESOS M/CTE"),
    ],
)
def test_importes(importe, esperado):
    assert en_letras(importe) == esperado


def test_ignora_los_centavos():
    """El peso colombiano no los usa; «CON CERO CENTAVOS» en cada factura
    seria ruido."""
    assert en_letras(1_000_000.75) == en_letras(1_000_000)


def test_un_negativo_no_revienta():
    """No deberia llegar uno, pero si llega vale mas que lo diga a que tumbe
    la factura entera."""
    assert en_letras(-5_000).startswith("MENOS")
