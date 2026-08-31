import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import { citasApi, productosApi, serviciosApi } from "../api/cliente";
import { useAuth } from "../hooks/useAuth";

/** Fecha de hoy en formato AAAA-MM-DD, en hora local (no UTC). */
function hoyISO() {
  const d = new Date();
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}

function sumarDias(iso, dias) {
  const [a, m, d] = iso.split("-").map(Number);
  const fecha = new Date(a, m - 1, d + dias);
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

function nombreDia(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

/**
 * Agendamiento de citas.
 *
 * El boton "Cotizar" del catalogo trae aqui con ?modelo=<slug>. El cliente
 * elige servicio, fecha y hora; las horas disponibles se consultan al backend
 * para no ofrecer franjas ya reservadas.
 */
function AgendarCita() {
  const [parametros] = useSearchParams();
  const navegar = useNavigate();
  const { autenticado, usuario } = useAuth();

  const slugModelo = parametros.get("modelo");
  const servicioPreferido = parametros.get("servicio");

  const [vehiculo, setVehiculo] = useState(null);
  const [servicios, setServicios] = useState([]);
  const [servicioId, setServicioId] = useState("");
  const [fecha, setFecha] = useState(hoyISO());
  const [horas, setHoras] = useState([]);
  const [hora, setHora] = useState("");
  const [notas, setNotas] = useState("");

  const [cargandoHoras, setCargandoHoras] = useState(true);
  const [ticketHoras, setTicketHoras] = useState(0);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [erroresCampo, setErroresCampo] = useState({});
  const [confirmada, setConfirmada] = useState(null);

  const minimo = useMemo(() => hoyISO(), []);
  const maximo = useMemo(() => sumarDias(hoyISO(), 60), []);

  /* ---------------------- Carga inicial de datos ---------------------- */
  useEffect(() => {
    let vigente = true;

    serviciosApi
      .listar()
      .then((datos) => {
        if (!vigente) return;
        setServicios(datos.servicios);

        // Si vino ?servicio=..., se preselecciona; si no, el primero.
        const porNombre = datos.servicios.find((s) =>
          s.nombre.toLowerCase().includes((servicioPreferido || "").toLowerCase())
        );
        const elegido = servicioPreferido && porNombre ? porNombre : datos.servicios[0];
        if (elegido) setServicioId(String(elegido.id));
      })
      .catch((e) => vigente && setError(e.message));

    return () => {
      vigente = false;
    };
  }, [servicioPreferido]);

  useEffect(() => {
    if (!slugModelo) return undefined;
    let vigente = true;

    productosApi
      .obtener(slugModelo)
      .then((datos) => vigente && setVehiculo(datos.producto))
      .catch(() => vigente && setVehiculo(null));

    return () => {
      vigente = false;
    };
  }, [slugModelo]);

  /* -------------------- Horas disponibles por fecha -------------------- */
  // El indicador de carga se enciende en el manejador del <input>, no aqui,
  // para no llamar setState dentro del cuerpo del efecto.
  useEffect(() => {
    if (!fecha) return undefined;
    let vigente = true;

    citasApi
      .disponibilidad(fecha, vehiculo?.id)
      .then((datos) => {
        if (!vigente) return;
        setHoras(datos.horas);
        setHora("");
      })
      .catch((fallo) => {
        if (!vigente) return;
        setError(fallo.message);
        setHoras([]);
      })
      .finally(() => {
        if (vigente) setCargandoHoras(false);
      });

    return () => {
      vigente = false;
    };
  }, [fecha, vehiculo, ticketHoras]);

  const recargarHoras = useCallback(() => {
    setCargandoHoras(true);
    setTicketHoras((t) => t + 1);
  }, []);

  const cambiarFecha = (evento) => {
    setCargandoHoras(true);
    setFecha(evento.target.value);
  };

  /* ----------------------------- Envio ----------------------------- */
  const enviar = async (evento) => {
    evento.preventDefault();
    setError("");
    setErroresCampo({});

    if (!autenticado) {
      navegar("/login", { state: { desde: `/agendar${window.location.search}` } });
      return;
    }

    if (!hora) {
      setErroresCampo({ hora: "Selecciona una hora disponible." });
      return;
    }

    setEnviando(true);
    try {
      const datos = await citasApi.crear({
        fecha,
        hora,
        servicioId: Number(servicioId),
        productoId: vehiculo?.id ?? null,
        notas: notas.trim() || undefined,
      });
      setConfirmada(datos.cita);
    } catch (e) {
      setError(e.message);
      setErroresCampo(e.errores || {});
      recargarHoras(); // alguien pudo tomar la franja mientras tanto
    } finally {
      setEnviando(false);
    }
  };

  /* --------------------------- Confirmacion --------------------------- */
  if (confirmada) {
    return (
      <section className="mx-auto max-w-3xl px-5 pb-24 pt-32 sm:px-8">
        <div className="cristal reflejo p-8 text-center sm:p-12">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center border border-exito/40 text-exito">
            <Icono nombre="check" className="h-8 w-8" />
          </div>

          <p className="etiqueta text-accion-claro">Cita agendada</p>
          <h1 className="display mt-3 text-4xl text-hueso sm:text-5xl">
            Nos vemos pronto
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-ceniza">
            Tu cita quedó registrada con el número{" "}
            <span className="font-semibold text-hueso">#{confirmada.id}</span> en
            estado <span className="font-semibold text-hueso">{confirmada.estado}</span>.
            Un asesor la confirmará por correo.
          </p>

          <dl className="cristal-sutil mt-8 grid gap-5 p-6 text-left sm:grid-cols-2">
            {[
              ["Servicio", confirmada.servicio],
              ["Fecha", nombreDia(confirmada.fecha)],
              ["Hora", confirmada.hora.slice(0, 5)],
              ["Vehículo", confirmada.vehiculo || "Sin vehículo asignado"],
            ].map(([titulo, dato]) => (
              <div key={titulo}>
                <dt className="etiqueta text-plomo">{titulo}</dt>
                <dd className="mt-1 text-sm text-hueso">{dato}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button to="/panel/cliente" tamano="lg">
              Ver mis citas
              <Icono nombre="flecha" className="h-4 w-4" />
            </Button>
            <Button to="/modelos" variante="contorno" tamano="lg">
              Volver al catálogo
            </Button>
          </div>
        </div>
      </section>
    );
  }

  /* ---------------------------- Formulario ---------------------------- */
  return (
    <section className="mx-auto max-w-[1600px] px-5 pb-24 pt-28 sm:px-8 lg:pt-32">
      <nav aria-label="Ruta de navegación">
        <ol className="flex flex-wrap items-center gap-2 font-sans text-xs uppercase tracking-[0.18em] text-plomo">
          <li>
            <Link to="/" className="transition-colors duration-200 hover:text-hueso">
              Inicio
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li>
            <Link to="/modelos" className="transition-colors duration-200 hover:text-hueso">
              Modelos
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li className="text-hueso">Agendar cita</li>
        </ol>
      </nav>

      <h1 className="display mt-6 text-5xl text-hueso sm:text-7xl">
        Agenda tu cita
      </h1>
      <p className="mt-4 max-w-xl leading-relaxed text-ceniza">
        Elige el servicio, el día y la hora. Atendemos de lunes a viernes de
        8:00&nbsp;a.m. a 6:00&nbsp;p.m. y los sábados hasta el mediodía.
      </p>

      <div className="mt-12 grid gap-10 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
        {/* ------------------------- Formulario ------------------------- */}
        <form onSubmit={enviar} noValidate className="cristal reflejo space-y-8 p-6 sm:p-8">
          <Select
            label="Servicio"
            value={servicioId}
            onChange={(e) => setServicioId(e.target.value)}
            placeholder="Selecciona un servicio"
            opciones={servicios.map((s) => ({
              valor: String(s.id),
              etiqueta: `${s.nombre} (${s.duracionMin} min)`,
            }))}
            error={erroresCampo.servicioId}
          />

          <Input
            label="Fecha"
            type="date"
            value={fecha}
            min={minimo}
            max={maximo}
            onChange={cambiarFecha}
            ayuda="Puedes agendar hasta 60 días adelante. Los domingos no atendemos."
            error={erroresCampo.fecha}
          />

          {/* ------------------- Horas disponibles ------------------- */}
          <fieldset>
            <legend className="etiqueta mb-3 text-ceniza">
              Hora disponible {fecha && `· ${nombreDia(fecha)}`}
            </legend>

            {cargandoHoras ? (
              <p className="text-sm text-plomo">Consultando disponibilidad...</p>
            ) : horas.length === 0 ? (
              <p className="cristal-sutil p-4 text-sm text-ceniza">
                No atendemos ese día. Elige otra fecha.
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {horas.map((franja) => {
                  const activa = hora === franja.hora;
                  return (
                    <button
                      key={franja.hora}
                      type="button"
                      disabled={!franja.disponible}
                      onClick={() => setHora(franja.hora)}
                      aria-pressed={activa}
                      className={[
                        "min-h-12 border font-sans text-sm uppercase tracking-[0.1em]",
                        "transition-colors duration-200",
                        !franja.disponible
                          ? "cursor-not-allowed border-linea text-plomo line-through"
                          : activa
                            ? "cursor-pointer border-accion bg-accion-fondo text-hueso"
                            : "cursor-pointer border-linea text-hueso hover:border-hueso",
                      ].join(" ")}
                    >
                      {franja.hora}
                    </button>
                  );
                })}
              </div>
            )}

            {erroresCampo.hora && (
              <p role="alert" className="mt-2 flex items-start gap-2 text-sm font-medium text-accion-claro">
                <Icono nombre="alerta" className="mt-0.5 h-4 w-4 shrink-0" />
                {erroresCampo.hora}
              </p>
            )}
          </fieldset>

          <Input
            label="Notas (opcional)"
            multilinea
            filas={4}
            value={notas}
            onChange={(e) => setNotas(e.target.value)}
            maxLength={300}
            mostrarContador
            placeholder="Cuéntanos algo que debamos tener en cuenta."
            error={erroresCampo.notas}
          />

          {error && (
            <div
              role="alert"
              className="flex items-start gap-3 border border-accion/40 bg-accion/10 p-4
                         text-sm font-medium text-accion-claro"
            >
              <Icono nombre="alerta" className="mt-0.5 h-5 w-5 shrink-0" />
              {error}
            </div>
          )}

          {!autenticado && (
            <div className="cristal-sutil p-4 text-sm text-ceniza">
              Para confirmar la cita necesitas una cuenta.{" "}
              <Link to="/login" className="font-semibold text-accion-claro underline-offset-4 hover:underline">
                Inicia sesión o regístrate
              </Link>
              . No perderás lo que ya seleccionaste.
            </div>
          )}

          <Button type="submit" tamano="lg" cargando={enviando} ancho>
            {enviando
              ? "Agendando..."
              : autenticado
                ? "Confirmar cita"
                : "Iniciar sesión y agendar"}
          </Button>
        </form>

        {/* --------------------------- Resumen --------------------------- */}
        <aside className="lg:sticky lg:top-28 lg:self-start">
          <div className="cristal">
            {vehiculo ? (
              <>
                <div className="border-b border-linea p-6 text-hueso">
                  <p className="etiqueta text-accion">{vehiculo.marca}</p>
                  <h2 className="display mt-1 text-3xl">{vehiculo.modelo}</h2>
                  <img
                    src={`/src/assets/images/${vehiculo.imagen}`}
                    alt={vehiculo.titulo}
                    width={1600}
                    height={900}
                    loading="lazy"
                    className="mt-4 w-full object-contain"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                    }}
                  />
                </div>
                <dl className="divide-y divide-linea">
                  {[
                    ["Motor", vehiculo.specs.motor],
                    ["Potencia", vehiculo.specs.potencia],
                    ["0–100 km/h", vehiculo.specs.aceleracion],
                  ].map(([t, d]) => (
                    <div key={t} className="flex items-baseline justify-between gap-4 p-4">
                      <dt className="text-sm text-ceniza">{t}</dt>
                      <dd className="font-sans text-sm uppercase tracking-[0.08em] text-hueso">
                        {d}
                      </dd>
                    </div>
                  ))}
                </dl>
              </>
            ) : (
              <div className="p-6">
                <p className="etiqueta text-accion-claro">Sin vehículo</p>
                <h2 className="display mt-2 text-2xl text-hueso">
                  Cita general
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-ceniza">
                  No seleccionaste un modelo. Puedes elegir uno desde el catálogo
                  o continuar con una cita general.
                </p>
                <Button to="/modelos" variante="contorno" ancho className="mt-5">
                  Ver el catálogo
                </Button>
              </div>
            )}
          </div>

          {autenticado && (
            <div className="mt-3 border border-linea p-5">
              <p className="etiqueta text-plomo">Agendas como</p>
              <p className="mt-1 text-sm text-hueso">
                {usuario.nombre} {usuario.apellido}
              </p>
              <p className="text-sm text-ceniza">{usuario.correo}</p>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

export default AgendarCita;
