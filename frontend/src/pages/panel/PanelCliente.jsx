import { useCallback, useState } from "react";
import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import { PanelLayout, Tarjeta, Aviso, Estado } from "../../components/panel/PanelLayout";
import { citasApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";

function fechaLarga(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Una cita futura y no cancelada sigue vigente. */
function esProxima(cita) {
  if (cita.estado === "cancelada" || cita.estado === "completada") return false;
  const [a, m, d] = cita.fecha.split("-").map(Number);
  const hoy = new Date();
  return new Date(a, m - 1, d) >= new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
}

/**
 * Panel de cliente (requisito 12).
 * Muestra los datos de la cuenta y las citas del usuario autenticado.
 */
function PanelCliente() {
  const { usuario } = useAuth();

  const [aviso, setAviso] = useState("");

  const obtener = useCallback(async () => {
    const [c, r] = await Promise.all([citasApi.listar(), citasApi.resumen()]);
    return { citas: c.citas, resumen: r.resumen };
  }, []);

  const { datos, cargando, error, setError, recargar: cargar } = useCarga(obtener);

  const citas = datos?.citas ?? [];
  const resumen = datos?.resumen ?? null;

  const cancelar = async (cita) => {
    setError("");
    try {
      await citasApi.cambiarEstado(cita.id, "cancelada");
      setAviso(`Cancelaste la cita #${cita.id}.`);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  };

  const proximas = citas.filter(esProxima);

  return (
    <PanelLayout
      etiqueta="Panel de cliente"
      titulo={`Hola, ${usuario.nombre}`}
      descripcion="Aquí ves tus citas agendadas y los datos de tu cuenta. Puedes cancelar una cita mientras no se haya completado."
      acciones={
        <Button to="/agendar">
          <Icono nombre="reloj" className="h-4 w-4" />
          Agendar cita
        </Button>
      }
    >
      {resumen && (
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Tarjeta titulo="Próximas" valor={proximas.length} icono="reloj" acento />
          <Tarjeta titulo="Confirmadas" valor={resumen.confirmada} icono="check" />
          <Tarjeta titulo="Completadas" valor={resumen.completada} icono="check" />
          <Tarjeta titulo="Canceladas" valor={resumen.cancelada} icono="cerrar" />
        </div>
      )}

      <div className="mt-10 grid gap-10 lg:grid-cols-[1.5fr_1fr] lg:gap-16">
        {/* ---------------------------- Mis citas ---------------------------- */}
        <div>
          <h2 className="display text-3xl text-hueso">Mis citas</h2>

          <div className="mt-4 space-y-3">
            {error && <Aviso tipo="error">{error}</Aviso>}
            {aviso && !error && <Aviso tipo="exito">{aviso}</Aviso>}
          </div>

          {cargando ? (
            <p className="mt-6 text-sm text-ceniza">Cargando tus citas...</p>
          ) : citas.length === 0 ? (
            <div className="cristal mt-6 p-8 text-center">
              <p className="text-sm text-ceniza">
                Todavía no tienes citas agendadas.
              </p>
              <Button to="/modelos" variante="contorno" className="mt-6">
                Ver el catálogo
              </Button>
            </div>
          ) : (
            <ul className="mt-6 space-y-3">
              {citas.map((c) => (
                <li key={c.id} className="cristal cristal-vivo reflejo alza p-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="etiqueta text-accion-claro">
                        Cita #{c.id} · {c.servicio}
                      </p>
                      <p className="display mt-2 text-2xl text-hueso">
                        {fechaLarga(c.fecha)}
                      </p>
                      <p className="mt-1 font-sans text-sm uppercase tracking-[0.1em] text-ceniza">
                        {c.hora.slice(0, 5)} · {c.duracionMin} minutos
                      </p>
                      {c.vehiculo && (
                        <p className="mt-2 text-sm text-ceniza">
                          Vehículo: <span className="text-hueso">{c.vehiculo}</span>
                        </p>
                      )}
                      {c.notas && <p className="mt-2 text-sm text-plomo">{c.notas}</p>}
                    </div>

                    <div className="flex flex-col items-end gap-3">
                      <Estado valor={c.estado} />
                      {["pendiente", "confirmada"].includes(c.estado) && (
                        <button
                          type="button"
                          onClick={() => cancelar(c)}
                          className="min-h-11 cursor-pointer border border-accion/40 px-3
                                     font-sans text-xs uppercase tracking-[0.12em]
                                     text-accion-claro transition-colors duration-200
                                     hover:bg-accion-fondo hover:text-hueso"
                        >
                          Cancelar
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* --------------------------- Mis datos --------------------------- */}
        <aside className="lg:sticky lg:top-28 lg:self-start">
          <h2 className="display text-3xl text-hueso">Mi cuenta</h2>
          <dl className="cristal mt-6 divide-y divide-linea">
            {[
              ["Nombre", `${usuario.nombre} ${usuario.apellido}`],
              ["Documento", `${usuario.tipoDocumento} ${usuario.numeroDocumento}`],
              ["Correo", usuario.correo],
              ["Teléfono", usuario.telefono],
              ["Dirección", usuario.direccion],
              ["Rol", usuario.rol],
            ].map(([titulo, dato]) => (
              <div key={titulo} className="p-4">
                <dt className="etiqueta text-plomo">{titulo}</dt>
                <dd className="mt-1 break-words text-sm text-hueso">{dato}</dd>
              </div>
            ))}
          </dl>

          <p className="mt-4 text-xs leading-relaxed text-plomo">
            ¿Necesitas corregir algún dato? Escríbenos y un asesor lo actualiza
            por ti.
          </p>
          <Button to="/contacto" variante="contorno" ancho className="mt-4">
            Contactar al concesionario
          </Button>
        </aside>
      </div>
    </PanelLayout>
  );
}

export default PanelCliente;
