const { pool } = require("../config/db");

/**
 * Acceso a la tabla `usuarios`.
 *
 * Todas las consultas usan parametros (?) en lugar de concatenar cadenas, para
 * evitar inyeccion SQL. `password_hash` solo sale de la base de datos en
 * `buscarPorCorreoConPassword`, que es la unica funcion que lo necesita.
 */

// Columnas publicas: nunca incluyen el hash de la contrasena.
const CAMPOS = `
  u.id, u.nombre, u.apellido, u.tipo_documento AS tipoDocumento,
  u.numero_documento AS numeroDocumento, u.direccion, u.telefono, u.correo,
  u.rol_id AS rolId, r.nombre AS rol, u.estado, u.creado_en AS creadoEn
`;

async function listar({ rol, estado, buscar } = {}) {
  let sql = `SELECT ${CAMPOS} FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE 1 = 1`;
  const valores = [];

  if (rol) {
    sql += " AND r.nombre = ?";
    valores.push(rol);
  }
  if (estado) {
    sql += " AND u.estado = ?";
    valores.push(estado);
  }
  if (buscar) {
    sql += " AND (u.nombre LIKE ? OR u.apellido LIKE ? OR u.correo LIKE ? OR u.numero_documento LIKE ?)";
    const patron = `%${buscar}%`;
    valores.push(patron, patron, patron, patron);
  }

  sql += " ORDER BY u.creado_en DESC";
  const [filas] = await pool.query(sql, valores);
  return filas;
}

async function buscarPorId(id) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS} FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE u.id = ?`,
    [id]
  );
  return filas[0] || null;
}

/** Solo para el login: incluye el hash para poder compararlo. */
async function buscarPorCorreoConPassword(correo) {
  const [filas] = await pool.query(
    `SELECT ${CAMPOS}, u.password_hash AS passwordHash
     FROM usuarios u JOIN roles r ON r.id = u.rol_id
     WHERE u.correo = ?`,
    [correo]
  );
  return filas[0] || null;
}

async function existeCorreo(correo, excluirId = null) {
  const sql = excluirId
    ? "SELECT id FROM usuarios WHERE correo = ? AND id <> ?"
    : "SELECT id FROM usuarios WHERE correo = ?";
  const [filas] = await pool.query(sql, excluirId ? [correo, excluirId] : [correo]);
  return filas.length > 0;
}

async function existeDocumento(tipo, numero, excluirId = null) {
  const sql = excluirId
    ? "SELECT id FROM usuarios WHERE tipo_documento = ? AND numero_documento = ? AND id <> ?"
    : "SELECT id FROM usuarios WHERE tipo_documento = ? AND numero_documento = ?";
  const valores = excluirId ? [tipo, numero, excluirId] : [tipo, numero];
  const [filas] = await pool.query(sql, valores);
  return filas.length > 0;
}

/** Recibe el hash ya calculado; este modelo nunca ve la contrasena original. */
async function crear(datos, passwordHash, rolId) {
  const [resultado] = await pool.query(
    `INSERT INTO usuarios
      (nombre, apellido, tipo_documento, numero_documento, direccion,
       telefono, correo, password_hash, rol_id)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      datos.nombre,
      datos.apellido,
      datos.tipoDocumento,
      datos.numeroDocumento,
      datos.direccion,
      datos.telefono,
      datos.correo,
      passwordHash,
      rolId,
    ]
  );
  return buscarPorId(resultado.insertId);
}

async function actualizar(id, columnas) {
  const claves = Object.keys(columnas);
  if (claves.length === 0) return buscarPorId(id);

  const asignaciones = claves.map((c) => `${c} = ?`).join(", ");
  await pool.query(`UPDATE usuarios SET ${asignaciones} WHERE id = ?`, [
    ...claves.map((c) => columnas[c]),
    id,
  ]);
  return buscarPorId(id);
}

async function cambiarEstado(id, estado) {
  await pool.query("UPDATE usuarios SET estado = ? WHERE id = ?", [estado, id]);
  return buscarPorId(id);
}

async function eliminar(id) {
  const [resultado] = await pool.query("DELETE FROM usuarios WHERE id = ?", [id]);
  return resultado.affectedRows > 0;
}

async function idDeRol(nombreRol) {
  const [filas] = await pool.query("SELECT id FROM roles WHERE nombre = ?", [nombreRol]);
  return filas[0] ? filas[0].id : null;
}

async function permisosDeRol(rolId) {
  const [filas] = await pool.query(
    `SELECT p.nombre FROM permisos p
     JOIN rol_permiso rp ON rp.permiso_id = p.id
     WHERE rp.rol_id = ?`,
    [rolId]
  );
  return filas.map((f) => f.nombre);
}

module.exports = {
  listar,
  buscarPorId,
  buscarPorCorreoConPassword,
  existeCorreo,
  existeDocumento,
  crear,
  actualizar,
  cambiarEstado,
  eliminar,
  idDeRol,
  permisosDeRol,
};
