const { pool } = require("../config/db");

/** Acceso a la tabla `productos` (los vehiculos del catalogo). */

const CAMPOS = `
  id, slug, marca, modelo, familia, base, lema, descripcion, imagen, anio,
  kilometraje, precio, unidades, motor, potencia, aceleracion, velocidad,
  transmision, traccion, estado, creado_en AS creadoEn
`;

/** Arma el objeto que espera el frontend (specs anidadas). */
function aSalida(fila) {
  if (!fila) return null;
  const { motor, potencia, aceleracion, velocidad, transmision, traccion, ...resto } = fila;
  return {
    ...resto,
    titulo: `${fila.marca} ${fila.modelo}`,
    precio: fila.precio === null ? null : Number(fila.precio),
    specs: { motor, potencia, aceleracion, velocidad, transmision, traccion },
  };
}

async function listar({ familia, estado } = {}) {
  let sql = `SELECT ${CAMPOS} FROM productos WHERE 1 = 1`;
  const valores = [];

  if (familia && familia !== "todos") {
    sql += " AND familia = ?";
    valores.push(familia);
  }
  if (estado) {
    sql += " AND estado = ?";
    valores.push(estado);
  }

  sql += " ORDER BY id";
  const [filas] = await pool.query(sql, valores);
  return filas.map(aSalida);
}

async function buscarPorId(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM productos WHERE id = ?`, [id]);
  return aSalida(filas[0]);
}

async function buscarPorSlug(slug) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} FROM productos WHERE slug = ?`, [slug]);
  return aSalida(filas[0]);
}

async function existeSlug(slug, excluirId = null) {
  const sql = excluirId
    ? "SELECT id FROM productos WHERE slug = ? AND id <> ?"
    : "SELECT id FROM productos WHERE slug = ?";
  const [filas] = await pool.query(sql, excluirId ? [slug, excluirId] : [slug]);
  return filas.length > 0;
}

async function crear(datos) {
  const columnas = Object.keys(datos);
  const marcadores = columnas.map(() => "?").join(", ");
  const [resultado] = await pool.query(
    `INSERT INTO productos (${columnas.join(", ")}) VALUES (${marcadores})`,
    columnas.map((c) => datos[c])
  );
  return buscarPorId(resultado.insertId);
}

async function actualizar(id, columnas) {
  const claves = Object.keys(columnas);
  if (claves.length === 0) return buscarPorId(id);

  const asignaciones = claves.map((c) => `${c} = ?`).join(", ");
  await pool.query(`UPDATE productos SET ${asignaciones} WHERE id = ?`, [
    ...claves.map((c) => columnas[c]),
    id,
  ]);
  return buscarPorId(id);
}

async function eliminar(id) {
  const [resultado] = await pool.query("DELETE FROM productos WHERE id = ?", [id]);
  return resultado.affectedRows > 0;
}

module.exports = {
  listar,
  buscarPorId,
  buscarPorSlug,
  existeSlug,
  crear,
  actualizar,
  eliminar,
};
