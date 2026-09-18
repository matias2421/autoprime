/**
 * Cliente HTTP de la API.
 *
 * Centraliza el envio del token JWT y la lectura de errores, para que los
 * componentes no repitan la misma logica de fetch en cada pantalla.
 */

// El backend pasa a ser FastAPI (cuarto avance) y escucha en el 8000.
// La URL real se toma de VITE_API_URL cuando esta definida.
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const CLAVE_TOKEN = "autoprime:token";

export const guardarToken = (token, recordar = false) => {
  const almacen = recordar ? window.localStorage : window.sessionStorage;
  try {
    almacen.setItem(CLAVE_TOKEN, token);
  } catch {
    /* almacenamiento no disponible (modo privado) */
  }
};

export const obtenerToken = () => {
  try {
    return (
      window.sessionStorage.getItem(CLAVE_TOKEN) ||
      window.localStorage.getItem(CLAVE_TOKEN)
    );
  } catch {
    return null;
  }
};

export const borrarToken = () => {
  try {
    window.sessionStorage.removeItem(CLAVE_TOKEN);
    window.localStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* almacenamiento no disponible */
  }
};

/** Error de API que conserva el codigo HTTP y los errores por campo. */
export class ErrorApi extends Error {
  constructor(mensaje, estado, errores) {
    super(mensaje);
    this.name = "ErrorApi";
    this.estado = estado;
    this.errores = errores || {};
    this.codigo = null;
  }
}

async function peticion(ruta, { metodo = "GET", cuerpo, autenticado = true } = {}) {
  const cabeceras = {};
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";

  if (autenticado) {
    const token = obtenerToken();
    if (token) cabeceras.Authorization = `Bearer ${token}`;
  }

  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    // El servidor no respondio: normalmente el backend esta apagado.
    throw new ErrorApi(
      "No pudimos conectar con el servidor. Verifica que el backend este encendido.",
      0
    );
  }

  let datos = null;
  try {
    datos = await respuesta.json();
  } catch {
    // La respuesta no traia cuerpo JSON (por ejemplo un 204).
  }

  if (!respuesta.ok) {
    /*
     * FastAPI devuelve los errores como {codigo, mensaje, ruta, detalles},
     * donde `detalles` es una lista [{campo, problema}]. Los formularios de
     * la app esperan un objeto {campo: mensaje} para marcar cada input, asi
     * que la lista se aplana aqui y no en cada pantalla.
     */
    const errores = Array.isArray(datos?.detalles)
      ? Object.fromEntries(datos.detalles.map((d) => [d.campo, d.problema]))
      : datos?.errores;

    const fallo = new ErrorApi(
      datos?.mensaje || `Error ${respuesta.status}`,
      respuesta.status,
      errores
    );
    // `codigo` es estable y sirve para decidir en el frontend; el mensaje
    // puede cambiar de redaccion.
    fallo.codigo = datos?.codigo ?? `http_${respuesta.status}`;
    throw fallo;
  }

  return datos;
}

export const api = {
  get: (ruta, opciones) => peticion(ruta, { ...opciones, metodo: "GET" }),
  post: (ruta, cuerpo, opciones) => peticion(ruta, { ...opciones, metodo: "POST", cuerpo }),
  put: (ruta, cuerpo, opciones) => peticion(ruta, { ...opciones, metodo: "PUT", cuerpo }),
  patch: (ruta, cuerpo, opciones) => peticion(ruta, { ...opciones, metodo: "PATCH", cuerpo }),
  delete: (ruta, opciones) => peticion(ruta, { ...opciones, metodo: "DELETE" }),
};

/* -------------------------------------------------------------------------- */
/* Endpoints agrupados por recurso                                            */
/* -------------------------------------------------------------------------- */

