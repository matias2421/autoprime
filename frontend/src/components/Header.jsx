import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import Icono from "./ui/Icono";
import SelectorIdioma from "./SelectorIdioma";
import { useAuth } from "../hooks/useAuth";
import { useBloqueoScroll } from "../hooks/useBloqueoScroll";
import { useIdioma } from "../hooks/useIdioma";

/* Las listas guardan la CLAVE del diccionario, no el texto ya resuelto. */
const ENLACES = [
  { a: "/modelos", clave: "nav.modelos", icono: "auto" },
  { a: "/quienes-somos", clave: "nav.quienesSomos", icono: "escudo" },
  { a: "/contacto", clave: "nav.contacto", icono: "correo" },
];

const FAMILIAS = [
  { a: "/modelos?familia=gama", clave: "fam.gama" },
  { a: "/modelos?familia=edicion", clave: "fam.edicion" },
  { a: "/modelos?familia=coleccion", clave: "fam.coleccion" },
];

const AGENDAR = { a: "/agendar", clave: "nav.agendar", icono: "reloj" };

/** Ruta del panel que corresponde a cada rol. */
const PANEL_POR_ROL = {
  administrador: "/panel/admin",
  empleado: "/panel/empleado",
  cliente: "/panel/cliente",
};

/* El ancho del raíl plegado. Se repite en AppRouter para apartar el
   contenido, así que cambiarlo aquí obliga a cambiarlo allí. */
export const ANCHO_RAIL = 72;

function Logo() {
  return (
    <Link
      to="/"
      className="flex min-h-11 shrink-0 items-center gap-2.5"
      aria-label="AutoPrime, ir al inicio"
    >
      <span className="flex h-7 w-7 items-center justify-center bg-accion-fondo">
        <Icono nombre="auto" className="h-4 w-4 text-negro" />
      </span>
      <span className="font-sans text-base font-medium uppercase tracking-[0.28em] text-hueso sm:text-lg">
        AutoPrime
      </span>
    </Link>
  );
}

/**
 * Fila del raíl.
 *
 * El icono vive en una casilla de exactamente el ancho plegado, así que al
 * desplegarse no se mueve ni un píxel: lo único que entra es el rótulo. Un
 * icono que se desplaza al abrir delata el truco y marea la vista.
 */
function FilaRail({ a, icono, children, alPulsar }) {
  return (
    <NavLink
      to={a}
      onClick={alPulsar}
      className={({ isActive }) =>
        [
          "relative flex items-center transition-colors duration-200",
          isActive ? "text-hueso" : "text-ceniza hover:text-hueso",
        ].join(" ")
      }
    >
      {({ isActive }) => (
        <>
          {/* Marca de sección activa: la misma regla fina que el sitio usa
              bajo cada rótulo, aquí puesta de canto. */}
          <span
            aria-hidden="true"
            className={[
              "absolute left-0 top-0 h-full w-0.5 transition-colors duration-200",
              isActive ? "bg-accion" : "bg-transparent",
            ].join(" ")}
          />
          <span
            className="flex h-14 shrink-0 items-center justify-center"
            style={{ width: ANCHO_RAIL }}
          >
            <Icono nombre={icono} className="h-5 w-5" />
          </span>
          <span className="whitespace-nowrap pr-6 font-sans text-xs uppercase tracking-[0.18em]">
            {children}
          </span>
        </>
      )}
    </NavLink>
  );
}

