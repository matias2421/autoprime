/**
 * Reglas de validación reutilizables.
 * Cada regla recibe (valor, todosLosValores) y devuelve un string con el
 * mensaje de error, o "" si el campo es válido.
 */

/* -------------------------------------------------------------------------- */
/* Expresiones regulares                                                      */
/* -------------------------------------------------------------------------- */
export const REGEX = {
  soloLetras: /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]+$/,
  correo: /^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/,
  soloDigitos: /^\d+$/,
  alfanumerico: /^[A-Za-z0-9]+$/,
  direccion: /^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s#.,°_-]+$/,
  mayuscula: /[A-Z]/,
  minuscula: /[a-z]/,
  digito: /\d/,
  especial: /[^A-Za-z0-9]/,
};

/* -------------------------------------------------------------------------- */
/* Sanitizadores: restringen los caracteres que el usuario puede escribir      */
/* -------------------------------------------------------------------------- */
export const soloLetras = (valor) =>
  valor.replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s'-]/g, "").replace(/\s{2,}/g, " ");

export const soloDigitos = (valor) => valor.replace(/\D/g, "");

export const soloAlfanumerico = (valor) => valor.replace(/[^A-Za-z0-9]/g, "");

export const sinEspacios = (valor) => valor.replace(/\s/g, "");