export const authApi = {
  registro: (datos) => api.post("/auth/registro", datos, { autenticado: false }),
  login: (correo, password) =>
    api.post("/auth/login", { correo, password }, { autenticado: false }),
  perfil: () => api.get("/auth/perfil"),

  // Recuperacion de contrasena olvidada: dos pasos, dos peticiones.
  // Ninguna lleva token de sesion; precisamente se usan cuando no se puede
  // iniciar sesion.
  recuperar: (correo) =>
    api.post("/auth/recuperar", { correo }, { autenticado: false }),
  restablecer: (datos) =>
    api.post("/auth/restablecer", datos, { autenticado: false }),
};

export const usuariosApi = {
  listar: (filtros = {}) => {
    const q = new URLSearchParams(
      Object.entries(filtros).filter(([, v]) => v)
    ).toString();
    return api.get(`/usuarios${q ? `?${q}` : ""}`);
  },
  crear: (datos) => api.post("/usuarios", datos),
  actualizar: (id, datos) => api.put(`/usuarios/${id}`, datos),
  cambiarEstado: (id, estado) => api.patch(`/usuarios/${id}/estado`, { estado }),
  eliminar: (id) => api.delete(`/usuarios/${id}`),

  // Selector de comprador para el mostrador. Devuelve solo clientes
  // activos y cuatro campos de cada uno: el empleado que registra una
  // venta no necesita la ficha completa de todo el mundo.
  clientes: (buscar) =>
    api.get(`/usuarios/clientes${buscar ? `?buscar=${encodeURIComponent(buscar)}` : ""}`),
};

export const productosApi = {
  listar: (familia) =>
    api.get(`/productos${familia && familia !== "todos" ? `?familia=${familia}` : ""}`, {
      autenticado: false,
    }),
  obtener: (slug) => api.get(`/productos/${slug}`, { autenticado: false }),
  crear: (datos) => api.post("/productos", datos),
  actualizar: (id, datos) => api.put(`/productos/${id}`, datos),
  eliminar: (id) => api.delete(`/productos/${id}`),
};

export const serviciosApi = {
  listar: () => api.get("/servicios", { autenticado: false }),
};

export const citasApi = {
  disponibilidad: (fecha, productoId) => {
    const q = new URLSearchParams({ fecha });
    if (productoId) q.set("productoId", productoId);
    return api.get(`/citas/disponibilidad?${q}`, { autenticado: false });
  },
  listar: (filtros = {}) => {
    const q = new URLSearchParams(
      Object.entries(filtros).filter(([, v]) => v)
    ).toString();
    return api.get(`/citas${q ? `?${q}` : ""}`);
  },
  resumen: () => api.get("/citas/resumen"),
  crear: (datos) => api.post("/citas", datos),
  cambiarEstado: (id, estado) => api.patch(`/citas/${id}/estado`, { estado }),
  eliminar: (id) => api.delete(`/citas/${id}`),
};

/* -------------------------------------------------------------------------- */
/* Quinto avance                                                              */
/* -------------------------------------------------------------------------- */

/** Arma una cadena de consulta descartando lo vacio. */
const consulta = (filtros = {}) => {
  const pares = Object.entries(filtros).filter(
    ([, v]) => v !== "" && v !== null && v !== undefined
  );
  const q = new URLSearchParams(pares).toString();
  return q ? `?${q}` : "";
};

/**
 * Descarga un archivo de la API (PDF o Excel).
 *
 * No pasa por `peticion` porque aquella da por hecho que la respuesta es JSON
 * y aqui el cuerpo son octetos. Y no se puede usar un <a href> normal: la
 * descarga va autenticada, y un enlace no lleva la cabecera Authorization.
 * Asi que se pide con fetch, se convierte en un Blob y se dispara un enlace
 * temporal apuntando a ese Blob.
 *
 * El nombre del archivo lo pone el servidor en `Content-Disposition`. El
 * backend expone esa cabecera a proposito; si no lo hiciera, el navegador se
 * la ocultaria a JavaScript por venir de otro origen.
 */
