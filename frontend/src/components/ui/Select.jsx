import { useId } from "react";
import Icono from "./Icono";

/**
 * Lista desplegable reutilizable, con la misma anatomía visual y de
 * accesibilidad que <Input>.
 */
function Select({
  label,
  opciones = [],
  error = "",
  valido = false,
  ayuda = "",
  placeholder = "Selecciona una opción",
  className = "",
  ...props
}) {
  const id = useId();
  const idError = `${id}-error`;
  const idAyuda = `${id}-ayuda`;

  const descritoPor =
    [error ? idError : null, ayuda ? idAyuda : null].filter(Boolean).join(" ") ||
    undefined;

  const borde = error
    ? "border-accion focus:border-accion"
    : valido
      ? "border-exito/60 focus:border-hueso"
      : "border-linea focus:border-hueso";

  return (
    <div className="w-full">
      <label htmlFor={id} className="etiqueta mb-2 block text-ceniza">
        {label}
      </label>

      <div className="relative">
        <select
          id={id}
          aria-invalid={Boolean(error)}
          aria-describedby={descritoPor}
          className={[
            "w-full min-h-14 cursor-pointer appearance-none border bg-carbon",
            "py-4 pl-4 pr-12 text-base text-hueso transition-colors duration-200",
            "focus:outline-none",
            borde,
            className,
          ].join(" ")}
          {...props}
        >
          <option value="" className="bg-carbon">
            {placeholder}
          </option>
          {opciones.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor} className="bg-carbon">
              {opcion.etiqueta}
            </option>
          ))}
        </select>

        <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-plomo">
          <Icono nombre="chevronAbajo" />
        </span>
      </div>

      {error ? (
        <p
          id={idError}
          role="alert"
          className="mt-2 flex items-start gap-2 text-sm font-medium text-accion-claro"
        >
          <Icono nombre="alerta" className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : ayuda ? (
        <p id={idAyuda} className="mt-2 text-sm text-plomo">
          {ayuda}
        </p>
      ) : null}
    </div>
  );
}

export default Select;
