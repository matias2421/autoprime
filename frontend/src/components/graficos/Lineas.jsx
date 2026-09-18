import { useId } from "react";

/**
 * Serie temporal: línea con relleno, para ingresos por día.
 *
 * Está hecha a mano en SVG y no con una librería de gráficas por dos razones.
 * La identidad del sitio es propia y una gráfica genérica se ve pegada; y una
 * librería de gráficas pesa más que todo el resto del panel junto para
 * dibujar dos polilíneas.
 *
 * Lo que sí hereda del suelo de calidad del proyecto: los valores se leen sin
 * pasar el puntero por encima. Una gráfica cuyos números solo aparecen al
 * hacer hover no existe en un móvil, y no existe para quien navega con
 * teclado. Aquí los extremos van rotulados siempre, y debajo hay una tabla
 * para lectores de pantalla.
 */
function Lineas({
  datos,
  formato = (v) => v,
  titulo = "Serie por día",
  alto = 220,
}) {
  const id = useId();

  // El viewBox fija el sistema de coordenadas; el ancho real lo pone el CSS,
  // así que la gráfica se adapta al contenedor sin recalcular nada.
  const ANCHO = 720;
  const ALTO = alto;
  const MARGEN = { arriba: 28, derecha: 16, abajo: 32, izquierda: 16 };

  if (!datos || datos.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-plomo">
        Sin datos en el periodo seleccionado.
      </p>
    );
  }

  const valores = datos.map((d) => d.valor);

  /*
   * Dos maximos distintos, y confundirlos rompe la grafica.
   *
   * `cumbre` es el valor mas alto que hay de verdad, y puede ser cero: un
   * periodo sin ventas es un caso normal, no un error.
   *
   * `escala` es entre cuanto se divide para calcular las alturas, y no puede
   * ser cero. Cuando eran la misma variable, un periodo vacio la dejaba en 1
   * -para no dividir entre cero- y `indexOf(1)` devolvia -1, porque ningun
   * dia valia uno. La pantalla entera se caia al leer `datos[-1].etiqueta`.
   */
  const cumbre = Math.max(...valores);
  const escala = cumbre > 0 ? cumbre : 1;
  const indiceCumbre = Math.max(valores.indexOf(cumbre), 0);

  const util = {
    ancho: ANCHO - MARGEN.izquierda - MARGEN.derecha,
    alto: ALTO - MARGEN.arriba - MARGEN.abajo,
  };

  // Con un solo punto no hay tramo que repartir: se coloca en el centro.
  const x = (i) =>
    datos.length === 1
      ? MARGEN.izquierda + util.ancho / 2
      : MARGEN.izquierda + (i * util.ancho) / (datos.length - 1);

  const y = (valor) => MARGEN.arriba + util.alto - (valor / escala) * util.alto;

  const puntos = datos.map((d, i) => [x(i), y(d.valor)]);
  const linea = puntos.map(([px, py]) => `${px},${py}`).join(" ");
  const area = `${MARGEN.izquierda},${MARGEN.arriba + util.alto} ${linea} ${
    x(datos.length - 1)
  },${MARGEN.arriba + util.alto}`;

  // Con muchos días no caben todas las fechas: se rotulan cuatro repartidas.
  const paso = Math.max(1, Math.ceil(datos.length / 4));

  return (
    <figure className="m-0">
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        className="h-auto w-full"
        role="img"
        aria-label={
          cumbre > 0
            ? `${titulo}. Máximo ${formato(cumbre)} el ${datos[indiceCumbre].etiqueta}.`
            : `${titulo}. Sin movimiento en el periodo.`
        }
      >
        <defs>
          <linearGradient id={`relleno-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-accion)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-accion)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Tres reglas de fondo: dan escala sin competir con la línea. */}
        {[0, 0.5, 1].map((fraccion) => (
          <line
            key={fraccion}
            x1={MARGEN.izquierda}
            x2={ANCHO - MARGEN.derecha}
            y1={MARGEN.arriba + util.alto * fraccion}
            y2={MARGEN.arriba + util.alto * fraccion}
            stroke="var(--color-linea)"
            strokeWidth="1"
          />
        ))}

        <polygon points={area} fill={`url(#relleno-${id})`} />
        <polyline
          points={linea}
          fill="none"
          stroke="var(--color-accion)"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {puntos.map(([px, py], i) => (
          <circle
            key={datos[i].etiqueta}
            cx={px}
            cy={py}
            r={i === indiceCumbre ? 5 : 3}
            fill={i === indiceCumbre ? "var(--color-accion-claro)" : "var(--color-negro)"}
            stroke="var(--color-accion)"
            strokeWidth="2"
          />
        ))}

        {/* La cumbre, rotulada siempre: es el dato que se busca al mirar.
            Con el periodo a cero no se rotula nada, que un «$0» flotando
            sobre la linea de base no informa de nada. */}
        {cumbre > 0 && (
          <text
            x={Math.min(Math.max(x(indiceCumbre), 44), ANCHO - 44)}
            y={Math.max(y(cumbre) - 12, 14)}
            textAnchor="middle"
            className="fill-hueso font-sans text-[13px]"
          >
            {formato(cumbre)}
          </text>
        )}

        {datos.map((d, i) =>
          i % paso === 0 || i === datos.length - 1 ? (
            <text
              key={d.etiqueta}
              x={x(i)}
              y={ALTO - 10}
              textAnchor={
                i === 0 ? "start" : i === datos.length - 1 ? "end" : "middle"
              }
              className="fill-plomo font-sans text-[12px]"
            >
              {d.corta ?? d.etiqueta}
            </text>
          ) : null
        )}
      </svg>

      {/* Lo mismo en texto, para quien no ve el dibujo. */}
      <table className="sr-only">
        <caption>{titulo}</caption>
        <tbody>
          {datos.map((d) => (
            <tr key={d.etiqueta}>
              <th scope="row">{d.etiqueta}</th>
              <td>{formato(d.valor)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

export default Lineas;
