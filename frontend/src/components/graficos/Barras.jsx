/**
 * Barras horizontales, para rankings y cortes por estado.
 *
 * Horizontales y no verticales a propósito: las etiquetas son nombres de
 * vehículos («MANSORY Phantom VIII (2024)»), y en vertical hay que girarlas
 * o recortarlas. En horizontal la etiqueta va en su renglón y se lee sola.
 *
 * Se hace con divs y no con SVG porque una barra horizontal es un rectángulo
 * de ancho porcentual, que es exactamente lo que CSS ya sabe hacer: sin
 * viewBox, sin escalas y con el texto seleccionable.
 *
 * El valor va escrito al lado de cada barra, no en un tooltip. Un número que
 * solo aparece al pasar el puntero no existe en un móvil.
 */
function Barras({ datos, formato = (v) => v, vacio = "Sin datos todavía." }) {
  if (!datos || datos.length === 0) {
    return <p className="py-8 text-center text-sm text-plomo">{vacio}</p>;
  }

  const maximo = Math.max(...datos.map((d) => d.valor), 1);

  return (
    <ul className="space-y-4">
      {datos.map((d) => {
        // Un mínimo del 2% para que una fila con valor pequeño pero no nulo
        // siga dibujando algo: una barra invisible se lee como un cero.
        const porcentaje = Math.max((d.valor / maximo) * 100, d.valor > 0 ? 2 : 0);

        return (
          <li key={d.etiqueta}>
            <div className="flex items-baseline justify-between gap-4">
              <span className="truncate text-sm text-hueso" title={d.etiqueta}>
                {d.etiqueta}
              </span>
              <span className="shrink-0 font-sans text-sm text-accion-claro">
                {formato(d.valor)}
              </span>
            </div>

            <div className="mt-2 h-2 w-full bg-linea">
              <div
                className="h-full bg-accion transition-[width] duration-500 ease-out
                           motion-reduce:transition-none"
                style={{ width: `${porcentaje}%` }}
              />
            </div>

            {d.detalle && (
              <p className="mt-1 font-sans text-xs text-plomo">{d.detalle}</p>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default Barras;
