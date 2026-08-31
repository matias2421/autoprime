import { Link } from "react-router-dom";

const BASE =
  // `pulsable` da el hundido al presionar y `barrido` la luz que cruza al
  // pasar el puntero; ambas viven en index.css.
  "inline-flex items-center justify-center gap-3 font-sans uppercase tracking-[0.14em] " +
  "font-medium cursor-pointer select-none pulsable barrido " +
  "focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-accion-claro " +
  "disabled:cursor-not-allowed disabled:opacity-50";

const VARIANTES = {
  /* Relleno sólido: la acción principal de cada pantalla. */
  primario: "bg-accion-fondo text-hueso hover:bg-accion-hondo",
  /* Contorno fino sobre imagen o fondo oscuro. */
  contorno:
    "border border-hueso/35 text-hueso hover:border-hueso hover:bg-hueso/10",
  /* Cristal: destaca sin recurrir al acento y sin introducir una superficie
     clara, que en esta identidad no existe. */
  claro: "cristal cristal-vivo text-hueso",
  /* Sin caja, para acciones terciarias. */
  texto:
    "text-hueso underline-offset-8 hover:text-accion-claro hover:underline px-0",
};

/* Alturas generosas al estilo editorial; todas superan los 44 px táctiles. */
const TAMANOS = {
  sm: "min-h-11 px-5 text-xs",
  md: "min-h-14 px-8 text-sm",
  lg: "min-h-16 px-10 text-sm",
};

function Cargando() {
  return (
    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.3" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Botón reutilizable. Se renderiza como <button>, como <Link> de React Router
 * (prop `to`) o como <a> (prop `href`).
 */
function Button({
  children,
  variante = "primario",
  tamano = "md",
  ancho = false,
  cargando = false,
  to,
  href,
  className = "",
  type = "button",
  disabled,
  ...props
}) {
  const clases = [
    BASE,
    VARIANTES[variante] ?? VARIANTES.primario,
    TAMANOS[tamano] ?? TAMANOS.md,
    ancho ? "w-full" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (to) {
    return (
      <Link to={to} className={clases} {...props}>
        {children}
      </Link>
    );
  }

  if (href) {
    return (
      <a href={href} className={clases} {...props}>
        {children}
      </a>
    );
  }

  return (
    <button
      type={type}
      className={clases}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      {...props}
    >
      {cargando && <Cargando />}
      {children}
    </button>
  );
}

export default Button;
