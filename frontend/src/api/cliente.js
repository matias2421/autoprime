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
