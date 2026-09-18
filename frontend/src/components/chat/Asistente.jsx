import { useCallback, useEffect, useRef, useState } from "react";

import Icono from "../ui/Icono";
import { chatApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";

/**
 * Chat flotante con el asistente.
 *
 * Atiende también a quien no ha iniciado sesión: es lo primero que ve un
 * visitante, y pedirle registro antes de dejarle preguntar un precio es
 * perder la conversación antes de empezarla.
 *
 * Por eso el hilo se guarda aquí, en el estado del componente, y no se
 * recupera del servidor: una conversación anónima no se puede releer —los
 * identificadores son consecutivos y cualquiera podría pedir la de otro—, así
 * que la transcripción vive mientras dure la pestaña. Con sesión iniciada sí
 * queda asociada a la cuenta en la base.
 *
 * Si el asistente no está configurado, el botón no se pinta: mejor que no
 * exista a que exista y no responda.
 */

const SUGERENCIAS = [
  "¿Qué vehículos tienen disponibles?",
  "¿Cuánto cuesta un peritaje?",
  "¿Cómo agendo una prueba de manejo?",
];

function Burbuja({ mensaje }) {
  const esMio = mensaje.rol === "usuario";
  return (
    <div className={`flex ${esMio ? "justify-end" : "justify-start"}`}>
      <p
        className={`max-w-[85%] whitespace-pre-wrap px-4 py-3 text-sm leading-relaxed ${
          esMio
            ? "bg-accion-fondo text-hueso"
            : "border border-linea bg-grafito text-ceniza"
        }`}
      >
        {mensaje.contenido}
      </p>
    </div>
  );
}

function Conversador() {
  const [abierto, setAbierto] = useState(false);
  const [conversacion, setConversacion] = useState(null);
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [esperando, setEsperando] = useState(false);
  const [error, setError] = useState("");

  const finRef = useRef(null);
  const campoRef = useRef(null);

  useEffect(() => {
    if (abierto) finRef.current?.scrollIntoView({ block: "end" });
  }, [mensajes, abierto, esperando]);

  useEffect(() => {
    if (abierto) campoRef.current?.focus();
  }, [abierto]);

  // Escape cierra, como cualquier capa flotante del sitio.
  useEffect(() => {
    if (!abierto) return undefined;
    const alPulsar = (evento) => {
      if (evento.key === "Escape") setAbierto(false);
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, [abierto]);

  const enviar = useCallback(
    async (contenido) => {
      const limpio = contenido.trim();
      if (!limpio || esperando) return;

      setError("");
      setTexto("");

      // La pregunta se pinta de inmediato con un id provisional. Esperar a que
      // el servidor conteste para mostrarla haría que el chat pareciera
      // ignorar lo que uno acaba de escribir durante un segundo largo.
      const provisional = { id: `local-${Date.now()}`, rol: "usuario", contenido: limpio };
      setMensajes((previos) => [...previos, provisional]);
      setEsperando(true);

      try {
        let hilo = conversacion;
        if (!hilo) {
          const abierta = await chatApi.abrir(null);
          hilo = abierta.conversacion.id;
          setConversacion(hilo);
        }

        const respuesta = await chatApi.escribir(hilo, limpio);
        setMensajes((previos) => [
          ...previos.filter((m) => m.id !== provisional.id),
          respuesta.chat.pregunta,
          respuesta.chat.respuesta,
        ]);
      } catch (fallo) {
        // La pregunta se queda en pantalla: se puede reintentar sin volver a
        // escribirla, y el servidor ya la guardó si llegó a registrarse.
        setError(
          fallo.codigo === "servicio_externo_caido"
            ? "El asistente no está respondiendo ahora mismo. Puedes radicar una PQR y te contestamos nosotros."
            : fallo.message
        );
      } finally {
        setEsperando(false);
      }
    },
    [conversacion, esperando]
  );

  return (
    <>
      {/* Botón flotante. 56 px, por encima del mínimo táctil de 44.
          Va apilado sobre el de WhatsApp y no en la esquina izquierda, que
          ya la ocupa el de «volver arriba»: dos controles flotantes en el
          mismo sitio se tapan justo cuando aparece el segundo. */}
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
        aria-controls="panel-asistente"
        aria-label={abierto ? "Cerrar el asistente" : "Abrir el asistente"}
        className="cristal cristal-vivo fixed bottom-24 right-5 z-50 inline-flex h-14 w-14
                   items-center justify-center text-hueso transition-transform
                   hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-3
                   focus-visible:outline-accion-claro motion-reduce:transition-none
                   sm:bottom-28 sm:right-8"
      >
        <Icono nombre={abierto ? "cerrar" : "correo"} className="h-5 w-5" />
      </button>

      {abierto && (
        <section
          id="panel-asistente"
          aria-label="Asistente de AutoPrime"
          className="cristal fixed bottom-42 left-4 right-4 z-50 flex max-h-[62vh] flex-col
                     overflow-hidden sm:left-auto sm:right-8 sm:w-[400px]"
        >
          <header className="flex items-start justify-between gap-4 border-b border-linea p-5">
            <div>
              <p className="etiqueta text-accion-claro">Asistente</p>
              <p className="mt-1 text-sm text-hueso">AutoPrime</p>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              aria-label="Cerrar el asistente"
              className="inline-flex h-11 w-11 items-center justify-center text-plomo
                         hover:text-hueso focus-visible:outline-2
                         focus-visible:outline-offset-2 focus-visible:outline-accion-claro"
            >
              <Icono nombre="cerrar" className="h-4 w-4" />
            </button>
          </header>

          <div
            className="flex-1 space-y-3 overflow-y-auto p-5"
            role="log"
            aria-live="polite"
            aria-atomic="false"
          >
            {mensajes.length === 0 && (
              <>
                <p className="text-sm leading-relaxed text-ceniza">
                  Pregúntame por el catálogo, los servicios o cómo agendar. Si
                  no tengo el dato, te digo dónde conseguirlo en vez de
                  inventármelo.
                </p>
                <ul className="space-y-2 pt-2">
                  {SUGERENCIAS.map((s) => (
                    <li key={s}>
                      <button
                        type="button"
                        onClick={() => enviar(s)}
                        className="min-h-11 w-full border border-trazo px-4 py-2.5 text-left
                                   text-sm text-ceniza transition-colors hover:border-hueso
                                   hover:text-hueso focus-visible:outline-2
                                   focus-visible:outline-offset-2
                                   focus-visible:outline-accion-claro
                                   motion-reduce:transition-none"
                      >
                        {s}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )}

            {mensajes.map((m) => (
              <Burbuja key={m.id} mensaje={m} />
            ))}

            {esperando && (
              <p className="text-sm text-plomo">Escribiendo…</p>
            )}

            {error && (
              <p role="alert" className="border border-accion/40 bg-accion/10 p-3 text-sm text-accion-claro">
                {error}
              </p>
            )}

            <div ref={finRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              enviar(texto);
            }}
            className="flex items-end gap-2 border-t border-linea p-4"
          >
            <label htmlFor="mensaje-asistente" className="sr-only">
              Escribe tu mensaje
            </label>
            <input
              id="mensaje-asistente"
              ref={campoRef}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              maxLength={1500}
              autoComplete="off"
              placeholder="Escribe tu mensaje…"
              className="min-h-11 flex-1 border border-linea bg-carbon px-3 py-2.5 text-sm
                         text-hueso placeholder:text-plomo focus:border-hueso
                         focus:outline-none"
            />
            <button
              type="submit"
              disabled={!texto.trim() || esperando}
              aria-label="Enviar mensaje"
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center
                         bg-accion-fondo text-hueso hover:bg-accion-hondo
                         focus-visible:outline-2 focus-visible:outline-offset-2
                         focus-visible:outline-accion-claro
                         disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Icono nombre="derecha" className="h-4 w-4" />
            </button>
          </form>

          <p className="border-t border-linea px-4 py-2 font-sans text-[11px] text-plomo">
            Respuestas generadas con IA. No escribas contraseñas ni datos de tu
            tarjeta.
          </p>
        </section>
      )}
    </>
  );
}

/**
 * Envoltorio: decide si el asistente existe y le pone `key` al conversador.
 *
 * Esa `key` es lo que resetea el hilo al entrar o salir de la sesion. La
 * alternativa —un efecto que vacie los mensajes cuando cambia el usuario—
 * hace lo mismo un render mas tarde, y en ese hueco la pantalla muestra la
 * conversacion de la sesion anterior. Con `key`, React desmonta y vuelve a
 * montar: no hay hueco que mostrar.
 */
function Asistente() {
  const { usuario } = useAuth();
  const [disponible, setDisponible] = useState(false);

  // Se pregunta una vez. Sin clave configurada el boton no se pinta: mejor
  // que no exista a que exista y no responda.
  useEffect(() => {
    let vigente = true;
    chatApi
      .estado()
      .then((r) => {
        if (vigente) setDisponible(Boolean(r.disponible));
      })
      .catch(() => {
        if (vigente) setDisponible(false);
      });
    return () => {
      vigente = false;
    };
  }, []);

  if (!disponible) return null;

  return <Conversador key={usuario?.id ?? "visitante"} />;
}

export default Asistente;
