import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import Icono from "./ui/Icono";
import SelectorIdioma from "./SelectorIdioma";
import { useAuth } from "../hooks/useAuth";
import { useBloqueoScroll } from "../hooks/useBloqueoScroll";
import { useIdioma } from "../hooks/useIdioma";

/* Las listas guardan la CLAVE del diccionario, no el texto ya resuelto. */
const ENLACES = [
  { a: "/modelos", clave: "nav.modelos" },
  { a: "/quienes-somos", clave: "nav.quienesSomos" },
  { a: "/contacto", clave: "nav.contacto" },
];

const SECUNDARIOS = [
  { a: "/modelos?familia=gama", clave: "fam.gama" },
  { a: "/modelos?familia=edicion", clave: "fam.edicion" },
  { a: "/modelos?familia=coleccion", clave: "fam.coleccion" },
  { a: "/agendar", clave: "nav.agendar" },
];

/** Ruta del panel que corresponde a cada rol. */
const PANEL_POR_ROL = {
  administrador: "/panel/admin",
  empleado: "/panel/empleado",
  cliente: "/panel/cliente",
};

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

  // El encabezado pasa de transparente a solido al bajar.
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

  const claseEnlace = ({ isActive }) =>
    [
      "flex min-h-11 items-center font-sans text-xs uppercase tracking-[0.18em]",
      "transition-colors duration-200 hover:text-hueso",
      isActive ? "text-hueso" : "text-ceniza",
    ].join(" ");

  return (
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-60
                   focus:bg-accion-fondo focus:px-5 focus:py-3 focus:font-sans focus:text-xs
                   focus:uppercase focus:tracking-[0.18em] focus:text-negro"
      >
        {t("nav.saltar")}
      </a>

      <header
        className={[
          "fixed inset-x-0 top-0 z-40 transition-colors duration-300",
          // Sin desplazar la cabecera flota sobre la fotografía del héroe:
          // ahí manda la paleta oscura, sea cual sea el tema de la página.
          desplazado || abierto
            ? "cristal border-x-0 border-t-0 shadow-none"
            : "bg-gradient-to-b from-negro/70 to-transparent",
        ].join(" ")}
      >
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Logo />

          <nav aria-label="Navegación principal" className="hidden lg:block">
            <ul className="flex items-center gap-9">
              {ENLACES.map((enlace) => (
                <li key={enlace.a}>
                  <NavLink to={enlace.a} className={claseEnlace}>
                    {t(enlace.clave)}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className="flex items-center gap-2">
            {/* Idioma: a la vista en escritorio; en movil va en el menu. */}
            <SelectorIdioma className="hidden sm:flex" />

            {autenticado ? (
              <>
                {/* Requisito 13: el usuario autenticado se identifica en el Navbar */}
                <Link
                  to={panel}
                  className="hidden min-h-11 items-center gap-2 border border-hueso/35 px-4
                             font-sans text-xs uppercase tracking-[0.14em] text-hueso
                             transition-colors duration-200 hover:border-hueso hover:bg-hueso/10 sm:flex"
                >
                  <Icono nombre="usuario" className="h-4 w-4 text-accion" />
                  <span>
                    {t("nav.bienvenido")}, {usuario.nombre}
                  </span>
                  <span className="text-plomo">·</span>
                  <span className="text-ceniza">{rol}</span>
                </Link>

                <button
                  type="button"
                  onClick={salir}
                  className="hidden min-h-11 cursor-pointer items-center px-3 font-sans
                             text-xs uppercase tracking-[0.14em] text-ceniza transition-colors
                             duration-200 hover:text-accion-claro sm:flex"
                >
                  {t("nav.salir")}
                </button>
              </>
            ) : (
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

      {/* ------------------- Menú a pantalla completa ------------------- */}
      {abierto && (
        <div
          id="menu-completo"
          className="cristal-denso cristal fixed inset-0 z-30 overflow-y-auto border-0 pt-24 animate-aparecer"
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

            {/* En movil el selector de idioma no cabe en la barra: va aqui. */}
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

            <ul className="mt-10 grid gap-1 sm:grid-cols-2 lg:grid-cols-4">
              {SECUNDARIOS.map((enlace) => (
                <li key={enlace.texto}>
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
                    Iniciar sesión
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
