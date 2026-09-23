import { useId } from "react";
import Icono from "./Icono";

/**
 * Casilla de verificación reutilizable. El área táctil abarca toda la
 * etiqueta para cumplir el mínimo de 44x44 px.
 *
 * Acepta `error` para poder marcarse igual que un campo de texto. Sin eso,
 * una casilla obligatoria sin marcar era el único fallo del formulario que
 * no se veía en ninguna parte: todo salía en verde mientras el aviso pedía
 * revisar «los campos en rojo».
 */
function Checkbox({ label, checked = false, error = "", className = "", ...props }) {
  const id = useId();

  // El mismo `border-accion` que usa Input para marcar error: dos tonos
  // distintos para decir lo mismo solo confunden.
  const borde = error
    ? "border-accion"
    : "border-linea checked:border-accion";

  return (
    <label
      htmlFor={id}
      className={[
        "flex min-h-11 cursor-pointer select-none items-center gap-3 text-sm",
        error ? "text-accion-claro" : "text-ceniza",
        className,
      ].join(" ")}
    >
      <span className="relative flex h-5 w-5 shrink-0 items-center justify-center">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          aria-invalid={Boolean(error)}
          className={`peer h-5 w-5 cursor-pointer appearance-none border
                     bg-carbon transition-colors duration-200
                     checked:bg-accion focus-visible:outline-2
                     focus-visible:outline-offset-3 focus-visible:outline-accion-claro
                     ${borde}`}
          {...props}
        />
        <Icono
          nombre="check"
          className="pointer-events-none absolute h-3.5 w-3.5 text-hueso opacity-0
                     transition-opacity duration-200 peer-checked:opacity-100"
        />
      </span>
      {label}
    </label>
  );
}

export default Checkbox;
