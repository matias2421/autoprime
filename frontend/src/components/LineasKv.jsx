/**
 * Motivo gráfico de líneas diagonales de la identidad.
 *
 * Es un haz de rectas que nacen fuera del encuadre, por abajo a la izquierda,
 * y se abren hacia arriba. Se superpone a las fotografías con mezcla "lighten"
 * (clase `.lineas-kv`), de modo que solo puede aclarar la imagen: nunca la
 * ensucia ni compromete el contraste del texto que va encima.
 *
 * Es puramente decorativo, así que queda fuera del árbol de accesibilidad.
 */

const TOTAL = 16;

// Punto de fuga, fuera del lienzo por la esquina inferior izquierda.
const FUGA = { x: -30, y: 130 };

const lineas = Array.from({ length: TOTAL }, (_, i) => {
  // Los extremos superiores se reparten a lo ancho, con más densidad
  // a la izquierda para que el haz se vea abrirse.
  const t = i / (TOTAL - 1);
  const x = -20 + 150 * t ** 1.55;
  return { x1: FUGA.x, y1: FUGA.y, x2: x, y2: -15, key: i };
});

function LineasKv({ className = "", opacidad = 0.45 }) {
  return (
    <svg
      className={`lineas-kv ${className}`}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      style={{ opacity: opacidad }}
    >
      <defs>
        {/* Las rectas se desvanecen hacia arriba para que no corten el encuadre. */}
        <linearGradient id="lineas-kv-fundido" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="#829fb0" stopOpacity="0" />
          <stop offset="30%" stopColor="#a9bdc8" stopOpacity="0.9" />
          <stop offset="70%" stopColor="#ffffff" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {lineas.map(({ x1, y1, x2, y2, key }) => (
        <line
          key={key}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="url(#lineas-kv-fundido)"
          strokeWidth="0.14"
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}

export default LineasKv;
