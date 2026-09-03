const { pool } = require("../config/db");

/** Acceso a la tabla `servicios` (lo que un cliente puede agendar). */

const CAMPOS = `
  id, nombre, descripcion, duracion_min AS duracionMin, precio, estado
`;

async function listar({ soloActivos = false } = {}) {
  const sql = soloActivos
    ? `SELECT ${CAMPOS} FROM servicios WHERE estado = 'activo' ORDER BY id`
    : `SELECT ${CAMPOS} FROM servicios ORDER BY id`;
  const [filas] = await pool.query(sql);
  return filas.map((f) => ({ ...f, precio: Number(f.precio) }));
}

async function buscarPorId(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM servicios WHERE id = ?`, [id]);
  if (!filas[0]) return null;
  return { ...filas[0], precio: Number(filas[0].precio) };
}

async function crear({ nombre, descripcion, duracionMin, precio }) {
  const [resultado] = await pool.query(
    `INSERT INTO servicios (nombre, descripcion, duracion_min, precio)
     VALUES (?, ?, ?, ?)`,
    [nombre, descripcion, duracionMin || 60, precio || 0]
  );
  return buscarPorId(resultado.insertId);
}

async function actualizar(id, columnas) {
  const claves = Object.keys(columnas);
  if (claves.length === 0) return buscarPorId(id);

  const asignaciones = claves.map((c) => `${c} = ?`).join(", ");
  await pool.query(`UPDATE servicios SET ${asignaciones} WHERE id = ?`, [
    ...claves.map((c) => columnas[c]),
    id,
  ]);
  return buscarPorId(id);
}

async function eliminar(id) {
  const [resultado] = await pool.query("DELETE FROM servicios WHERE id = ?", [id]);
  return resultado.affectedRows > 0;
}

module.exports = { listar, buscarPorId, crear, actualizar, eliminar };
