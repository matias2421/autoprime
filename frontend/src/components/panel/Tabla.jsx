import Icono from "../ui/Icono";

/**
 * Tabla de datos de los paneles, con sus tres estados.
 *
 * Existe porque las cuatro pantallas nuevas —ventas, facturas, PQR y citas—
 * repetían la misma estructura, y con ella los mismos olvidos: una tabla sin
 * estado vacío deja la pantalla en blanco cuando no hay filas y parece rota;
 * otra sin aviso de carga parpadea; otra sin desplazamiento horizontal se
 * desborda en un móvil.
 *
 * `columnas` es una lista de {clave, titulo, alineacion, ancho} y `fila` una
 * función que recibe el registro y devuelve las celdas. Quien la usa decide
 * qué pinta cada celda; esto solo pone el marco.
 */
function Tabla({
  columnas,
  filas,
  fila,
  clave = (r) => r.id,
  cargando = false,
  vacio = "No hay registros todavía.",
  pie,
}) {
  return (
    <div className="cristal overflow-hidden">
      {/* El desplazamiento va en el contenedor, no en la página: en un móvil
          la tabla se arrastra sola sin mover el resto del panel. */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <thead>
            <tr className="border-b border-linea">
              {columnas.map((c) => (
                <th
                  key={c.clave}
                  scope="col"
                  style={c.ancho ? { width: c.ancho } : undefined}
                  className={`px-4 py-3.5 font-sans text-xs uppercase
                              tracking-[0.14em] text-plomo ${
                                c.alineacion === "derecha"
                                  ? "text-right"
                                  : c.alineacion === "centro"
                                    ? "text-center"
                                    : ""
                              }`}
                >
                  {c.titulo}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {filas.map((registro) => (
              <tr
                key={clave(registro)}
                className="border-b border-linea/60 last:border-0
                           hover:bg-hueso/[0.03]"
              >
                {fila(registro)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cargando y vacío van fuera de la tabla: dentro tendrían que ser una
          fila con colSpan, y ese número se olvida al añadir una columna. */}
      {cargando && filas.length === 0 && (
        <p className="px-4 py-10 text-center text-sm text-ceniza">
          Cargando…
        </p>
      )}

      {!cargando && filas.length === 0 && (
        <div className="flex flex-col items-center gap-3 px-4 py-12 text-center">
          <Icono nombre="documento" className="h-6 w-6 text-trazo" />
          <p className="max-w-sm text-sm text-plomo">{vacio}</p>
        </div>
      )}

      {pie && <div className="border-t border-linea px-4 py-3">{pie}</div>}
    </div>
  );
}

/** Celda. `derecha` para importes: los números se comparan por su final. */
function Celda({ children, alineacion, className = "" }) {
  const alinear =
    alineacion === "derecha"
      ? "text-right tabular-nums"
      : alineacion === "centro"
        ? "text-center"
        : "";
  return (
    <td className={`px-4 py-3.5 text-sm text-ceniza ${alinear} ${className}`}>
      {children}
    </td>
  );
}

export { Tabla, Celda };
export default Tabla;
