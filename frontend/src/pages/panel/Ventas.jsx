import { useCallback, useState } from "react";

import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import Input from "../../components/ui/Input";
import Paginador from "../../components/panel/Paginador";
import { Tabla, Celda } from "../../components/panel/Tabla";
import { PanelLayout, Aviso, Estado } from "../../components/panel/PanelLayout";
import {
  facturasApi,
  productosApi,
  serviciosApi,
  usuariosApi,
  ventasApi,
} from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";
import { fechaHora, numero, pesos } from "../../utils/formato";

/**
 * Ventas.
 *
 * Una pantalla para los dos casos, porque es el mismo recurso visto desde dos
 * lados: el personal registra y gestiona, un cliente consulta lo suyo. El
 * backend ya filtra por rol, así que aquí solo cambia qué acciones se ofrecen.
 */

const ESTADOS = [
  { valor: "", etiqueta: "Todos los estados" },
  { valor: "pendiente", etiqueta: "Pendientes" },
  { valor: "pagada", etiqueta: "Pagadas" },
  { valor: "anulada", etiqueta: "Anuladas" },
];

/* ------------------------------------------------------------------ */
/*  Formulario de venta                                               */
/* ------------------------------------------------------------------ */

function FormularioVenta({ abierto, onCerrar, onGuardado, onError }) {
  const [lineas, setLineas] = useState([{ tipo: "producto", id: "", cantidad: 1 }]);
  const [clienteId, setClienteId] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [notas, setNotas] = useState("");
  const [guardando, setGuardando] = useState(false);

  const obtener = useCallback(async () => {
    const [cat, ser, cli] = await Promise.all([
      productosApi.listar(),
      serviciosApi.listar(),
      usuariosApi.clientes(),
    ]);
    return {
      productos: cat.productos.filter((p) => p.estado === "disponible"),
      servicios: ser.servicios,
      clientes: cli.clientes,
    };
  }, []);

  const { datos, cargando } = useCarga(obtener);

  const productos = datos?.productos ?? [];
  const servicios = datos?.servicios ?? [];
  const clientes = (datos?.clientes ?? []).filter((c) => {
    if (!busqueda.trim()) return true;
    const texto = `${c.nombre} ${c.apellido} ${c.documento} ${c.correo}`.toLowerCase();
    return texto.includes(busqueda.trim().toLowerCase());
  });

  const cambiarLinea = (indice, cambios) =>
    setLineas((previas) =>
      previas.map((l, i) => (i === indice ? { ...l, ...cambios } : l))
    );

  const anadirLinea = () =>
    setLineas((previas) => [...previas, { tipo: "servicio", id: "", cantidad: 1 }]);

  const quitarLinea = (indice) =>
    setLineas((previas) => previas.filter((_, i) => i !== indice));

  /*
   * El total se calcula aquí solo para que se vea antes de confirmar. El que
   * vale es el que devuelve el servidor: los precios los pone el catálogo en
   * el momento de vender, no este formulario. Si alguien manipulara estos
   * números, el backend los ignoraría igual.
   */
  const estimado = lineas.reduce((suma, l) => {
    if (!l.id) return suma;
    const fuente = l.tipo === "producto" ? productos : servicios;
    const elemento = fuente.find((e) => String(e.id) === String(l.id));
    return suma + (elemento?.precio ?? 0) * (Number(l.cantidad) || 1);
  }, 0);

  const iva = Math.round(estimado * 0.19);

  const enviar = async (evento) => {
    evento.preventDefault();
    onError("");

    const utiles = lineas.filter((l) => l.id);
    if (utiles.length === 0) {
      onError("Agrega al menos una línea a la venta.");
      return;
    }

    setGuardando(true);
    try {
      await ventasApi.crear({
        usuarioId: clienteId ? Number(clienteId) : undefined,
        notas: notas.trim() || undefined,
        lineas: utiles.map((l) => ({
          [l.tipo === "producto" ? "productoId" : "servicioId"]: Number(l.id),
          cantidad: Number(l.cantidad) || 1,
        })),
      });
      setLineas([{ tipo: "producto", id: "", cantidad: 1 }]);
      setClienteId("");
      setNotas("");
      onGuardado();
    } catch (fallo) {
      onError(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Modal
      abierto={abierto}
      alCerrar={onCerrar}
      titulo="Registrar una venta"
      descripcion="El precio de cada linea lo pone el catalogo al registrar la venta, no este formulario."
    >
      <form onSubmit={enviar} className="space-y-6">
        {cargando && <p className="text-sm text-ceniza">Cargando catálogo…</p>}

        <div className="space-y-3">
          <Input
            label="Buscar cliente"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Nombre, documento o correo"
          />
          <Select
            label="Comprador"
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value)}
            ayuda="Sin elegir, la venta queda a tu nombre."
            placeholder="— A mi nombre —"
            opciones={clientes.map((c) => ({
              valor: String(c.id),
              etiqueta: `${c.nombre} ${c.apellido} · ${c.documento}`,
            }))}
          />
        </div>

        <fieldset className="space-y-4 border-t border-linea pt-5">
          <legend className="etiqueta text-plomo">Líneas</legend>

          {lineas.map((linea, indice) => {
            const fuente = linea.tipo === "producto" ? productos : servicios;
            return (
              <div
                key={indice}
                className="grid gap-3 border border-linea p-4 sm:grid-cols-[auto_1fr_auto_auto]"
              >
                <Select
                  label="Tipo"
                  value={linea.tipo}
                  onChange={(e) =>
                    cambiarLinea(indice, { tipo: e.target.value, id: "" })
                  }
                  placeholder="— Elige —"
                  opciones={[
                    { valor: "producto", etiqueta: "Vehículo" },
                    { valor: "servicio", etiqueta: "Servicio" },
                  ]}
                />

                <Select
                  label={linea.tipo === "producto" ? "Vehículo" : "Servicio"}
                  value={linea.id}
                  onChange={(e) => cambiarLinea(indice, { id: e.target.value })}
                  placeholder="— Elige —"
                  opciones={fuente.map((e) => ({
                      valor: String(e.id),
                      etiqueta:
                        linea.tipo === "producto"
                          ? `${e.marca} ${e.modelo} · ${
                              e.precio ? pesos(e.precio) : "bajo consulta"
                            }`
                          : `${e.nombre} · ${e.precio ? pesos(e.precio) : "sin costo"}`,
                  }))}
                />

                <Input
                  label="Cant."
                  type="number"
                  min="1"
                  max="99"
                  value={String(linea.cantidad)}
                  onChange={(e) =>
                    cambiarLinea(indice, { cantidad: e.target.value })
                  }
                  className="w-24"
                />

                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={() => quitarLinea(indice)}
                    disabled={lineas.length === 1}
                    aria-label={`Quitar la línea ${indice + 1}`}
                    className="inline-flex h-11 w-11 items-center justify-center
                               border border-trazo text-ceniza hover:border-hueso
                               hover:text-hueso focus-visible:outline-2
                               focus-visible:outline-offset-2
                               focus-visible:outline-accion-claro
                               disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Icono nombre="cerrar" className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}

          <Button variante="texto" tamano="sm" onClick={anadirLinea}>
            + Agregar línea
          </Button>
        </fieldset>

        <Input
          label="Notas (opcional)"
          value={notas}
          onChange={(e) => setNotas(e.target.value)}
          maxLength={300}
        />

        <div className="border-t border-linea pt-5">
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between text-ceniza">
              <dt>Subtotal estimado</dt>
              <dd className="tabular-nums">{pesos(estimado)}</dd>
            </div>
            <div className="flex justify-between text-ceniza">
              <dt>IVA (19%)</dt>
              <dd className="tabular-nums">{pesos(iva)}</dd>
            </div>
            <div className="flex justify-between border-t border-linea pt-2 text-hueso">
              <dt className="font-sans uppercase tracking-[0.12em]">Total</dt>
              <dd className="tabular-nums text-lg">{pesos(estimado + iva)}</dd>
            </div>
          </dl>
          <p className="mt-2 text-xs text-plomo">
            El importe definitivo lo calcula el servidor con los precios del
            catálogo en el momento de registrar la venta.
          </p>
        </div>

        <div className="flex flex-wrap justify-end gap-3">
          <Button variante="contorno" onClick={onCerrar}>
            Cancelar
          </Button>
          <Button type="submit" cargando={guardando}>
            Registrar venta
          </Button>
        </div>
      </form>
    </Modal>
  );
}

/* ------------------------------------------------------------------ */
/*  Pantalla                                                          */
/* ------------------------------------------------------------------ */

function Ventas() {
  const { rol } = useAuth();
  const esPersonal = rol === "administrador" || rol === "empleado";
  const esAdmin = rol === "administrador";

  const [estado, setEstado] = useState("");
  const [pagina, setPagina] = useState(1);
  const [formulario, setFormulario] = useState(false);
  const [aviso, setAviso] = useState("");

  const obtener = useCallback(
    () => ventasApi.listar({ estado, pagina, porPagina: 20 }),
    [estado, pagina]
  );

  const { datos, cargando, error, setError, recargar } = useCarga(obtener);

  const ventas = datos?.ventas ?? [];

  const accion = async (tarea, mensaje) => {
    setError("");
    setAviso("");
    try {
      await tarea();
      setAviso(mensaje);
      recargar();
    } catch (fallo) {
      setError(fallo.message);
    }
  };

  const columnas = [
    { clave: "numero", titulo: "Número" },
    { clave: "fecha", titulo: "Fecha" },
    ...(esPersonal ? [{ clave: "cliente", titulo: "Cliente" }] : []),
    { clave: "lineas", titulo: "Líneas", alineacion: "centro" },
    { clave: "total", titulo: "Total", alineacion: "derecha" },
    { clave: "estado", titulo: "Estado" },
    { clave: "factura", titulo: "Factura" },
    { clave: "acciones", titulo: "", alineacion: "derecha" },
  ];

  return (
    <PanelLayout
      etiqueta={esPersonal ? "Gestión comercial" : "Mis compras"}
      titulo="Ventas"
      descripcion={
        esPersonal
          ? "Registra ventas de mostrador, marca las que se cobran y emite su factura. Anular una venta devuelve el vehículo al catálogo."
          : "El historial de lo que has comprado, con su factura descargable."
      }
      acciones={
        esPersonal && (
          <Button onClick={() => setFormulario(true)}>
            <Icono nombre="etiqueta" className="h-4 w-4" />
            Registrar venta
          </Button>
        )
      }
    >
      <div className="mt-8 flex flex-wrap items-end gap-4">
        <Select
          label="Estado"
          value={estado}
          onChange={(e) => {
            setEstado(e.target.value);
            setPagina(1);
          }}
          placeholder="Todos los estados"
          opciones={ESTADOS.filter((e) => e.valor).map((e) => ({
            valor: e.valor,
            etiqueta: e.etiqueta,
          }))}
          className="w-56"
        />
        <Button variante="texto" tamano="sm" to="/panel/tablero">
          Ver el tablero
        </Button>
      </div>

      {error && (
        <div className="mt-6">
          <Aviso tipo="error">{error}</Aviso>
        </div>
      )}
      {aviso && (
        <div className="mt-6">
          <Aviso tipo="exito">{aviso}</Aviso>
        </div>
      )}

      <div className="mt-6">
        <Tabla
          columnas={columnas}
          filas={ventas}
          cargando={cargando}
          vacio={
            esPersonal
              ? "Todavía no hay ventas registradas. Usa «Registrar venta» para crear la primera."
              : "Todavía no has comprado nada en AutoPrime."
          }
          pie={<Paginador pagina={datos?.pagina} onCambiar={setPagina} />}
          fila={(v) => (
            <>
              <Celda className="font-sans text-hueso">{v.numero}</Celda>
              <Celda>{fechaHora(v.fecha)}</Celda>
              {esPersonal && <Celda>{v.cliente ?? "—"}</Celda>}
              <Celda alineacion="centro">{numero(v.lineas?.length ?? 0)}</Celda>
              <Celda alineacion="derecha" className="text-hueso">
                {pesos(v.total)}
              </Celda>
              <Celda>
                <Estado valor={v.estado} />
              </Celda>
              <Celda>
                {v.facturaNumero ? (
                  <span className="font-sans text-xs text-accion-claro">
                    {v.facturaNumero}
                  </span>
                ) : (
                  <span className="text-plomo">—</span>
                )}
              </Celda>
              <Celda alineacion="derecha">
                <div className="flex flex-wrap items-center justify-end gap-2">
                  {esPersonal && v.estado === "pendiente" && (
                    <Button
                      variante="texto"
                      tamano="sm"
                      onClick={() =>
                        accion(
                          () => ventasApi.cambiarEstado(v.id, "pagada"),
                          `Venta ${v.numero} marcada como pagada.`
                        )
                      }
                    >
                      Cobrar
                    </Button>
                  )}

                  {esPersonal && !v.facturaNumero && v.estado !== "anulada" && (
                    <Button
                      variante="texto"
                      tamano="sm"
                      onClick={() =>
                        accion(
                          () => facturasApi.emitir(v.id),
                          `Factura emitida para la venta ${v.numero}.`
                        )
                      }
                    >
                      Facturar
                    </Button>
                  )}

                  {esPersonal && v.estado !== "anulada" && (
                    <Button
                      variante="texto"
                      tamano="sm"
                      onClick={() =>
                        accion(
                          () => ventasApi.cambiarEstado(v.id, "anulada"),
                          `Venta ${v.numero} anulada. El vehículo vuelve al catálogo.`
                        )
                      }
                    >
                      Anular
                    </Button>
                  )}

                  {esAdmin && !v.facturaNumero && (
                    <button
                      type="button"
                      aria-label={`Eliminar la venta ${v.numero}`}
                      onClick={() =>
                        accion(
                          () => ventasApi.eliminar(v.id),
                          `Venta ${v.numero} eliminada.`
                        )
                      }
                      className="inline-flex h-11 w-11 items-center justify-center
                                 text-plomo hover:text-accion-claro
                                 focus-visible:outline-2 focus-visible:outline-offset-2
                                 focus-visible:outline-accion-claro"
                    >
                      <Icono nombre="cerrar" className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </Celda>
            </>
          )}
        />
      </div>

      {esPersonal && (
        <FormularioVenta
          abierto={formulario}
          onCerrar={() => setFormulario(false)}
          onError={setError}
          onGuardado={() => {
            setFormulario(false);
            setAviso("Venta registrada.");
            recargar();
          }}
        />
      )}
    </PanelLayout>
  );
}

export default Ventas;
