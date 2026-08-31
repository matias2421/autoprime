/**
 * Enlaces a las redes del concesionario.
 *
 * Los perfiles son de muestra: este es un proyecto académico y las cuentas no
 * existen. Cada enlace lleva su nombre accesible, porque el icono por sí solo
 * no dice nada a un lector de pantalla.
 */

const REDES = [
  {
    nombre: "Instagram",
    url: "https://www.instagram.com/",
    ruta: "M12 7.6a4.4 4.4 0 1 0 0 8.8 4.4 4.4 0 0 0 0-8.8Zm0 7.25a2.85 2.85 0 1 1 0-5.7 2.85 2.85 0 0 1 0 5.7Z M17.2 7.25a1.03 1.03 0 1 1-2.06 0 1.03 1.03 0 0 1 2.06 0Z M12 3.6c-2.28 0-2.57.01-3.47.05-.9.04-1.51.18-2.05.4a4.1 4.1 0 0 0-1.5.97c-.46.46-.75.93-.97 1.5-.21.53-.36 1.14-.4 2.04C3.58 9.46 3.57 9.75 3.57 12s.01 2.54.05 3.44c.04.9.19 1.51.4 2.05.22.57.51 1.04.97 1.5.46.46.93.75 1.5.97.54.21 1.15.36 2.05.4.9.04 1.19.05 3.46.05s2.57-.01 3.47-.05c.9-.04 1.51-.19 2.05-.4a4.1 4.1 0 0 0 1.5-.97c.46-.46.75-.93.97-1.5.21-.54.36-1.15.4-2.05.04-.9.05-1.19.05-3.44s-.01-2.54-.05-3.44c-.04-.9-.19-1.51-.4-2.05a4.1 4.1 0 0 0-.97-1.5 4.1 4.1 0 0 0-1.5-.97c-.54-.21-1.15-.36-2.05-.4-.9-.04-1.19-.05-3.47-.05Zm0 1.55c2.24 0 2.5.01 3.39.05.82.04 1.26.17 1.55.29.39.15.67.33.96.62.3.29.48.57.63.96.11.29.25.73.29 1.54.04.88.05 1.15.05 3.39s-.01 2.51-.05 3.39c-.04.81-.18 1.25-.29 1.54-.15.39-.33.67-.63.96-.29.29-.57.47-.96.62-.29.12-.73.25-1.55.29-.88.04-1.15.05-3.39.05s-2.51-.01-3.39-.05c-.82-.04-1.26-.17-1.55-.29a2.6 2.6 0 0 1-.96-.62 2.6 2.6 0 0 1-.63-.96c-.11-.29-.25-.73-.29-1.54-.04-.88-.05-1.15-.05-3.39s.01-2.51.05-3.39c.04-.81.18-1.25.29-1.54.15-.39.33-.67.63-.96.29-.29.57-.47.96-.62.29-.12.73-.25 1.55-.29.88-.04 1.15-.05 3.39-.05Z",
  },
  {
    nombre: "YouTube",
    url: "https://www.youtube.com/",
    ruta: "M21.2 8.1a2.4 2.4 0 0 0-1.7-1.7C18 6 12 6 12 6s-6 0-7.5.4A2.4 2.4 0 0 0 2.8 8.1C2.4 9.6 2.4 12 2.4 12s0 2.4.4 3.9a2.4 2.4 0 0 0 1.7 1.7C6 18 12 18 12 18s6 0 7.5-.4a2.4 2.4 0 0 0 1.7-1.7c.4-1.5.4-3.9.4-3.9s0-2.4-.4-3.9ZM10.2 14.9V9.1l5 2.9-5 2.9Z",
  },
  {
    nombre: "LinkedIn",
    url: "https://www.linkedin.com/",
    ruta: "M6.94 8.5H4.1V19.5h2.84V8.5ZM5.52 4.5a1.65 1.65 0 1 0 0 3.3 1.65 1.65 0 0 0 0-3.3ZM19.9 13.4c0-3.06-1.63-4.48-3.81-4.48-1.76 0-2.55.97-2.99 1.65V8.5H10.3c.04.8 0 11 0 11h2.8v-6.14c0-.25.02-.5.09-.68.2-.5.65-1.01 1.42-1.01 1 0 1.4.76 1.4 1.88V19.5h2.8v-6.1Z",
  },
  {
    nombre: "Facebook",
    url: "https://www.facebook.com/",
    ruta: "M20 12.06C20 7.6 16.42 4 12 4s-8 3.6-8 8.06c0 4.02 2.93 7.36 6.75 7.94v-5.62h-2.03v-2.32h2.03v-1.77c0-2.02 1.2-3.14 3.02-3.14.88 0 1.79.16 1.79.16v1.98h-1.01c-1 0-1.31.62-1.31 1.26v1.51h2.22l-.35 2.32h-1.87V20A8.04 8.04 0 0 0 20 12.06Z",
  },
];

function RedesSociales({ className = "", titulo }) {
  return (
    <ul className={`flex flex-wrap items-center gap-3 ${className}`}>
      {REDES.map(({ nombre, url, ruta }) => (
        <li key={nombre}>
          <a
            href={url}
            target="_blank"
            rel="noreferrer noopener"
            aria-label={titulo ? `${titulo} en ${nombre}` : nombre}
            title={nombre}
            className="pulsable flex h-11 w-11 items-center justify-center border border-trazo
                       text-ceniza hover:border-accion hover:text-accion"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
              <path d={ruta} fill="currentColor" />
            </svg>
          </a>
        </li>
      ))}
    </ul>
  );
}

export default RedesSociales;
