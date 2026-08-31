import { useCallback, useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import Icono from "./Icono";
import { useBloqueoScroll } from "../../hooks/useBloqueoScroll";

const FOCUSABLES =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Ventana modal reutilizable y accesible.
 *
 * - Se cierra con la tecla Escape, con el botón "X" o pulsando fuera.
 * - Bloquea el scroll del fondo mientras está abierta.
 * - Mantiene el foco dentro del diálogo y lo devuelve al cerrar.
 */
function Modal({ abierto, alCerrar, titulo, descripcion, children, ancho = "max-w-2xl" }) {
  const id = useId();
  const cajaRef = useRef(null);
  const focoPrevioRef = useRef(null);

  const manejarTeclado = useCallback(
    (evento) => {
      if (evento.key === "Escape") {
        evento.stopPropagation();
        alCerrar();
        return;
      }

      if (evento.key !== "Tab" || !cajaRef.current) return;

      // Trampa de foco: el tabulador no debe salir del diálogo.
      const elementos = Array.from(
        cajaRef.current.querySelectorAll(FOCUSABLES)
      ).filter((el) => el.offsetParent !== null);
      if (elementos.length === 0) return;

      const primero = elementos[0];
      const ultimo = elementos[elementos.length - 1];

      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault();
        primero.focus();
      }
    },
    [alCerrar]
  );

  /**
   * El efecto de abajo NO puede depender de `manejarTeclado`.
   *
   * `manejarTeclado` se recrea cada vez que cambia `alCerrar`, y `alCerrar`
   * suele llegar como una funcion nueva en cada render del padre. Si estuviera
   * en las dependencias, cada tecla que se escribe en un campo del formulario
   * volveria a ejecutar el efecto; su limpieza devuelve el foco al elemento
   * anterior y el usuario perderia el campo tras cada caracter.
   *
   * La solucion es guardar siempre la version mas reciente en un ref y que el
   * efecto dependa unicamente de `abierto`.
   */
  // El fondo no se desplaza mientras el diálogo está abierto.
  useBloqueoScroll("modal", abierto);

  const manejarTecladoRef = useRef(manejarTeclado);

  useEffect(() => {
    manejarTecladoRef.current = manejarTeclado;
  }, [manejarTeclado]);

  useEffect(() => {
    if (!abierto) return undefined;

    focoPrevioRef.current = document.activeElement;

    const temporizador = window.setTimeout(() => {
      const primero = cajaRef.current?.querySelector(FOCUSABLES);
      (primero ?? cajaRef.current)?.focus();
    }, 0);

    const alTeclado = (evento) => manejarTecladoRef.current(evento);
    document.addEventListener("keydown", alTeclado);

    return () => {
      window.clearTimeout(temporizador);
      document.removeEventListener("keydown", alTeclado);
      focoPrevioRef.current?.focus?.();
    };
  }, [abierto]);

  if (!abierto) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto
                 bg-negro/80 p-4 backdrop-blur-md sm:items-center sm:p-6 animate-aparecer"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget) alCerrar();
      }}
    >
      <div
        ref={cajaRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-titulo`}
        aria-describedby={descripcion ? `${id}-desc` : undefined}
        tabIndex={-1}
        className={`cristal my-auto w-full ${ancho} animate-subir`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-linea p-6 sm:p-8 sm:pb-6">
          <div>
            <h2 id={`${id}-titulo`} className="display text-3xl text-hueso sm:text-4xl">
              {titulo}
            </h2>
            {descripcion && (
              <p id={`${id}-desc`} className="mt-2 text-sm text-ceniza">
                {descripcion}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={alCerrar}
            aria-label="Cerrar ventana"
            className="flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center
                       border border-linea text-ceniza transition-colors duration-200
                       hover:border-hueso hover:text-hueso"
          >
            <Icono nombre="cerrar" />
          </button>
        </div>

        <div className="p-6 sm:p-8">{children}</div>
      </div>
    </div>,
    document.body
  );
}

export default Modal;
