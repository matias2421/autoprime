import { useEnVista, useMovimientoReducido } from "../hooks/useScroll";

/**
 * Envoltorio que hace aparecer su contenido cuando entra en pantalla.
 * Si el sistema pide menos movimiento, el contenido se muestra tal cual.
 *
 * `retraso` en milisegundos permite escalonar varios elementos seguidos.
 */
function Revelar({ children, retraso = 0, className = "", as: Etiqueta = "div" }) {
  const [ref, enVista] = useEnVista();
  const reducido = useMovimientoReducido();

  if (reducido) {
    return <Etiqueta className={className}>{children}</Etiqueta>;
  }

  return (
    <Etiqueta
      ref={ref}
      className={`transition-[opacity,transform] duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        enVista ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0"
      } ${className}`}
      style={{ transitionDelay: enVista ? `${retraso}ms` : "0ms" }}
    >
      {children}
    </Etiqueta>
  );
}

export default Revelar;
