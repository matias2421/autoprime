import { useId, useState } from "react";
import Icono from "./Icono";

/**
 * Campo de texto reutilizable con etiqueta visible, validación en tiempo real,
 * mensaje de error accesible (role="alert") y contador de caracteres opcional.
 */
function Input({
  label,
  error = "",
  valido = false,
  ayuda = "",
  icono,
  type = "text",
  maxLength,
  mostrarContador = false,
  value = "",
  multilinea = false,
  filas = 5,
  className = "",
  ...props
}) {
  const id = useId();
  const [verPassword, setVerPassword] = useState(false);

  const idError = `${id}-error`;
  const idAyuda = `${id}-ayuda`;
  const esPassword = type === "password";
  const tipoFinal = esPassword && verPassword ? "text" : type;

  const descritoPor =
    [error ? idError : null, ayuda ? idAyuda : null].filter(Boolean).join(" ") ||
    undefined;

  const borde = error
    ? "border-accion focus:border-accion"
    : valido
      ? "border-exito/60 focus:border-hueso"
      : "border-linea focus:border-hueso";

  const relleno = [
    icono ? "pl-12" : "pl-4",
    esPassword || valido || error ? "pr-12" : "pr-4",
  ].join(" ");

  const clasesCampo = [
    "w-full min-h-14 border bg-grafito/55 backdrop-blur-md py-4 text-base text-hueso",
    "placeholder:text-plomo transition-colors duration-200",
    "focus:outline-none",
    borde,
    multilinea ? "px-4 resize-y" : relleno,
    className,
  ].join(" ");

  const Etiqueta = multilinea ? "textarea" : "input";

  return (
    <div className="w-full">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="etiqueta text-ceniza">
          {label}
        </label>
        {mostrarContador && maxLength ? (
          <span className="shrink-0 font-sans text-xs tabular-nums text-plomo">
            {String(value).length}/{maxLength}
          </span>
        ) : null}
      </div>

      <div className="relative">
        {icono && !multilinea && (
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-plomo">
            <Icono nombre={icono} />
          </span>
        )}

        <Etiqueta
          id={id}
          type={multilinea ? undefined : tipoFinal}
          rows={multilinea ? filas : undefined}
          maxLength={maxLength}
          value={value}
          aria-invalid={Boolean(error)}
          aria-describedby={descritoPor}
          className={clasesCampo}
          {...props}
        />

        {esPassword && (
          <button
            type="button"
            onClick={() => setVerPassword((previo) => !previo)}
            className="absolute right-0 top-1/2 flex h-12 w-12 -translate-y-1/2 cursor-pointer
                       items-center justify-center text-plomo transition-colors
                       duration-200 hover:text-hueso"
            aria-label={verPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
          >
            <Icono nombre={verPassword ? "ojoCerrado" : "ojo"} />
          </button>
        )}

        {!esPassword && !multilinea && valido && !error && (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-exito">
            <Icono nombre="check" />
          </span>
        )}

        {!esPassword && !multilinea && error && (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-accion-claro">
            <Icono nombre="alerta" />
          </span>
        )}
      </div>

      {/* El error se anuncia a lectores de pantalla y se muestra junto al campo */}
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

export default Input;
