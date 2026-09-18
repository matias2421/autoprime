import { useCallback, useState } from "react";

import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Barras from "../../components/graficos/Barras";
import Lineas from "../../components/graficos/Lineas";
import { PanelLayout, Tarjeta, Aviso } from "../../components/panel/PanelLayout";
import { reportesApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";
import {
  diaMes,
  fechaCorta,
  haceDias,
  hoyIso,
  numero,
  pesos,
  pesosCortos,
} from "../../utils/formato";

/**
 * Tablero de ventas.
 *
 * Una sola pantalla para los tres roles, no tres pantallas parecidas. El
 * backend ya decide qué cifras devuelve según quién pregunta: al personal le
 * da las del negocio y a un cliente las suyas. Duplicar la pantalla por rol
 * duplicaría también cada arreglo futuro, y a la tercera vez una de las
 * copias se queda atrás.
 *
 * Lo que sí cambia por rol es qué se muestra alrededor: el bloque de cifras
 * de todo el negocio solo tiene sentido para quien lo gestiona.
 */

const RANGOS = [
  { id: "hoy", etiqueta: "Hoy", dias: 0 },
  { id: "semana", etiqueta: "7 días", dias: 6 },
  { id: "mes", etiqueta: "30 días", dias: 29 },
  { id: "trimestre", etiqueta: "90 días", dias: 89 },
];

function Tablero() {
  const { rol } = useAuth();
  const esPersonal = rol === "administrador" || rol === "empleado";

  const [rango, setRango] = useState("semana");
  const [descargando, setDescargando] = useState("");
  const [avisoDescarga, setAvisoDescarga] = useState("");

  const elegido = RANGOS.find((r) => r.id === rango) ?? RANGOS[1];
  const desde = haceDias(elegido.dias);
  const hasta = hoyIso();

  const obtener = useCallback(async () => {
    const peticiones = [reportesApi.ventas({ desde, hasta })];
    // El panel administrativo es del negocio entero: pedirlo como cliente
    // devolvería 403 y rompería la carga de toda la pantalla.
    if (esPersonal) peticiones.push(reportesApi.panel());

    const [reporte, administrativo] = await Promise.all(peticiones);
    return { reporte: reporte.reporte, panel: administrativo?.panel ?? null };
  }, [desde, hasta, esPersonal]);

  const { datos, cargando, error, setError } = useCarga(obtener);

  const reporte = datos?.reporte ?? null;
  const panel = datos?.panel ?? null;

  const descargar = async (formato) => {
    setError("");
    setAvisoDescarga("");
    setDescargando(formato);
    try {
      const nombre = await (formato === "pdf"
        ? reportesApi.ventasPdf({ desde, hasta })
        : reportesApi.ventasExcel({ desde, hasta }));
      setAvisoDescarga(`Descargado: ${nombre}`);
    } catch (fallo) {
      setError(fallo.message);
    } finally {
      setDescargando("");
    }
  };

  const serie = (reporte?.porDia ?? []).map((d) => ({
    etiqueta: fechaCorta(d.fecha),
    corta: diaMes(d.fecha),
    valor: d.ingresos,
  }));

  return (
    <PanelLayout
      etiqueta="Tablero"
      titulo={esPersonal ? "Ventas del negocio" : "Mis compras"}
      descripcion={
        esPersonal
          ? "Cifras del periodo, movimiento diario y lo que más se vende. El mismo reporte se descarga en PDF para imprimir o en Excel para analizar."
          : "Un resumen de lo que has comprado en AutoPrime, con el detalle descargable."
      }
      acciones={
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variante="claro"
            tamano="sm"
            onClick={() => descargar("pdf")}
            cargando={descargando === "pdf"}
          >
            <Icono nombre="documento" className="h-4 w-4" />
            PDF
          </Button>
          <Button
            variante="claro"
            tamano="sm"
            onClick={() => descargar("excel")}
            cargando={descargando === "excel"}
          >
            <Icono nombre="documento" className="h-4 w-4" />
            Excel
          </Button>
        </div>
      }
    >
      {/* ----------------------------- Filtro ----------------------------- */}
      <div
        role="group"
        aria-label="Periodo del reporte"
        className="mt-8 flex flex-wrap items-center gap-2"
      >
        {RANGOS.map((r) => (
          <button
            key={r.id}
            type="button"
            onClick={() => setRango(r.id)}
            aria-pressed={rango === r.id}
            className={`min-h-11 border px-5 font-sans text-xs uppercase
                        tracking-[0.14em] transition-colors
                        focus-visible:outline-2 focus-visible:outline-offset-2
                        focus-visible:outline-accion-claro
                        motion-reduce:transition-none ${
                          rango === r.id
                            ? "border-accion bg-accion-fondo text-hueso"
                            : "border-trazo text-ceniza hover:border-hueso hover:text-hueso"
                        }`}
          >
            {r.etiqueta}
          </button>
        ))}

        <p className="ml-auto font-sans text-xs uppercase tracking-[0.12em] text-plomo">
          {desde === hasta
            ? fechaCorta(hasta)
            : `${fechaCorta(desde)} — ${fechaCorta(hasta)}`}
        </p>
      </div>

      {error && (
        <div className="mt-6">
          <Aviso tipo="error">{error}</Aviso>
        </div>
      )}
      {avisoDescarga && (
        <div className="mt-6">
          <Aviso tipo="exito">{avisoDescarga}</Aviso>
        </div>
      )}

      {cargando && !reporte && (
        <p className="mt-10 text-sm text-ceniza">Cargando el tablero…</p>
      )}

      {reporte && (
        <>
          {/* --------------------------- Tarjetas -------------------------- */}
          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Tarjeta
              titulo="Ventas"
              valor={numero(reporte.resumen.total)}
              icono="etiqueta"
            />
            <Tarjeta
              titulo="Ingresos"
              valor={pesosCortos(reporte.resumen.ingresos)}
              icono="tarjeta"
              acento
            />
            <Tarjeta
              titulo="Ticket promedio"
              valor={pesosCortos(reporte.resumen.ticketPromedio)}
              icono="rayo"
            />
            <Tarjeta
              titulo="Por cobrar"
              valor={numero(reporte.resumen.pendientes)}
              icono="reloj"
            />
          </div>

          {/* --------------------------- Gráficas -------------------------- */}
          <div className="mt-6 grid gap-6 xl:grid-cols-[1.6fr_1fr]">
            <section className="cristal p-6">
              <h2 className="etiqueta text-plomo">Ingresos por día</h2>
              <p className="mt-1 text-xs text-plomo">
                Solo cuenta lo cobrado: una venta anulada no ingresó nada.
              </p>
              <div className="mt-6">
                <Lineas
                  datos={serie}
                  formato={pesosCortos}
                  titulo="Ingresos por día"
                />
              </div>
            </section>

            <section className="cristal p-6">
              <h2 className="etiqueta text-plomo">Por estado</h2>
              <div className="mt-6">
                <Barras
                  datos={(reporte.porEstado ?? []).map((c) => ({
                    etiqueta: c.estado.replace(/_/g, " "),
                    valor: c.ventas,
                    detalle: pesos(c.importe),
                  }))}
                  formato={numero}
                  vacio="Sin ventas en el periodo."
                />
              </div>
            </section>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <section className="cristal p-6">
              <h2 className="etiqueta text-plomo">Vehículos más vendidos</h2>
              <div className="mt-6">
                <Barras
                  datos={(reporte.topVehiculos ?? []).map((v) => ({
                    etiqueta: v.descripcion,
                    valor: v.importe,
                    detalle: `${numero(v.unidades)} ${
                      v.unidades === 1 ? "unidad" : "unidades"
                    }`,
                  }))}
                  formato={pesosCortos}
                  vacio="Ningún vehículo vendido en el periodo."
                />
              </div>
            </section>

            <section className="cristal p-6">
              <h2 className="etiqueta text-plomo">Servicios más vendidos</h2>
              <div className="mt-6">
                <Barras
                  datos={(reporte.topServicios ?? []).map((s) => ({
                    etiqueta: s.descripcion,
                    valor: s.importe,
                    detalle: `${numero(s.unidades)} ${
                      s.unidades === 1 ? "vez" : "veces"
                    }`,
                  }))}
                  formato={pesosCortos}
                  vacio="Ningún servicio vendido en el periodo."
                />
              </div>
            </section>
          </div>

          {/* -------------------- Cifras de todo el negocio ----------------- */}
          {panel && (
            <section className="mt-10">
              <h2 className="etiqueta text-accion-claro">Estado del negocio</h2>
              <p className="mt-2 text-sm text-ceniza">
                Estas cifras no dependen del periodo elegido: son de ahora mismo.
              </p>

              <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Tarjeta
                  titulo="Ventas de hoy"
                  valor={numero(panel.ventasHoy)}
                  icono="etiqueta"
                  acento
                />
                <Tarjeta
                  titulo="Ingresos de hoy"
                  valor={pesosCortos(panel.ingresosHoy)}
                  icono="tarjeta"
                />
                <Tarjeta
                  titulo="Catálogo disponible"
                  valor={numero(panel.vehiculosDisponibles)}
                  icono="auto"
                />
                <Tarjeta
                  titulo="Vehículos vendidos"
                  valor={numero(panel.vehiculosVendidos)}
                  icono="check"
                />
                <Tarjeta
                  titulo="Citas por atender"
                  valor={numero(panel.citasPendientes)}
                  icono="reloj"
                />
                <Tarjeta
                  titulo="PQR abiertas"
                  valor={numero(panel.pqrAbiertas)}
                  icono="alerta"
                  acento={panel.pqrAbiertas > 0}
                />
                <Tarjeta
                  titulo="Facturas emitidas"
                  valor={numero(panel.facturasEmitidas)}
                  icono="documento"
                />
                <Tarjeta
                  titulo="Usuarios activos"
                  valor={numero(panel.usuariosActivos)}
                  icono="usuario"
                />
              </div>
            </section>
          )}
        </>
      )}
    </PanelLayout>
  );
}

export default Tablero;