function Header() {
  const [abierto, setAbierto] = useState(false);
  const [desplazado, setDesplazado] = useState(false);
  const cerrarMenu = () => setAbierto(false);

  const { autenticado, usuario, rol, cerrarSesion } = useAuth();
  const { t } = useIdioma();

  // El fondo no se desplaza mientras el menú a pantalla completa está abierto.
  useBloqueoScroll("menu", abierto);
  const navegar = useNavigate();

  const panel = PANEL_POR_ROL[rol] || "/panel/cliente";

  const salir = () => {
    cerrarSesion();
    cerrarMenu();
    navegar("/", { replace: true });
  };

  // La barra superior pasa de transparente a sólida al bajar. Solo afecta a
  // móvil y tableta: en escritorio manda el raíl, que siempre es cristal.
  useEffect(() => {
    const alDesplazar = () => setDesplazado(window.scrollY > 40);
    alDesplazar();
    window.addEventListener("scroll", alDesplazar, { passive: true });
    return () => window.removeEventListener("scroll", alDesplazar);
  }, []);

  useEffect(() => {
    if (!abierto) return undefined;
    const alTeclado = (e) => {
      if (e.key === "Escape") setAbierto(false);
    };
    document.addEventListener("keydown", alTeclado);
    return () => document.removeEventListener("keydown", alTeclado);
  }, [abierto]);

  return (
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-60
                   focus:bg-accion-fondo focus:px-5 focus:py-3 focus:font-sans focus:text-xs
                   focus:uppercase focus:tracking-[0.18em] focus:text-negro lg:focus:left-24"
      >
        {t("nav.saltar")}
      </a>

      {/* ==================== Raíl lateral · escritorio ==================== */}
      {/*
        Se despliega al apuntarlo y también al recibir el foco del teclado:
        sin `focus-within` quien navegue con tabulador leería los iconos sin
        su rótulo. No empuja el contenido —va fijo y se superpone—, de modo
        que la maqueta no se recalcula al pasar el ratón por encima.
      */}
      <aside
        aria-label={t("nav.menu")}
        /* El ancho va literal y no como variable CSS: Tailwind no llega a
           generar la regla con la forma `w-(--variable)` y el rail se
           quedaria sin ancho plegado, abierto de continuo. */
        /* En horizontal se recorta —es lo que oculta los rótulos mientras
           está plegado—, pero en vertical se desplaza: en una pantalla baja,
           al desplegar las familias el contenido crece y recortarlo dejaría
           fuera el idioma y la sesión, que son el pie del raíl. */
        className="cristal group fixed inset-y-0 left-0 z-40 hidden w-[72px]
                   overflow-x-hidden overflow-y-auto border-y-0 border-l-0
                   transition-[width] duration-300 ease-out
                   hover:w-66 focus-within:w-66 lg:flex lg:flex-col"
      >
        {/* Marca */}
        <Link
          to="/"
          aria-label="AutoPrime, ir al inicio"
          className="flex h-20 shrink-0 items-center border-b border-linea"
        >
          <span
            className="flex shrink-0 items-center justify-center"
            style={{ width: ANCHO_RAIL }}
          >
            <span className="flex h-9 w-9 items-center justify-center bg-accion-fondo">
              <Icono nombre="auto" className="h-5 w-5 text-negro" />
            </span>
          </span>
          <span className="whitespace-nowrap pr-6 font-sans text-sm font-medium uppercase tracking-[0.28em] text-hueso">
            AutoPrime
          </span>
        </Link>

        {/* Navegación */}
        <nav aria-label="Navegación principal" className="mt-4 flex flex-col">
          {ENLACES.map((enlace) => (
            <div key={enlace.a}>
              <FilaRail a={enlace.a} icono={enlace.icono}>
                {t(enlace.clave)}
              </FilaRail>

              {/* Las familias cuelgan de Modelos y solo existen desplegadas:
                  plegado el raíl no hay sitio para un segundo nivel. */}
              {enlace.a === "/modelos" && (
                <div
                  className="max-h-0 overflow-hidden opacity-0 transition-all duration-300
                             group-hover:max-h-40 group-hover:opacity-100
                             group-focus-within:max-h-40 group-focus-within:opacity-100"
                >
                  <ul style={{ paddingLeft: ANCHO_RAIL }} className="pb-2">
                    {FAMILIAS.map((familia) => (
                      <li key={familia.a}>
                        <Link
                          to={familia.a}
                          className="flex min-h-9 items-center whitespace-nowrap pr-6 font-sans
                                     text-[0.68rem] uppercase tracking-[0.16em] text-plomo
                                     transition-colors duration-200 hover:text-hueso"
                        >
                          {t(familia.clave)}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          <FilaRail a={AGENDAR.a} icono={AGENDAR.icono}>
            {t(AGENDAR.clave)}
          </FilaRail>
        </nav>

        {/* Pie del raíl: idioma y sesión */}
        <div className="mt-auto flex flex-col border-t border-linea pt-3">
          {autenticado ? (
            <>
              {/* Requisito 20: el usuario autenticado se identifica aquí. */}
              <NavLink
                to={panel}
                className={({ isActive }) =>
                  [
                    "relative flex items-center transition-colors duration-200",
                    isActive ? "text-hueso" : "text-ceniza hover:text-hueso",
                  ].join(" ")
                }
              >
                <span
                  className="flex h-14 shrink-0 items-center justify-center"
                  style={{ width: ANCHO_RAIL }}
                >
                  <Icono nombre="usuario" className="h-5 w-5 text-accion" />
                </span>
                <span className="whitespace-nowrap pr-6">
                  <span className="block font-sans text-xs uppercase tracking-[0.18em] text-hueso">
                    {usuario.nombre}
                  </span>
                  <span className="block font-sans text-[0.65rem] uppercase tracking-[0.16em] text-plomo">
                    {rol}
                  </span>
                </span>
              </NavLink>

              <button
                type="button"
                onClick={salir}
                className="flex cursor-pointer items-center text-ceniza transition-colors
                           duration-200 hover:text-accion-claro"
              >
                <span
                  className="flex h-12 shrink-0 items-center justify-center"
                  style={{ width: ANCHO_RAIL }}
                >
                  <Icono nombre="izquierda" className="h-5 w-5" />
                </span>
                <span className="whitespace-nowrap pr-6 font-sans text-xs uppercase tracking-[0.18em]">
                  {t("nav.salir")}
                </span>
              </button>
            </>
          ) : (
            <FilaRail a="/login" icono="usuario">
              {t("nav.entrar")}
            </FilaRail>
          )}

          <div className="flex items-center pb-4 pt-1">
            <span
              className="flex shrink-0 items-center justify-center"
              style={{ width: ANCHO_RAIL }}
            >
              <Icono nombre="etiqueta" className="h-4 w-4 text-plomo" />
            </span>
            <SelectorIdioma className="shrink-0" />
          </div>
        </div>
      </aside>

      {/* ================= Barra superior · móvil y tableta ================= */}
      <header
        className={[
          "fixed inset-x-0 top-0 z-40 transition-colors duration-300 lg:hidden",
          // Sin desplazar, la barra flota sobre la fotografía del héroe: ahí
          // manda la paleta oscura, sea cual sea el tema de la página.
          desplazado || abierto
            ? "cristal border-x-0 border-t-0 shadow-none"
            : "bg-gradient-to-b from-negro/70 to-transparent",
        ].join(" ")}
      >
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Logo />

          <div className="flex items-center gap-2">
            <SelectorIdioma className="hidden sm:flex" />

            {!autenticado && (
              <Link
                to="/login"
                className="hidden min-h-11 items-center gap-2 border border-hueso/35 px-5
                           font-sans text-xs uppercase tracking-[0.18em] text-hueso
                           transition-colors duration-200 hover:border-hueso hover:bg-hueso/10 sm:flex"
              >
                <Icono nombre="usuario" className="h-4 w-4" />
                {t("nav.entrar")}
              </Link>
            )}

            <button
              type="button"
              onClick={() => setAbierto((previo) => !previo)}
              aria-expanded={abierto}
              aria-controls="menu-completo"
              aria-label={abierto ? t("nav.cerrarMenu") : t("nav.menu")}
              className="flex h-11 w-11 cursor-pointer items-center justify-center text-hueso
                         transition-colors duration-200 hover:text-accion-claro"
            >
              <Icono nombre={abierto ? "cerrar" : "menu"} className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>

      {/* ------- Menú a pantalla completa · solo móvil y tableta ------- */}
      {abierto && (
        <div
          id="menu-completo"
          className="cristal-denso cristal fixed inset-0 z-30 overflow-y-auto border-0 pt-24 animate-aparecer lg:hidden"
        >
          <nav
            aria-label="Menú completo"
            className="mx-auto max-w-[1600px] px-5 pb-16 sm:px-8"
          >
            {autenticado && (
              <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border border-linea p-5">
                <div>
                  <p className="etiqueta text-accion-claro">Sesión activa · {rol}</p>
                  <p className="display mt-1 text-2xl text-hueso">
                    {usuario.nombre} {usuario.apellido}
                  </p>
                  <p className="mt-1 text-sm text-ceniza">{usuario.correo}</p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link
                    to={panel}
                    onClick={cerrarMenu}
                    className="flex min-h-11 items-center bg-accion-fondo px-5 font-sans text-xs
                               uppercase tracking-[0.14em] text-negro transition-colors
                               duration-200 hover:bg-accion-hondo"
                  >
                    {t("nav.panel")}
                  </Link>
                  <button
                    type="button"
                    onClick={salir}
                    className="flex min-h-11 cursor-pointer items-center border border-hueso/35
                               px-5 font-sans text-xs uppercase tracking-[0.14em] text-hueso
                               transition-colors duration-200 hover:border-hueso hover:bg-hueso/10"
                  >
                    {t("nav.salir")}
                  </button>
                </div>
              </div>
            )}

            {/* En móvil el selector de idioma no cabe en la barra: va aquí. */}
            <div className="flex items-center gap-3 pb-8 sm:hidden">
              <SelectorIdioma />
            </div>

            <ul className="border-t border-linea">
              {ENLACES.map((enlace) => (
                <li key={enlace.a} className="border-b border-linea">
                  <NavLink
                    to={enlace.a}
                    onClick={cerrarMenu}
                    className="display block py-6 text-4xl text-hueso transition-colors
                               duration-200 hover:text-accion-claro sm:text-6xl"
                  >
                    {t(enlace.clave)}
                  </NavLink>
                </li>
              ))}
            </ul>

            <ul className="mt-10 grid gap-1 sm:grid-cols-2">
              {[...FAMILIAS, AGENDAR].map((enlace) => (
                <li key={enlace.a}>
                  <Link
                    to={enlace.a}
                    onClick={cerrarMenu}
                    className="flex min-h-12 items-center gap-3 font-sans text-xs uppercase
                               tracking-[0.18em] text-ceniza transition-colors duration-200
                               hover:text-hueso"
                  >
                    <Icono nombre="derecha" className="h-4 w-4 text-accion" />
                    {t(enlace.clave)}
                  </Link>
                </li>
              ))}

              {!autenticado && (
                <li>
                  <Link
                    to="/login"
                    onClick={cerrarMenu}
                    className="flex min-h-12 items-center gap-3 font-sans text-xs uppercase
                               tracking-[0.18em] text-ceniza transition-colors duration-200
                               hover:text-hueso"
                  >
                    <Icono nombre="derecha" className="h-4 w-4 text-accion" />
                    {t("nav.entrar")}
                  </Link>
                </li>
              )}
            </ul>
          </nav>
        </div>
      )}
    </>
  );
}

export default Header;
