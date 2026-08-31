/**
 * Validaciones del backend.
 *
 * Replican las reglas del frontend (frontend/src/utils/validaciones.js). Se
 * validan otra vez aqui a proposito: el frontend puede saltarse con Postman o
 * con las herramientas del navegador, asi que el servidor nunca debe confiar
 * en lo que le llega.
 */

const REGEX = {
  soloLetras: /^[A-Za-zAEIOUaeiouUuNnÀ-ſ\s'-]+$/,
  correo: /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/,
  soloDigitos: /^\d+$/,
  alfanumerico: /^[A-Za-z0-9]+$/,
  direccion: /^[A-Za-z0-9À-ſ\s#.,°_-]+$/,
  mayuscula: /[A-Z]/,
  minuscula: /[a-z]/,
  digito: /\d/,
  especial: /[^A-Za-z0-9]/,
  fechaISO: /^\d{4}-\d{2}-\d{2}$/,
  hora: /^([01]\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$/,
};

const TIPOS_DOCUMENTO = ["CC", "TI", "CE", "PA", "NIT"];
const ESTADOS_USUARIO = ["activo", "inactivo"];
const ESTADOS_CITA = ["pendiente", "confirmada", "cancelada", "completada"];
const FAMILIAS = ["gama", "edicion", "coleccion"];
const ESTADOS_PRODUCTO = ["disponible", "vendido", "inactivo"];

const LIMITES = {
  nombre: 40,
  apellido: 40,
  documento: 15,
  direccion: 80,
  telefono: 10,
  correo: 60,
  password: 32,
  notas: 300,
};

const texto = (valor) => (typeof valor === "string" ? valor.trim() : "");

/* -------------------------------------------------------------------------- */
/* Reglas individuales                                                        */
/* -------------------------------------------------------------------------- */

function validarNombre(valor, etiqueta = "El nombre") {
  const v = texto(valor);
  if (!v) return `${etiqueta} es obligatorio.`;
  if (v.length < 2) return `${etiqueta} debe tener al menos 2 caracteres.`;
  if (v.length > LIMITES.nombre)
    return `${etiqueta} no puede superar los ${LIMITES.nombre} caracteres.`;
  if (!REGEX.soloLetras.test(v)) return `${etiqueta} solo admite letras.`;
  return "";
}

function validarTipoDocumento(valor) {
  if (!valor) return "Selecciona un tipo de documento.";
  if (!TIPOS_DOCUMENTO.includes(valor)) return "Tipo de documento no valido.";
  return "";
}

/** El formato depende del tipo: el pasaporte admite letras, los demas no. */
function validarDocumento(valor, tipo) {
  const v = texto(valor);
  if (!v) return "El numero de documento es obligatorio.";
  if (!tipo) return "Primero selecciona el tipo de documento.";

  if (tipo === "PA") {
    if (!REGEX.alfanumerico.test(v))
      return "El pasaporte solo admite letras y numeros.";
    if (v.length < 6 || v.length > 15)
      return "El pasaporte debe tener entre 6 y 15 caracteres.";
    return "";
  }

  if (!REGEX.soloDigitos.test(v)) return "El documento solo admite numeros.";

  if (tipo === "NIT") {
    if (v.length < 9 || v.length > 10)
      return "El NIT debe tener entre 9 y 10 digitos.";
    return "";
  }

  if (v.length < 6 || v.length > 11)
    return "El documento debe tener entre 6 y 11 digitos.";
  return "";
}

function validarDireccion(valor) {
  const v = texto(valor);
  if (!v) return "La direccion es obligatoria.";
  if (v.length < 5) return "La direccion debe tener al menos 5 caracteres.";
  if (v.length > LIMITES.direccion)
    return `La direccion no puede superar los ${LIMITES.direccion} caracteres.`;
  if (!REGEX.direccion.test(v)) return "La direccion contiene caracteres no permitidos.";
  return "";
}

function validarTelefono(valor) {
  const v = texto(valor);
  if (!v) return "El telefono es obligatorio.";
  if (!REGEX.soloDigitos.test(v)) return "El telefono solo admite numeros.";
  if (v.length !== 10) return "El telefono debe tener exactamente 10 digitos.";
  if (!v.startsWith("3")) return "El celular en Colombia empieza por 3.";
  return "";
}

function validarCorreo(valor) {
  const v = texto(valor);
  if (!v) return "El correo electronico es obligatorio.";
  if (v.length > LIMITES.correo)
    return `El correo no puede superar los ${LIMITES.correo} caracteres.`;
  if (!REGEX.correo.test(v)) return "Formato de correo no valido.";
  return "";
}

function validarPassword(valor) {
  if (!valor) return "La contrasena es obligatoria.";
  if (valor.length < 8) return "La contrasena debe tener al menos 8 caracteres.";
  if (valor.length > LIMITES.password)
    return `La contrasena no puede superar los ${LIMITES.password} caracteres.`;
  if (/\s/.test(valor)) return "La contrasena no puede contener espacios.";
  if (!REGEX.mayuscula.test(valor)) return "La contrasena debe incluir una mayuscula.";
  if (!REGEX.minuscula.test(valor)) return "La contrasena debe incluir una minuscula.";
  if (!REGEX.digito.test(valor)) return "La contrasena debe incluir un numero.";
  if (!REGEX.especial.test(valor))
    return "La contrasena debe incluir un caracter especial.";
  return "";
}

/* -------------------------------------------------------------------------- */
/* Validaciones por entidad                                                   */
/* -------------------------------------------------------------------------- */

/** Devuelve { errores, datos }. `errores` vacio significa que todo paso. */
function validarRegistro(cuerpo = {}) {
  const errores = {};

  const e = (campo, mensaje) => {
    if (mensaje) errores[campo] = mensaje;
  };

  e("nombre", validarNombre(cuerpo.nombre, "El nombre"));
  e("apellido", validarNombre(cuerpo.apellido, "El apellido"));
  e("tipoDocumento", validarTipoDocumento(cuerpo.tipoDocumento));
  e("numeroDocumento", validarDocumento(cuerpo.numeroDocumento, cuerpo.tipoDocumento));
  e("direccion", validarDireccion(cuerpo.direccion));
  e("telefono", validarTelefono(cuerpo.telefono));
  e("correo", validarCorreo(cuerpo.correo));
  e("password", validarPassword(cuerpo.password));

  if (cuerpo.confirmarPassword !== undefined &&
      cuerpo.password !== cuerpo.confirmarPassword) {
    errores.confirmarPassword = "Las contrasenas no coinciden.";
  }

  return {
    errores,
    datos: {
      nombre: texto(cuerpo.nombre),
      apellido: texto(cuerpo.apellido),
      tipoDocumento: cuerpo.tipoDocumento,
      numeroDocumento: texto(cuerpo.numeroDocumento),
      direccion: texto(cuerpo.direccion),
      telefono: texto(cuerpo.telefono),
      correo: texto(cuerpo.correo).toLowerCase(),
      password: cuerpo.password,
    },
  };
}

function validarLogin(cuerpo = {}) {
  const errores = {};
  const correo = validarCorreo(cuerpo.correo);
  if (correo) errores.correo = correo;
  if (!cuerpo.password) errores.password = "La contrasena es obligatoria.";
  return {
    errores,
    datos: {
      correo: texto(cuerpo.correo).toLowerCase(),
      password: cuerpo.password,
    },
  };
}

/** Para PUT /usuarios/:id — solo valida los campos que vengan. */
function validarActualizacionUsuario(cuerpo = {}) {
  const errores = {};
  const datos = {};

  const revisar = (campo, columna, validador) => {
    if (cuerpo[campo] === undefined) return;
    const mensaje = validador(cuerpo[campo]);
    if (mensaje) errores[campo] = mensaje;
    else datos[columna] = texto(cuerpo[campo]);
  };

  revisar("nombre", "nombre", (v) => validarNombre(v, "El nombre"));
  revisar("apellido", "apellido", (v) => validarNombre(v, "El apellido"));
  revisar("direccion", "direccion", validarDireccion);
  revisar("telefono", "telefono", validarTelefono);

  if (cuerpo.correo !== undefined) {
    const mensaje = validarCorreo(cuerpo.correo);
    if (mensaje) errores.correo = mensaje;
    else datos.correo = texto(cuerpo.correo).toLowerCase();
  }

  if (cuerpo.tipoDocumento !== undefined || cuerpo.numeroDocumento !== undefined) {
    const tipo = cuerpo.tipoDocumento;
    const mensajeTipo = validarTipoDocumento(tipo);
    if (mensajeTipo) errores.tipoDocumento = mensajeTipo;

    const mensajeDoc = validarDocumento(cuerpo.numeroDocumento, tipo);
    if (mensajeDoc) errores.numeroDocumento = mensajeDoc;

    if (!mensajeTipo && !mensajeDoc) {
      datos.tipo_documento = tipo;
      datos.numero_documento = texto(cuerpo.numeroDocumento);
    }
  }

  if (cuerpo.estado !== undefined) {
    if (!ESTADOS_USUARIO.includes(cuerpo.estado)) {
      errores.estado = "El estado debe ser activo o inactivo.";
    } else {
      datos.estado = cuerpo.estado;
    }
  }

  if (cuerpo.rolId !== undefined) {
    const rol = Number(cuerpo.rolId);
    if (!Number.isInteger(rol) || rol < 1) errores.rolId = "Rol no valido.";
    else datos.rol_id = rol;
  }

  return { errores, datos };
}

function validarCita(cuerpo = {}) {
  const errores = {};

  const fecha = texto(cuerpo.fecha);
  if (!fecha) {
    errores.fecha = "Selecciona una fecha.";
  } else if (!REGEX.fechaISO.test(fecha)) {
    errores.fecha = "La fecha debe tener el formato AAAA-MM-DD.";
  } else {
    // No se permite agendar en el pasado.
    const hoy = new Date();
    const soloHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
    const [anio, mes, dia] = fecha.split("-").map(Number);
    const elegida = new Date(anio, mes - 1, dia);

    if (Number.isNaN(elegida.getTime())) {
      errores.fecha = "La fecha no es valida.";
    } else if (elegida < soloHoy) {
      errores.fecha = "No puedes agendar en una fecha pasada.";
    } else if (elegida.getDay() === 0) {
      errores.fecha = "Los domingos no atendemos.";
    } else {
      const limite = new Date(soloHoy);
      limite.setDate(limite.getDate() + 60);
      if (elegida > limite) errores.fecha = "Solo agendamos hasta 60 dias adelante.";
    }
  }

  const hora = texto(cuerpo.hora);
  if (!hora) errores.hora = "Selecciona una hora.";
  else if (!REGEX.hora.test(hora)) errores.hora = "La hora debe tener el formato HH:MM.";

  const servicioId = Number(cuerpo.servicioId);
  if (!Number.isInteger(servicioId) || servicioId < 1) {
    errores.servicioId = "Selecciona un servicio.";
  }

  let productoId = null;
  if (cuerpo.productoId !== undefined && cuerpo.productoId !== null &&
      cuerpo.productoId !== "") {
    productoId = Number(cuerpo.productoId);
    if (!Number.isInteger(productoId) || productoId < 1) {
      errores.productoId = "Vehiculo no valido.";
    }
  }

  const notas = texto(cuerpo.notas);
  if (notas.length > LIMITES.notas) {
    errores.notas = `Las notas no pueden superar los ${LIMITES.notas} caracteres.`;
  }

  return {
    errores,
    datos: { fecha, hora: hora.length === 5 ? `${hora}:00` : hora, servicioId, productoId, notas: notas || null },
  };
}

function validarProducto(cuerpo = {}, parcial = false) {
  const errores = {};
  const datos = {};

  const obligatorio = (campo, columna, etiqueta, max) => {
    if (parcial && cuerpo[campo] === undefined) return;
    const v = texto(cuerpo[campo]);
    if (!v) errores[campo] = `${etiqueta} es obligatorio.`;
    else if (max && v.length > max)
      errores[campo] = `${etiqueta} no puede superar los ${max} caracteres.`;
    else datos[columna] = v;
  };

  obligatorio("slug", "slug", "El slug", 60);
  obligatorio("marca", "marca", "La marca", 40);
  obligatorio("modelo", "modelo", "El modelo", 60);
  obligatorio("base", "base", "El vehiculo base", 60);
  obligatorio("lema", "lema", "El lema", 120);
  obligatorio("descripcion", "descripcion", "La descripcion");
  obligatorio("imagen", "imagen", "La imagen", 120);
  obligatorio("motor", "motor", "El motor", 60);
  obligatorio("potencia", "potencia", "La potencia", 20);
  obligatorio("aceleracion", "aceleracion", "La aceleracion", 20);
  obligatorio("velocidad", "velocidad", "La velocidad", 20);
  obligatorio("transmision", "transmision", "La transmision", 40);
  obligatorio("traccion", "traccion", "La traccion", 20);

  if (!parcial || cuerpo.familia !== undefined) {
    if (!FAMILIAS.includes(cuerpo.familia)) errores.familia = "Familia no valida.";
    else datos.familia = cuerpo.familia;
  }

  if (!parcial || cuerpo.anio !== undefined) {
    const anio = Number(cuerpo.anio);
    if (!Number.isInteger(anio) || anio < 1950 || anio > 2100)
      errores.anio = "El anio debe estar entre 1950 y 2100.";
    else datos.anio = anio;
  }

  if (!parcial || cuerpo.kilometraje !== undefined) {
    const km = Number(cuerpo.kilometraje);
    if (!Number.isInteger(km) || km < 0) errores.kilometraje = "Kilometraje no valido.";
    else datos.kilometraje = km;
  }

  if (!parcial || cuerpo.precio !== undefined) {
    if (cuerpo.precio === null || cuerpo.precio === "") {
      datos.precio = null;
    } else {
      const precio = Number(cuerpo.precio);
      if (!Number.isFinite(precio) || precio < 0) errores.precio = "Precio no valido.";
      else datos.precio = Math.round(precio);
    }
  }

  // Unidades fabricadas: vacio o null significa "serie no limitada".
  if (!parcial || cuerpo.unidades !== undefined) {
    if (cuerpo.unidades === null || cuerpo.unidades === "" || cuerpo.unidades === undefined) {
      datos.unidades = null;
    } else {
      const unidades = Number(cuerpo.unidades);
      if (!Number.isInteger(unidades) || unidades < 1)
        errores.unidades = "Las unidades deben ser un entero mayor que cero.";
      else datos.unidades = unidades;
    }
  }

  if (cuerpo.estado !== undefined) {
    if (!ESTADOS_PRODUCTO.includes(cuerpo.estado)) errores.estado = "Estado no valido.";
    else datos.estado = cuerpo.estado;
  }

  return { errores, datos };
}

module.exports = {
  REGEX,
  LIMITES,
  TIPOS_DOCUMENTO,
  ESTADOS_USUARIO,
  ESTADOS_CITA,
  FAMILIAS,
  ESTADOS_PRODUCTO,
  validarNombre,
  validarCorreo,
  validarPassword,
  validarTelefono,
  validarDocumento,
  validarRegistro,
  validarLogin,
  validarActualizacionUsuario,
  validarCita,
  validarProducto,
};
