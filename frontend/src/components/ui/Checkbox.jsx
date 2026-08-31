import { useId } from "react";
import Icono from "./Icono";

/**
 * Casilla de verificación reutilizable. El área táctil abarca toda la
 * etiqueta para cumplir el mínimo de 44x44 px.
 */
function Checkbox({ label, checked = false, className = "", ...props }) {
  const id = useId();

  return (
    <label
      htmlFor={id}
      className={[
        "flex min-h-11 cursor-pointer select-none items-center gap-3 text-sm text-ceniza",
        className,
      ].join(" ")}
    >
      <span className="relative flex h-5 w-5 shrink-0 items-center justify-center">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          className="peer h-5 w-5 cursor-pointer appearance-none border border-linea
                     bg-carbon transition-colors duration-200 checked:border-accion
                     checked:bg-accion focus-visible:outline-2
                     focus-visible:outline-offset-3 focus-visible:outline-accion-claro"
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
