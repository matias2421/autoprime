require("dotenv").config({ path: `${__dirname}/../.env` });

const bcrypt = require("bcrypt");
const { pool } = require("../src/config/db");

/**
 * Crea los usuarios de prueba (uno por rol) con la contrasena ya hasheada.
 *
 * Se hace desde Node y no desde el .sql a proposito: asi la contrasena nunca
 * queda escrita en texto plano dentro del script de la base de datos.
 *
 * Ejecutar:  npm run seed
 */
const RONDAS = Number(process.env.BCRYPT_ROUNDS) || 10;

const USUARIOS = [
  {
    nombre: "Jose Matias",
    apellido: "Agudelo Bolivar",
    tipo_documento: "CC",
    numero_documento: "1088111222",
    direccion: "Av. Las Americas 45-12",
    telefono: "3001112233",
    correo: "admin@autoprime.com.co",
    password: "Admin2026!",
    rol: "administrador",
  },
  {
    nombre: "Carolina",
    apellido: "Rivera Osorio",
    tipo_documento: "CC",
    numero_documento: "1088333444",
    direccion: "Carrera 12 34-56",
    telefono: "3002223344",
    correo: "empleado@autoprime.com.co",
    password: "Empleado2026!",
    rol: "empleado",
  },
  {
    nombre: "Andres",
    apellido: "Zapata Molina",
    tipo_documento: "CC",
    numero_documento: "1088555666",
    direccion: "Calle 45 12-30, Barrio Centro",
    telefono: "3003334455",
    correo: "cliente@autoprime.com.co",
    password: "Cliente2026!",
    rol: "cliente",
  },
];

async function main() {
  const [roles] = await pool.query("SELECT id, nombre FROM roles");
  const idPorRol = Object.fromEntries(roles.map((r) => [r.nombre, r.id]));

  for (const u of USUARIOS) {
    const hash = await bcrypt.hash(u.password, RONDAS);

    await pool.query(
      `INSERT INTO usuarios
        (nombre, apellido, tipo_documento, numero_documento, direccion,
         telefono, correo, password_hash, rol_id)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)`,
      [
        u.nombre, u.apellido, u.tipo_documento, u.numero_documento,
        u.direccion, u.telefono, u.correo, hash, idPorRol[u.rol],
      ]
    );

    console.log(`  ${u.rol.padEnd(15)} ${u.correo.padEnd(30)} ${u.password}`);
  }

  console.log("\nUsuarios de prueba listos. Las contrasenas quedaron hasheadas con bcrypt.");
  await pool.end();
}

main().catch((error) => {
  console.error("Fallo el seed:", error.message);
  process.exit(1);
});
