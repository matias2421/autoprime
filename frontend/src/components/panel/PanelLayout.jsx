import { Link } from "react-router-dom";

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

/**
 * Tarjeta de cifra para el resumen de cada panel.
 *
 * Tres cosas opcionales, y las tres existen por un motivo concreto:
 *
 * `variacion` — una cifra sola no dice si el periodo fue bueno. «$50 mil M»
 * solo significa algo al lado de lo que se hizo antes.
 *
 * `detalle` — «7 ventas por cobrar» no dice cuanto dinero es eso, que es la
 * pregunta siguiente y obligaba a ir a la tabla a sumarlas.
 *
 * `enlace` — una cifra que pide una accion tiene que llevar a donde se hace.
 * Con «5 PQR abiertas» y sin enlace, hay que ir a buscar el menu.
 */
function Tarjeta({ titulo, valor, icono, acento = false, variacion, detalle, enlace }) {
  const contenido = (
    <>
      <div className="flex items-center justify-between gap-3">
        <p className="etiqueta text-plomo">{titulo}</p>
        {icono && (
          <Icono
            nombre={icono}
            className={`h-4 w-4 ${acento ? "text-accion" : "text-plomo"}`}
          />
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="display text-3xl text-hueso">{valor}</p>
        {variacion && (
          <span
            className={`font-sans text-xs tracking-[0.08em] ${
              variacion.sube ? "text-exito" : "text-accion-claro"
            }`}
          >
            {/* El signo va en el texto ademas del color: quien no distingue
                el verde del azul se quedaria sin saber si sube o baja. */}
            {variacion.texto}
          </span>
        )}
      </div>

      {detalle && (
        <p className="mt-1 font-sans text-xs text-plomo">{detalle}</p>
      )}
    </>
  );

  const clases = "cristal cristal-vivo reflejo alza block p-5";

  if (enlace) {
    return (
      <Link
        to={enlace}
        className={`${clases} transition-colors hover:border-accion/40
                    focus-visible:outline-2 focus-visible:outline-offset-2
                    focus-visible:outline-accion-claro motion-reduce:transition-none`}
      >
        {contenido}
      </Link>
    );
  }

  return <div className={clases}>{contenido}</div>;
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

    // Quinto avance: ventas, facturas y PQR.
    //
    // El ambar no es decorativo: marca lo que espera una accion de alguien
    // -una venta por cobrar, una PQR sin responder- y es lo que hace que la
    // bandeja se lea de un vistazo en vez de fila por fila.
    pagada: "border-exito/50 text-exito",
    anulada: "border-plomo text-plomo",
    emitida: "border-exito/50 text-exito",
    en_proceso: "border-amber-500/50 text-amber-500",
    respondida: "border-exito/50 text-exito",
    cerrada: "border-plomo text-plomo",
  };

  // `en_proceso` se guarda con guion bajo porque asi esta en la base; en
  // pantalla se lee mejor con espacio.
  const texto = String(valor || "").replace(/_/g, " ");

  return (
    <span
      className={`inline-flex items-center border px-2.5 py-1 font-sans text-xs
                  uppercase tracking-[0.12em] ${colores[valor] || "border-linea text-ceniza"}`}
    >
      {texto}
    </span>
  );
}

export { PanelLayout, Tarjeta, Aviso, Estado };
export default PanelLayout;
