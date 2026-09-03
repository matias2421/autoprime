const { pool } = require("../config/db");

/**
 * Acceso a la tabla `citas`.
 *
 * Las consultas devuelven ya unidos el nombre del cliente, del servicio y del
 * vehiculo, para que el panel no tenga que hacer peticiones adicionales.
 */

const CAMPOS = `
  c.id, c.usuario_id AS usuarioId, c.producto_id AS productoId,
  c.servicio_id AS servicioId, c.fecha, c.hora, c.estado, c.notas,
  c.creado_en AS creadoEn,
  CONCAT(u.nombre, ' ', u.apellido) AS cliente,
  u.correo AS clienteCorreo,
  u.telefono AS clienteTelefono,
  s.nombre AS servicio,
  s.duracion_min AS duracionMin,
  CONCAT(p.marca, ' ', p.modelo) AS vehiculo,
  p.slug AS vehiculoSlug
`;

const BASE = `
  FROM citas c
  JOIN usuarios u  ON u.id = c.usuario_id
  JOIN servicios s ON s.id = c.servicio_id
  LEFT JOIN productos p ON p.id = c.producto_id
`;

/** `usuarioId` limita el listado a las citas de ese cliente. */
async function listar({ usuarioId, estado, desde } = {}) {
  let sql = `SELECT ${CAMPOS} ${BASE} WHERE 1 = 1`;
  const valores = [];

  if (usuarioId) {
    sql += " AND c.usuario_id = ?";
    valores.push(usuarioId);
  }
  if (estado) {
    sql += " AND c.estado = ?";
    valores.push(estado);
  }
  if (desde) {
    sql += " AND c.fecha >= ?";
    valores.push(desde);
  }

  sql += " ORDER BY c.fecha DESC, c.hora DESC";
  const [filas] = await pool.query(sql, valores);
  return filas;
}

async function buscarPorId(id) {
  const [filas] = await pool.query(`SELECT ${CAMPOS} ${BASE} WHERE c.id = ?`, [id]);
  return filas[0] || null;
}

/** Horas ya tomadas para una fecha, para pintar el calendario en el frontend. */
async function horasOcupadas(fecha, productoId = null) {
  const sql = productoId
    ? `SELECT TIME_FORMAT(hora, '%H:%i') AS hora FROM citas
       WHERE fecha = ? AND producto_id = ? AND estado <> 'cancelada'`
    : `SELECT TIME_FORMAT(hora, '%H:%i') AS hora FROM citas
       WHERE fecha = ? AND estado <> 'cancelada'`;
  const valores = productoId ? [fecha, productoId] : [fecha];
  const [filas] = await pool.query(sql, valores);
  return filas.map((f) => f.hora);
}

async function existeCupo(fecha, hora, productoId) {
  const sql = productoId
    ? `SELECT id FROM citas WHERE fecha = ? AND hora = ? AND producto_id = ?
       AND estado <> 'cancelada'`
    : `SELECT id FROM citas WHERE fecha = ? AND hora = ? AND producto_id IS NULL
       AND estado <> 'cancelada'`;
  const valores = productoId ? [fecha, hora, productoId] : [fecha, hora];
  const [filas] = await pool.query(sql, valores);
  return filas.length > 0;
}

async function crear({ usuarioId, productoId, servicioId, fecha, hora, notas }) {
  const [resultado] = await pool.query(
    `INSERT INTO citas (usuario_id, producto_id, servicio_id, fecha, hora, notas)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [usuarioId, productoId, servicioId, fecha, hora, notas]
  );
  return buscarPorId(resultado.insertId);
}

async function cambiarEstado(id, estado) {
  await pool.query("UPDATE citas SET estado = ? WHERE id = ?", [estado, id]);
  return buscarPorId(id);
}

async function eliminar(id) {
  const [resultado] = await pool.query("DELETE FROM citas WHERE id = ?", [id]);
  return resultado.affectedRows > 0;
}

/** Conteos para el resumen de los paneles. */
async function resumen(usuarioId = null) {
  const sql = usuarioId
    ? `SELECT estado, COUNT(*) AS total FROM citas WHERE usuario_id = ? GROUP BY estado`
    : `SELECT estado, COUNT(*) AS total FROM citas GROUP BY estado`;
  const [filas] = await pool.query(sql, usuarioId ? [usuarioId] : []);

  const conteo = { pendiente: 0, confirmada: 0, cancelada: 0, completada: 0 };
  filas.forEach((f) => {
    conteo[f.estado] = Number(f.total);
  });
  return conteo;
}

module.exports = {
  listar,
  buscarPorId,
  horasOcupadas,
  existeCupo,
  crear,
  cambiarEstado,
  eliminar,
  resumen,
};
