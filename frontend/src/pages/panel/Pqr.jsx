import { useCallback, useState } from "react";

import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import Paginador from "../../components/panel/Paginador";
import { Tabla, Celda } from "../../components/panel/Tabla";
import { PanelLayout, Tarjeta, Aviso, Estado } from "../../components/panel/PanelLayout";
import { pqrApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";
import { fechaHora, numero } from "../../utils/formato";

/**
 * PQR: peticiones, quejas, reclamos y sugerencias.
 *
 * Para un cliente es un formulario y el seguimiento de lo que ha radicado.
 * Para el personal es una bandeja de trabajo, y por eso el backend devuelve
 * lo pendiente primero: en una bandeja ordenada solo por fecha, un reclamo
 * sin atender acaba enterrado bajo veinte casos cerrados.
 */

const TIPOS = [
  { valor: "peticion", etiqueta: "Petición" },
  { valor: "queja", etiqueta: "Queja" },
  { valor: "reclamo", etiqueta: "Reclamo" },
  { valor: "sugerencia", etiqueta: "Sugerencia" },
];

const ESTADOS = [
  { valor: "pendiente", etiqueta: "Pendientes" },
  { valor: "en_proceso", etiqueta: "En proceso" },
  { valor: "respondida", etiqueta: "Respondidas" },
  { valor: "cerrada", etiqueta: "Cerradas" },
];

/* ------------------------------------------------------------------ */

function FormularioRadicar({ abierto, alCerrar, onGuardado, onError }) {
  const [tipo, setTipo] = useState("peticion");
  const [asunto, setAsunto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [guardando, setGuardando] = useState(false);

  const enviar = async (evento) => {
    evento.preventDefault();
    onError("");
    setGuardando(true);
    try {
      await pqrApi.crear({ tipo, asunto, descripcion });
      setAsunto("");
      setDescripcion("");
      setTipo("peticion");
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
      alCerrar={alCerrar}
      titulo="Radicar una PQR"
      descripcion="Cuéntanos qué pasó. Recibirás un número de radicado y podrás seguir el caso desde esta misma pantalla."
    >
      <form onSubmit={enviar} className="space-y-5">
        <Select
          label="Tipo"
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          placeholder="Elige el tipo"
          opciones={TIPOS}
        />

        <Input
          label="Asunto"
          value={asunto}
          onChange={(e) => setAsunto(e.target.value)}
          maxLength={120}
          mostrarContador
          ayuda="Un resumen en una línea."
          required
        />

        <Input
          label="Descripción"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          multilinea
          filas={6}
          maxLength={800}
          mostrarContador
          ayuda="Mínimo 20 caracteres. Cuanto más concreto, más rápido se resuelve."
          required
        />

        <div className="flex flex-wrap justify-end gap-3">
          <Button variante="contorno" onClick={alCerrar}>
            Cancelar
          </Button>
          <Button type="submit" cargando={guardando}>
            Radicar
          </Button>
        </div>
      </form>
    </Modal>
  );
}

/* ------------------------------------------------------------------ */

function FormularioResponder({ registro, alCerrar, onGuardado, onError }) {
  const [respuesta, setRespuesta] = useState("");
  const [estado, setEstado] = useState("respondida");
  const [guardando, setGuardando] = useState(false);

  const enviar = async (evento) => {
    evento.preventDefault();
    onError("");
    setGuardando(true);
    try {
      await pqrApi.responder(registro.id, { respuesta, estado });
      setRespuesta("");
      onGuardado();
    } catch (fallo) {
      onError(fallo.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Modal
      abierto={Boolean(registro)}
      alCerrar={alCerrar}
      titulo={`Responder ${registro?.numero ?? ""}`}
      descripcion={registro?.asunto}
    >
      <form onSubmit={enviar} className="space-y-5">
        <div className="border border-linea p-4">
          <p className="etiqueta text-plomo">Lo que nos escribieron</p>
          <p className="mt-2 text-sm leading-relaxed text-ceniza">
            {registro?.descripcion}
          </p>
          <p className="mt-3 font-sans text-xs text-plomo">
            {registro?.autor} · {fechaHora(registro?.creadoEn)}
          </p>
        </div>

        <Input
          label="Respuesta"
          value={respuesta}
          onChange={(e) => setRespuesta(e.target.value)}
          multilinea
          filas={6}
          maxLength={800}
          mostrarContador
          required
        />

        <Select
          label="Estado tras responder"
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
          placeholder="Elige el estado"
          ayuda="«En proceso» sirve para contestar un avance sin cerrar el caso."
          opciones={[
            { valor: "respondida", etiqueta: "Respondida" },
            { valor: "en_proceso", etiqueta: "En proceso" },
            { valor: "cerrada", etiqueta: "Cerrada" },
          ]}
        />

        <div className="flex flex-wrap justify-end gap-3">
          <Button variante="contorno" onClick={alCerrar}>
            Cancelar
          </Button>
          <Button type="submit" cargando={guardando}>
            Enviar respuesta
          </Button>
        </div>
      </form>
    </Modal>
  );
}

/* ------------------------------------------------------------------ */

function Pqr() {
  const { rol } = useAuth();
  const esPersonal = rol === "administrador" || rol === "empleado";

  const [estado, setEstado] = useState("");
  const [tipo, setTipo] = useState("");
  const [pagina, setPagina] = useState(1);
  const [radicando, setRadicando] = useState(false);
  const [respondiendo, setRespondiendo] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [aviso, setAviso] = useState("");

  const obtener = useCallback(async () => {
    const [lista, resumen] = await Promise.all([
      pqrApi.listar({ estado, tipo, pagina, porPagina: 20 }),
      pqrApi.resumen(),
    ]);
    return { ...lista, resumen: resumen.resumen };
  }, [estado, tipo, pagina]);

  const { datos, cargando, error, setError, recargar } = useCarga(obtener);

  const registros = datos?.pqr ?? [];
  const resumen = datos?.resumen;

  const cerrar = async (registro) => {
    setError("");
    setAviso("");
    try {
      await pqrApi.cambiarEstado(registro.id, "cerrada");
      setAviso(`${registro.numero} cerrada.`);
      recargar();
    } catch (fallo) {
      setError(fallo.message);
    }
  };

  const columnas = [
    { clave: "numero", titulo: "Radicado" },
    { clave: "tipo", titulo: "Tipo" },
    { clave: "asunto", titulo: "Asunto" },
    ...(esPersonal ? [{ clave: "autor", titulo: "De" }] : []),
    { clave: "creado", titulo: "Radicada" },
    { clave: "estado", titulo: "Estado" },
    { clave: "acciones", titulo: "", alineacion: "derecha" },
  ];

  return (
    <PanelLayout
      etiqueta={esPersonal ? "Atención al cliente" : "Mis solicitudes"}
      titulo="PQR"
      descripcion={
        esPersonal
          ? "La bandeja de peticiones, quejas, reclamos y sugerencias. Lo pendiente sale primero."
          : "Radica una solicitud y sigue su estado. Te responderemos desde aquí mismo."
      }
      acciones={
        <Button onClick={() => setRadicando(true)}>
          <Icono nombre="correo" className="h-4 w-4" />
          Radicar PQR
        </Button>
      }
    >
      {resumen && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Tarjeta
            titulo="Pendientes"
            valor={numero(resumen.pendientes)}
            icono="alerta"
            acento={resumen.pendientes > 0}
          />
          <Tarjeta
            titulo="En proceso"
            valor={numero(resumen.enProceso)}
            icono="reloj"
          />
          <Tarjeta
            titulo="Respondidas"
            valor={numero(resumen.respondidas)}
            icono="check"
          />
          <Tarjeta titulo="Total" valor={numero(resumen.total)} icono="documento" />
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <Select
          label="Estado"
          value={estado}
          onChange={(e) => {
            setEstado(e.target.value);
            setPagina(1);
          }}
          placeholder="Todos"
          opciones={ESTADOS}
          className="w-52"
        />
        <Select
          label="Tipo"
          value={tipo}
          onChange={(e) => {
            setTipo(e.target.value);
            setPagina(1);
          }}
          placeholder="Todos"
          opciones={TIPOS}
          className="w-52"
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
          filas={registros}
          cargando={cargando}
          vacio={
            esPersonal
              ? "No hay solicitudes en este filtro."
              : "Todavía no has radicado ninguna solicitud."
          }
          pie={<Paginador pagina={datos?.pagina} onCambiar={setPagina} />}
          fila={(p) => (
            <>
              <Celda className="font-sans text-hueso">{p.numero}</Celda>
              <Celda className="capitalize">{p.tipo}</Celda>
              <Celda className="max-w-xs truncate text-hueso" title={p.asunto}>
                {p.asunto}
              </Celda>
              {esPersonal && <Celda>{p.autor ?? "—"}</Celda>}
              <Celda>{fechaHora(p.creadoEn)}</Celda>
              <Celda>
                <Estado valor={p.estado} />
              </Celda>
              <Celda alineacion="derecha">
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <Button
                    variante="texto"
                    tamano="sm"
                    onClick={() => setDetalle(p)}
                  >
                    Ver
                  </Button>

                  {esPersonal && p.estado !== "cerrada" && (
                    <>
                      <Button
                        variante="texto"
                        tamano="sm"
                        onClick={() => setRespondiendo(p)}
                      >
                        Responder
                      </Button>
                      <Button
                        variante="texto"
                        tamano="sm"
                        onClick={() => cerrar(p)}
                      >
                        Cerrar
                      </Button>
                    </>
                  )}
                </div>
              </Celda>
            </>
          )}
        />
      </div>

      <FormularioRadicar
        abierto={radicando}
        alCerrar={() => setRadicando(false)}
        onError={setError}
        onGuardado={() => {
          setRadicando(false);
          setAviso("Solicitud radicada. Te avisaremos cuando haya respuesta.");
          recargar();
        }}
      />

      {respondiendo && (
        <FormularioResponder
          registro={respondiendo}
          alCerrar={() => setRespondiendo(null)}
          onError={setError}
          onGuardado={() => {
            setAviso(`Respuesta enviada para ${respondiendo.numero}.`);
            setRespondiendo(null);
            recargar();
          }}
        />
      )}

      {detalle && (
        <Modal
          abierto
          alCerrar={() => setDetalle(null)}
          titulo={detalle.numero}
          descripcion={detalle.asunto}
        >
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3">
              <Estado valor={detalle.estado} />
              <span className="font-sans text-xs uppercase tracking-[0.12em] text-plomo">
                {detalle.tipo} · {fechaHora(detalle.creadoEn)}
              </span>
            </div>

            <div>
              <p className="etiqueta text-plomo">Solicitud</p>
              <p className="mt-2 text-sm leading-relaxed text-ceniza">
                {detalle.descripcion}
              </p>
            </div>

            {detalle.respuesta ? (
              <div className="border-l-2 border-accion pl-4">
                <p className="etiqueta text-accion-claro">Respuesta de AutoPrime</p>
                <p className="mt-2 text-sm leading-relaxed text-hueso">
                  {detalle.respuesta}
                </p>
                {detalle.responsable && (
                  <p className="mt-3 font-sans text-xs text-plomo">
                    {detalle.responsable} · {fechaHora(detalle.actualizadoEn)}
                  </p>
                )}
              </div>
            ) : (
              <Aviso>
                Todavía sin respuesta. Te escribiremos en cuanto la tengamos.
              </Aviso>
            )}
          </div>
        </Modal>
      )}
    </PanelLayout>
  );
}

export default Pqr;
