/**
 * Marca de líneas que flanquea el logotipo.
 *
 * Tres reglas horizontales con el borde exterior escalonado y un ligero sesgo,
 * que leen como estelas de velocidad. Se usan en pareja: una a cada lado del
 * nombre, la de la derecha reflejada.
 *
 * El trazo hereda el color del texto (`currentColor`), de modo que la misma
 * pieza sirve sobre fondo oscuro y sobre fondo claro.
 */

/* Cada regla llega hasta el borde interior (x = 44) y arranca escalonada. */
const REGLAS = [
  { y: 5, desde: 4 },
  { y: 12, desde: 16 },
  { y: 19, desde: 9 },
];

function MarcaLineas({ className = "", reflejada = false }) {
  /*
   * El reflejo se aplica DENTRO del svg, no en su elemento raíz: quien use
   * esta pieza necesita el `transform` de la raíz libre para animarla, y una
   * animación sobre ese mismo eje anularía el reflejo.
   */
  const giro = reflejada
    ? "translate(44,0) scale(-1,1) skewX(-12)"
    : "skewX(-12)";

  return (
    <svg viewBox="0 0 44 24" className={className} aria-hidden="true" focusable="false">
      {/* El sesgo da la inclinación; el trazo no escala con el viewBox. */}
      <g transform={giro}>
        {REGLAS.map(({ y, desde }) => (
          <line
            key={y}
            x1={desde}
            y1={y}
            x2={44}
            y2={y}
            stroke="currentColor"
            strokeWidth="1.1"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </g>
    </svg>
  );
}

export default MarcaLineas;