export async function descargar(ruta, nombrePorDefecto) {
  const token = obtenerToken();
  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    throw new ErrorApi(
      "No pudimos conectar con el servidor para preparar la descarga.",
      0
    );
  }

  if (!respuesta.ok) {
    // Un error si viene en JSON, aunque la peticion pedia un archivo.
    let datos = null;
    try {
      datos = await respuesta.json();
    } catch {
      /* el error tampoco era JSON */
    }
    const fallo = new ErrorApi(
      datos?.mensaje || `No se pudo generar el archivo (${respuesta.status}).`,
      respuesta.status
    );
    fallo.codigo = datos?.codigo ?? `http_${respuesta.status}`;
    throw fallo;
  }

  const cabecera = respuesta.headers.get("Content-Disposition") || "";
  const coincidencia = cabecera.match(/filename="?([^"]+)"?/i);
  const nombre = coincidencia ? coincidencia[1] : nombrePorDefecto;

  const blob = await respuesta.blob();
  const url = URL.createObjectURL(blob);

  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();

  // Sin revocar, el Blob se queda en memoria hasta recargar la pagina. Con
  // un reporte de varios megas y unas cuantas descargas, se nota.
  URL.revokeObjectURL(url);

  return nombre;
}

export const ventasApi = {
  listar: (filtros) => api.get(`/ventas${consulta(filtros)}`),
  obtener: (id) => api.get(`/ventas/${id}`),
  resumen: (filtros) => api.get(`/ventas/resumen${consulta(filtros)}`),
  crear: (datos) => api.post("/ventas", datos),
  cambiarEstado: (id, estado) => api.patch(`/ventas/${id}/estado`, { estado }),
  eliminar: (id) => api.delete(`/ventas/${id}`),
};

export const facturasApi = {
  listar: (filtros) => api.get(`/facturas${consulta(filtros)}`),
  obtener: (id) => api.get(`/facturas/${id}`),
  emitir: (ventaId) => api.post(`/facturas/venta/${ventaId}`),
  anular: (id) => api.patch(`/facturas/${id}/anular`),
  descargar: (id, numero) => descargar(`/facturas/${id}/pdf`, `${numero}.pdf`),
};

export const reportesApi = {
  panel: () => api.get("/reportes/panel"),
  ventas: (filtros) => api.get(`/reportes/ventas${consulta(filtros)}`),
  ventasPdf: (filtros) =>
    descargar(`/reportes/ventas/pdf${consulta(filtros)}`, "reporte_ventas.pdf"),
  ventasExcel: (filtros) =>
    descargar(`/reportes/ventas/excel${consulta(filtros)}`, "reporte_ventas.xlsx"),
};

export const pqrApi = {
  listar: (filtros) => api.get(`/pqr${consulta(filtros)}`),
  obtener: (id) => api.get(`/pqr/${id}`),
  resumen: () => api.get("/pqr/resumen"),
  crear: (datos) => api.post("/pqr", datos),
  responder: (id, datos) => api.patch(`/pqr/${id}/responder`, datos),
  cambiarEstado: (id, estado) => api.patch(`/pqr/${id}/estado`, { estado }),
  eliminar: (id) => api.delete(`/pqr/${id}`),
};

export const chatApi = {
  // Publicos: el chat atiende tambien a quien no ha iniciado sesion. Van con
  // `autenticado: true` de todos modos porque, si HAY token, la conversacion
  // debe quedar asociada a la cuenta; el backend lo trata como opcional.
  estado: () => api.get("/chat/estado", { autenticado: false }),
  abrir: (titulo) => api.post("/chat/conversaciones", { titulo }),
  escribir: (conversacionId, contenido) =>
    api.post(`/chat/conversaciones/${conversacionId}/mensajes`, { contenido }),
  listar: (filtros) => api.get(`/chat/conversaciones${consulta(filtros)}`),
  leer: (id) => api.get(`/chat/conversaciones/${id}`),
  eliminar: (id) => api.delete(`/chat/conversaciones/${id}`),
};
