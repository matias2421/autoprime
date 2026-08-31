const mysql = require("mysql2/promise");

/**
 * Pool de conexiones a MySQL.
 *
 * Se usa un pool en lugar de abrir y cerrar una conexion por peticion: las
 * conexiones se reutilizan, que es lo apropiado para una API que atiende
 * varias peticiones al tiempo.
 */
const pool = mysql.createPool({
  host: process.env.DB_HOST || "localhost",
  port: Number(process.env.DB_PORT) || 3306,
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME || "autoprime",
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  charset: "utf8mb4",
  dateStrings: true, // devuelve DATE como "2026-09-01" y no como objeto Date
});

/** Comprueba la conexion al arrancar el servidor. */
async function probarConexion() {
  const conexion = await pool.getConnection();
  try {
    await conexion.ping();
    return true;
  } finally {
    conexion.release();
  }
}

module.exports = { pool, probarConexion };
