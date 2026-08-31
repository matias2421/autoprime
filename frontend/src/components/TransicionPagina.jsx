import { useLocation } from "react-router-dom";

/**
 * Transición de entrada entre páginas.
 *
 * La `key` es la ruta, así que React desmonta y vuelve a montar el contenido
 * en cada navegación y la animación arranca de cero. Es todo lo que hace
 * falta: no hay animación de salida porque exigiría retener la página vieja
 * y retrasaría la nueva sin ganar nada.
 *
 * Con `prefers-reduced-motion` la regla global deja la animación en 0,01 ms,
 * de modo que el cambio es instantáneo.
 */
function TransicionPagina({ children }) {
  const { pathname } = useLocation();

  return (
    <div key={pathname} className="pagina-entra">
      {children}
    </div>
  );
}

export default TransicionPagina;
