/**
 * Set de iconos SVG (trazo, estilo Lucide).
 * Regla del design system: nunca usar emojis como iconos.
 */
const TRAZOS = {
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  cerrar: <path d="M6 6l12 12M18 6L6 18" />,
  izquierda: <path d="M15 6l-6 6 6 6" />,
  derecha: <path d="M9 6l6 6-6 6" />,
  flecha: <path d="M5 12h14M13 6l6 6-6 6" />,
  ojo: (
    <>
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  ojoCerrado: (
    <>
      <path d="M4 4l16 16" />
      <path d="M9.9 5.2A9.9 9.9 0 0 1 12 5c6.4 0 10 7 10 7a17.7 17.7 0 0 1-3.4 4.3" />
      <path d="M6.6 7.3A17.6 17.6 0 0 0 2 12s3.6 7 10 7a9.7 9.7 0 0 0 4.2-.9" />
      <path d="M10 10a3 3 0 0 0 4 4" />
    </>
  ),
  check: <path d="M4 12.5l5 5L20 6.5" />,
  alerta: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5M12 16.2v.1" />
    </>
  ),
  correo: (
    <>
      <rect x="2.5" y="5" width="19" height="14" rx="2.5" />
      <path d="M3 7l9 6 9-6" />
    </>
  ),
  candado: (
    <>
      <rect x="4" y="10.5" width="16" height="10" rx="2.5" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
    </>
  ),
  usuario: (
    <>
      <circle cx="12" cy="8" r="3.8" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </>
  ),
  telefono: (
    <path d="M6.5 3.5h3l1.5 4-2 1.4a12 12 0 0 0 6.1 6.1l1.4-2 4 1.5v3a2 2 0 0 1-2.2 2A17 17 0 0 1 4.5 5.7a2 2 0 0 1 2-2.2z" />
  ),
  ubicacion: (
    <>
      <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11z" />
      <circle cx="12" cy="10" r="2.6" />
    </>
  ),
  auto: (
    <>
      <path d="M3 13.5l1.8-5A2.5 2.5 0 0 1 7.2 7h9.6a2.5 2.5 0 0 1 2.4 1.5l1.8 5" />
      <path d="M3 13.5h18v4H3zM6.5 17.5v2M17.5 17.5v2" />
      <path d="M6.5 15.5h.1M17.4 15.5h.1" />
    </>
  ),
  escudo: (
    <>
      <path d="M12 3l7.5 3v5.5c0 4.4-3.1 8.3-7.5 9.5-4.4-1.2-7.5-5.1-7.5-9.5V6z" />
      <path d="M9 12l2.2 2.2L15.5 10" />
    </>
  ),
  llave: (
    <>
      <circle cx="8" cy="8" r="4" />
      <path d="M11 11l9 9M17 17l2-2M14 14l2-2" />
    </>
  ),
  herramienta: (
    <path d="M15.5 3.5a5 5 0 0 0-5.9 6.4L3.5 16a2.1 2.1 0 0 0 3 3l6.1-6.1a5 5 0 0 0 6.4-5.9L16.2 9.4l-2-.1-.1-2z" />
  ),
  etiqueta: (
    <>
      <path d="M3.5 11.6V4.5a1 1 0 0 1 1-1h7.1a2 2 0 0 1 1.4.6l7 7a2 2 0 0 1 0 2.8l-6.1 6.1a2 2 0 0 1-2.8 0l-7-7a2 2 0 0 1-.6-1.4z" />
      <path d="M7.8 7.8h.1" />
    </>
  ),
  reloj: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5.3l3.3 2" />
    </>
  ),
  tarjeta: (
    <>
      <rect x="2.5" y="5" width="19" height="14" rx="2.5" />
      <path d="M2.5 9.5h19M6 15h3" />
    </>
  ),
  documento: (
    <>
      <rect x="3" y="4.5" width="18" height="15" rx="2.5" />
      <circle cx="9" cy="11" r="2.2" />
      <path d="M5.5 16.5a3.8 3.8 0 0 1 7 0M14.5 9.5h4M14.5 13h4" />
    </>
  ),
  estrella: (
    <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z" />
  ),
  rayo: <path d="M13.5 2.5L5 13.5h6l-.5 8L19 10.5h-6z" />,
  chevronAbajo: <path d="M6 9l6 6 6-6" />,
  whatsapp: (
    <path d="M3.5 20.5l1.3-4.4a8 8 0 1 1 3.1 3.1zM9 9.2c.3-.7.6-.7.9-.7h.7c.2 0 .5 0 .8.6l1 2.2c.1.3 0 .5-.1.7l-.5.6c-.2.2-.3.4-.1.7a7 7 0 0 0 3.2 2.7c.3.1.5.1.7-.1l.7-.8c.2-.2.4-.2.6-.1l2 1c.3.2.4.3.4.5 0 .5-.3 1.4-.8 1.7-.5.3-1.3.6-2.2.4a11 11 0 0 1-7.4-6.4c-.3-1-.2-1.8.1-2.3z" />
  ),
};

function Icono({ nombre, className = "h-5 w-5", relleno = false, ...props }) {
  const trazo = TRAZOS[nombre];
  if (!trazo) return null;

  return (
    <svg
      viewBox="0 0 24 24"
      fill={relleno ? "currentColor" : "none"}
      stroke={relleno ? "none" : "currentColor"}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {trazo}
    </svg>
  );
}

export default Icono;
