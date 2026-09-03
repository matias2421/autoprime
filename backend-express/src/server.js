require("dotenv").config();

const app = require("./app");
const { probarConexion } = require("./config/db");

const PORT = process.env.PORT || 3000;

/** Antes de escuchar, se comprueba que la base de datos responda. */
async function iniciar() {
  try {
    await probarConexion();
    console.log(`Base de datos "${process.env.DB_NAME}" conectada.`);
  } catch (error) {
    console.error("No se pudo conectar a la base de datos:", error.message);
    console.error("Revisa que MySQL este encendido (XAMPP) y que el .env sea correcto.");
    process.exit(1);
  }

  app.listen(PORT, () => {
    console.log(`Servidor iniciado en http://localhost:${PORT}`);
  });
}

iniciar();
