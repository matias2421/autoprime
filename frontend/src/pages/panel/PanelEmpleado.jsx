import { useCallback, useState } from "react";
import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Select from "../../components/ui/Select";
import { PanelLayout, Tarjeta, Aviso, Estado } from "../../components/panel/PanelLayout";
import { citasApi, productosApi } from "../../api/cliente";
import { useCarga } from "../../hooks/useCarga";

const ESTADOS = [
  { valor: "pendiente", etiqueta: "Pendiente" },
  { valor: "confirmada", etiqueta: "Confirmada" },
  { valor: "completada", etiqueta: "Completada" },
  { valor: "cancelada", etiqueta: "Cancelada" },
];

function fechaLarga(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/**
 * Panel de empleado (requisito 11).
 * Atiende las citas agendadas y consulta el catalogo. No gestiona usuarios.
 */
function PanelEmpleado() {
  const [filtroEstado, setFiltroEstado] = useState("");
  const [aviso, setAviso] = useState("");

  const obtener = useCallback(async () => {
    const [c, r, p] = await Promise.all([
      citasApi.listar(filtroEstado ? { estado: filtroEstado } : {}),
      citasApi.resumen(),
      productosApi.listar(),
    ]);
    return { citas: c.citas, resumen: r.resumen, productos: p.productos };
  }, [filtroEstado]);

  const { datos, cargando, error, setError, recargar: cargar } = useCarga(obtener);

  const citas = datos?.citas ?? [];
  const resumen = datos?.resumen ?? null;
  const productos = datos?.productos ?? [];

  const cambiarEstado = async (cita, estado) => {
    setError("");
    try {
      await citasApi.cambiarEstado(cita.id, estado);
      setAviso(`La cita #${cita.id} quedó ${estado}.`);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <PanelLayout
      etiqueta="Panel de empleado"
      titulo="Citas del concesionario"
      descripcion="Confirma, completa o cancela las citas agendadas por los clientes. También puedes consultar el catálogo disponible."
      acciones={
        <Button variante="contorno" onClick={cargar}>
          <Icono nombre="reloj" className="h-4 w-4" />
          Actualizar
        </Button>
      }
    >
      {resumen && (
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Tarjeta titulo="Pendientes" valor={resumen.pendiente} icono="reloj" acento />
          <Tarjeta titulo="Confirmadas" valor={resumen.confirmada} icono="check" />
          <Tarjeta titulo="Completadas" valor={resumen.completada} icono="check" />
          <Tarjeta titulo="Canceladas" valor={resumen.cancelada} icono="cerrar" />
        </div>
      )}

      <div className="mt-10 max-w-xs">
        <Select
          label="Filtrar por estado"
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value)}
          placeholder="Todas las citas"
          opciones={ESTADOS}
        />
      </div>

      <div className="mt-6 space-y-3">
        {error && <Aviso tipo="error">{error}</Aviso>}
        {aviso && !error && <Aviso tipo="exito">{aviso}</Aviso>}
      </div>

      {/* ------------------------------ Citas ------------------------------ */}
      <div className="cristal mt-6 overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="border-b border-linea">
            <tr>
              {["Cita", "Cliente", "Servicio", "Vehículo", "Estado", "Acciones"].map((h) => (
                <th key={h} scope="col" className="etiqueta px-4 py-4 text-plomo">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-linea">
            {cargando ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ceniza">
                  Cargando citas...
                </td>
              </tr>
            ) : citas.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ceniza">
                  No hay citas registradas con ese filtro.
                </td>
              </tr>
            ) : (
              citas.map((c) => (
                <tr key={c.id} className="transition-colors duration-200 hover:bg-carbon">
                  <td className="px-4 py-4">
                    <p className="font-sans text-sm uppercase tracking-[0.08em] text-hueso">
                      #{c.id} · {c.hora.slice(0, 5)}
                    </p>
                    <p className="text-xs text-plomo">{fechaLarga(c.fecha)}</p>
                  </td>
                  <td className="px-4 py-4">
                    <p className="text-hueso">{c.cliente}</p>
                    <p className="text-xs text-plomo">{c.clienteCorreo}</p>
                    <p className="text-xs text-plomo">{c.clienteTelefono}</p>
                  </td>
                  <td className="px-4 py-4 text-ceniza">
                    {c.servicio}
                    <span className="block text-xs text-plomo">{c.duracionMin} min</span>
                  </td>
                  <td className="px-4 py-4 text-ceniza">
                    {c.vehiculo || <span className="text-plomo">Sin vehículo</span>}
                  </td>
                  <td className="px-4 py-4">
                    <Estado valor={c.estado} />
                    {c.notas && (
                      <p className="mt-1 max-w-[16rem] text-xs text-plomo">{c.notas}</p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-2">
                      {c.estado === "pendiente" && (
                        <button
                          type="button"
                          onClick={() => cambiarEstado(c, "confirmada")}
                          className="min-h-11 cursor-pointer border border-exito/50 px-3 font-sans
                                     text-xs uppercase tracking-[0.12em] text-exito transition-colors
                                     duration-200 hover:bg-exito hover:text-negro"
                        >
                          Confirmar
                        </button>
                      )}
                      {["pendiente", "confirmada"].includes(c.estado) && (
                        <>
                          <button
                            type="button"
                            onClick={() => cambiarEstado(c, "completada")}
                            className="min-h-11 cursor-pointer border border-linea px-3 font-sans
                                       text-xs uppercase tracking-[0.12em] text-hueso transition-colors
                                       duration-200 hover:border-hueso"
                          >
                            Completar
                          </button>
                          <button
                            type="button"
                            onClick={() => cambiarEstado(c, "cancelada")}
                            className="min-h-11 cursor-pointer border border-accion/40 px-3 font-sans
                                       text-xs uppercase tracking-[0.12em] text-accion-claro
                                       transition-colors duration-200 hover:bg-accion-fondo hover:text-hueso"
                          >
                            Cancelar
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ---------------------------- Catálogo ---------------------------- */}
      <h2 className="display mt-16 text-3xl text-hueso">Catálogo disponible</h2>
      <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {productos.map((p) => (
          <li key={p.id} className="cristal cristal-vivo reflejo alza p-5">
            <p className="etiqueta text-plomo">{p.marca}</p>
            <h3 className="display mt-1 text-xl text-hueso">{p.modelo}</h3>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="font-sans text-xs uppercase tracking-[0.12em] text-ceniza">
                {p.specs.potencia} · {p.anio}
              </span>
              <Estado valor={p.estado} />
            </div>
          </li>
        ))}
      </ul>
    </PanelLayout>
  );
}

export default PanelEmpleado;
