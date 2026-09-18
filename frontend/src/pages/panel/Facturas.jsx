import { useCallback, useState } from "react";

import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Select from "../../components/ui/Select";
import Paginador from "../../components/panel/Paginador";
import { Tabla, Celda } from "../../components/panel/Tabla";
import { PanelLayout, Aviso, Estado } from "../../components/panel/PanelLayout";
import { facturasApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";
import { fechaHora, pesos } from "../../utils/formato";

/**
 * Facturas.
 *
 * No hay botón de borrar, y no es un olvido: una factura se anula, nunca se
 * elimina. Borrarla dejaría un hueco en el consecutivo, y un consecutivo con
 * huecos no sirve para lo único que hace falta, que es poder demostrar que no
 * falta ninguna. El backend tampoco expone una ruta para borrarlas.
 */

const ESTADOS = [
  { valor: "emitida", etiqueta: "Emitidas" },
  { valor: "anulada", etiqueta: "Anuladas" },
];

function Facturas() {
  const { rol } = useAuth();
  const esPersonal = rol === "administrador" || rol === "empleado";

  const [estado, setEstado] = useState("");
  const [pagina, setPagina] = useState(1);
  const [descargando, setDescargando] = useState(null);
  const [aviso, setAviso] = useState("");

  const obtener = useCallback(
    () => facturasApi.listar({ estado, pagina, porPagina: 20 }),
    [estado, pagina]
  );

  const { datos, cargando, error, setError, recargar } = useCarga(obtener);
  const facturas = datos?.facturas ?? [];

  const descargar = async (factura) => {
    setError("");
    setAviso("");
    setDescargando(factura.id);
    try {
      const nombre = await facturasApi.descargar(factura.id, factura.numero);
      setAviso(`Descargado: ${nombre}`);
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setDescargando(null);
    }
  };

  const anular = async (factura) => {
    setError("");
    setAviso("");
    try {
      await facturasApi.anular(factura.id);
      setAviso(`Factura ${factura.numero} anulada.`);
      recargar();
    } catch (fallo) {
      setError(fallo.message);
    }
  };

  const columnas = [
    { clave: "numero", titulo: "Número" },
    { clave: "fecha", titulo: "Emitida" },
    ...(esPersonal ? [{ clave: "cliente", titulo: "Cliente" }] : []),
    { clave: "venta", titulo: "Venta" },
    { clave: "total", titulo: "Total", alineacion: "derecha" },
    { clave: "estado", titulo: "Estado" },
    { clave: "acciones", titulo: "", alineacion: "derecha" },
  ];

  return (
    <PanelLayout
      etiqueta="Facturación"
      titulo="Facturas"
      descripcion={
        esPersonal
          ? "Las facturas emitidas, con su PDF descargable. Una factura se anula, no se borra: el consecutivo tiene que poder demostrar que no falta ninguna."
          : "Las facturas de tus compras. Descárgalas en PDF y consérvalas como soporte."
      }
      acciones={
        esPersonal && (
          <Button variante="claro" tamano="sm" to="/panel/ventas">
            <Icono nombre="etiqueta" className="h-4 w-4" />
            Ir a ventas
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
          placeholder="Todas"
          opciones={ESTADOS}
          className="w-56"
        />
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
          filas={facturas}
          cargando={cargando}
          vacio={
            esPersonal
              ? "Todavía no se ha emitido ninguna factura. Se emiten desde la pantalla de ventas."
              : "Todavía no tienes facturas. Aparecerán aquí cuando se emitan."
          }
          pie={<Paginador pagina={datos?.pagina} onCambiar={setPagina} />}
          fila={(f) => (
            <>
              <Celda className="font-sans text-hueso">{f.numero}</Celda>
              <Celda>{fechaHora(f.fechaEmision)}</Celda>
              {esPersonal && <Celda>{f.cliente ?? "—"}</Celda>}
              <Celda className="font-sans text-xs text-plomo">
                {f.ventaNumero ?? "—"}
              </Celda>
              <Celda alineacion="derecha" className="text-hueso">
                {pesos(f.total)}
              </Celda>
              <Celda>
                <Estado valor={f.estado} />
              </Celda>
              <Celda alineacion="derecha">
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <Button
                    variante="texto"
                    tamano="sm"
                    onClick={() => descargar(f)}
                    cargando={descargando === f.id}
                  >
                    <Icono nombre="documento" className="h-4 w-4" />
                    PDF
                  </Button>

                  {esPersonal && f.estado === "emitida" && (
                    <Button variante="texto" tamano="sm" onClick={() => anular(f)}>
                      Anular
                    </Button>
                  )}
                </div>
              </Celda>
            </>
          )}
        />
      </div>
    </PanelLayout>
  );
}

export default Facturas;