export const textoDireccion = (valor) =>
  valor.replace(/[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s#.,°_-]/g, "");

/* -------------------------------------------------------------------------- */
/* Catálogo de tipos de documento                                             */
/* -------------------------------------------------------------------------- */
export const TIPOS_DOCUMENTO = [
  { valor: "CC", etiqueta: "Cédula de ciudadanía" },
  { valor: "TI", etiqueta: "Tarjeta de identidad" },
  { valor: "CE", etiqueta: "Cédula de extranjería" },
  { valor: "PA", etiqueta: "Pasaporte" },
  { valor: "NIT", etiqueta: "NIT" },
];

/* -------------------------------------------------------------------------- */
/* Límites de longitud (se aplican también como maxLength en el input)         */
/* -------------------------------------------------------------------------- */
export const LIMITES = {
  nombre: 40,
  apellido: 40,
  documento: 15,
  direccion: 80,
  telefono: 10,
  correo: 60,
  password: 32,
  mensaje: 500,
  asunto: 60,
};

/* -------------------------------------------------------------------------- */
/* Reglas                                                                     */
/* -------------------------------------------------------------------------- */

const requerido = (valor, etiqueta) =>
  !valor || !String(valor).trim() ? `${etiqueta} es obligatorio.` : "";

export const validarNombre = (valor) => {
  const error = requerido(valor, "El nombre");
  if (error) return error;

  const limpio = valor.trim();
  if (limpio.length < 2) return "Debe tener al menos 2 caracteres.";
  if (limpio.length > LIMITES.nombre)
    return `No puede superar los ${LIMITES.nombre} caracteres.`;
  if (!REGEX.soloLetras.test(limpio))
    return "Solo se permiten letras, espacios, apóstrofos y guiones.";
  return "";
};

export const validarApellido = (valor) => {
  const error = validarNombre(valor);
  return error.replace("El nombre", "El apellido");
};

export const validarTipoDocumento = (valor) => {
  if (!valor) return "Selecciona un tipo de documento.";
  if (!TIPOS_DOCUMENTO.some((t) => t.valor === valor))
    return "Tipo de documento no válido.";
  return "";
};

/**
 * El formato válido depende del tipo de documento seleccionado:
 * el pasaporte admite letras, los demás solo dígitos.
 */
export const validarDocumento = (valor, valores = {}) => {
  const error = requerido(valor, "El número de documento");
  if (error) return error;

  const limpio = valor.trim();
  const tipo = valores.tipoDocumento;

  if (!tipo) return "Primero selecciona el tipo de documento.";

  if (tipo === "PA") {
    if (!REGEX.alfanumerico.test(limpio))
      return "El pasaporte solo admite letras y números.";
    if (limpio.length < 6 || limpio.length > 15)
      return "El pasaporte debe tener entre 6 y 15 caracteres.";
    return "";
  }

  if (!REGEX.soloDigitos.test(limpio)) return "Solo se permiten números.";

  if (tipo === "NIT") {
    if (limpio.length < 9 || limpio.length > 10)
      return "El NIT debe tener entre 9 y 10 dígitos.";
    return "";
  }

  if (limpio.length < 6 || limpio.length > 11)
    return "El documento debe tener entre 6 y 11 dígitos.";
  return "";
};

export const validarDireccion = (valor) => {
  const error = requerido(valor, "La dirección");
  if (error) return error;

  const limpio = valor.trim();
  if (limpio.length < 5) return "Debe tener al menos 5 caracteres.";
  if (limpio.length > LIMITES.direccion)
    return `No puede superar los ${LIMITES.direccion} caracteres.`;
  if (!REGEX.direccion.test(limpio))
    return "Contiene caracteres no permitidos.";
  return "";
};

export const validarTelefono = (valor) => {
  const error = requerido(valor, "El teléfono");
  if (error) return error;

  const limpio = valor.trim();
  if (!REGEX.soloDigitos.test(limpio)) return "Solo se permiten números.";
  if (limpio.length !== 10) return "Debe tener exactamente 10 dígitos.";
  if (!limpio.startsWith("3"))
    return "El número celular en Colombia empieza por 3.";
  return "";
};

export const validarCorreo = (valor) => {
  const error = requerido(valor, "El correo electrónico");
  if (error) return error;

  const limpio = valor.trim();
  if (limpio.length > LIMITES.correo)
    return `No puede superar los ${LIMITES.correo} caracteres.`;
  if (/\s/.test(limpio)) return "El correo no puede contener espacios.";
  if (!REGEX.correo.test(limpio))
    return "Formato no válido. Ejemplo: nombre@correo.com";
  return "";
};

export const validarPassword = (valor) => {
  const error = requerido(valor, "La contraseña");
  if (error) return error;

  if (valor.length < 8) return "Debe tener al menos 8 caracteres.";
  if (valor.length > LIMITES.password)
    return `No puede superar los ${LIMITES.password} caracteres.`;
  if (/\s/.test(valor)) return "No puede contener espacios.";
  if (!REGEX.mayuscula.test(valor)) return "Debe incluir una letra mayúscula.";
  if (!REGEX.minuscula.test(valor)) return "Debe incluir una letra minúscula.";
  if (!REGEX.digito.test(valor)) return "Debe incluir al menos un número.";
  if (!REGEX.especial.test(valor))
    return "Debe incluir un carácter especial (por ejemplo: ! @ # $).";
  return "";
};

export const validarConfirmacion = (valor, valores = {}) => {
  const error = requerido(valor, "La confirmación de contraseña");
  if (error) return error;
  if (valor !== valores.password) return "Las contraseñas no coinciden.";
  return "";
};

/** Validación relajada: en el login solo comprobamos que no esté vacía. */
export const validarPasswordLogin = (valor) => {
  const error = requerido(valor, "La contraseña");
  if (error) return error;
  if (valor.length < 8) return "Debe tener al menos 8 caracteres.";
  return "";
};

export const validarAsunto = (valor) => {
  if (!valor) return "Selecciona un asunto.";
  return "";
};

export const validarMensaje = (valor) => {
  const error = requerido(valor, "El mensaje");
  if (error) return error;

  const limpio = valor.trim();
  if (limpio.length < 15) return "Cuéntanos un poco más (mínimo 15 caracteres).";
  if (limpio.length > LIMITES.mensaje)
    return `No puede superar los ${LIMITES.mensaje} caracteres.`;
  return "";
};

/**
 * Nivel de seguridad de la contraseña (0 a 4) para el medidor visual.
 */
export const nivelPassword = (valor = "") => {
  let nivel = 0;
  if (valor.length >= 8) nivel += 1;
  if (REGEX.mayuscula.test(valor) && REGEX.minuscula.test(valor)) nivel += 1;
  if (REGEX.digito.test(valor)) nivel += 1;
  if (REGEX.especial.test(valor)) nivel += 1;
  return nivel;
};
