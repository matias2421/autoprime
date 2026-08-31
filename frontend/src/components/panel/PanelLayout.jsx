import Icono from "../ui/Icono";
import { useAuth } from "../../hooks/useAuth";

/** Cabecera comun a los tres paneles. */
function PanelLayout({ titulo, descripcion, etiqueta, acciones, children }) {
  const { usuario, rol } = useAuth();

  return (
    <section className="mx-auto max-w-[1600px] px-5 pb-24 pt-28 sm:px-8 lg:pt-32">
      <div className="flex flex-wrap items-end justify-between gap-6 border-b border-linea pb-8">
        <div>
          <p className="etiqueta text-accion-claro">{etiqueta}</p>
          <h1 className="display mt-3 text-4xl text-hueso sm:text-6xl">{titulo}</h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-ceniza">
            {descripcion}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <div className="cristal px-4 py-3">
            <p className="etiqueta text-plomo">Sesión</p>
            <p className="mt-1 text-sm text-hueso">
              {usuario.nombre} {usuario.apellido}
            </p>
            <p className="font-sans text-xs uppercase tracking-[0.14em] text-accion-claro">
              {rol}
            </p>
          </div>
          {acciones}
        </div>
      </div>

      {children}
    </section>
  );
}

/** Tarjeta de conteo para el resumen de cada panel. */
function Tarjeta({ titulo, valor, icono, acento = false }) {
  return (
    <div className="cristal cristal-vivo reflejo alza p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="etiqueta text-plomo">{titulo}</p>
        {icono && (
          <Icono
            nombre={icono}
            className={`h-4 w-4 ${acento ? "text-accion" : "text-plomo"}`}
          />
        )}
      </div>
      <p className="display mt-2 text-3xl text-hueso">{valor}</p>
    </div>
  );
}

/** Mensaje de estado (cargando, error o vacio) dentro de un panel. */
function Aviso({ tipo = "info", children }) {
  const estilos = {
    info: "border-linea text-ceniza",
    error: "border-accion/40 bg-accion/10 text-accion-claro",
    exito: "border-exito/40 bg-exito/10 text-exito",
  };

  return (
    <div
      role={tipo === "error" ? "alert" : undefined}
      className={`flex items-start gap-3 border p-4 text-sm ${estilos[tipo]}`}
    >
      {tipo !== "info" && (
        <Icono
          nombre={tipo === "error" ? "alerta" : "check"}
          className="mt-0.5 h-5 w-5 shrink-0"
        />
      )}
      {children}
    </div>
  );
}

/** Etiqueta de estado con color segun el valor. */
function Estado({ valor }) {
  const colores = {
    activo: "border-exito/50 text-exito",
    inactivo: "border-plomo text-plomo",
    pendiente: "border-amber-500/50 text-amber-500",
    confirmada: "border-exito/50 text-exito",
    cancelada: "border-accion/50 text-accion-claro",
    completada: "border-hueso/40 text-hueso",
    disponible: "border-exito/50 text-exito",
    vendido: "border-plomo text-plomo",
  };

  return (
    <span
      className={`inline-flex items-center border px-2.5 py-1 font-sans text-xs
                  uppercase tracking-[0.12em] ${colores[valor] || "border-linea text-ceniza"}`}
    >
      {valor}
    </span>
  );
}

export { PanelLayout, Tarjeta, Aviso, Estado };
export default PanelLayout;
