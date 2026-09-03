const express = require("express");
const cors = require("cors");

const authRoutes = require("./routes/auth.routes");
const usuarioRoutes = require("./routes/usuario.routes");
const productoRoutes = require("./routes/producto.routes");
const servicioRoutes = require("./routes/servicio.routes");
const citaRoutes = require("./routes/cita.routes");

const app = express();

/* --------------------------- Middlewares base --------------------------- */

// CORS: permite que el frontend de Vite consuma la API desde otro puerto.
// Se acepta una lista separada por comas porque Vite cambia de puerto (5173,
// 5174...) cuando el anterior esta ocupado.
const ORIGENES = (process.env.CORS_ORIGIN || "http://localhost:5173")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);

app.use(
  cors({
    origin(origen, permitir) {
      // Sin cabecera Origin (Postman, curl) tambien se permite.
      if (!origen || ORIGENES.includes(origen)) return permitir(null, true);
      return permitir(new Error(`Origen no permitido por CORS: ${origen}`));
    },
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

app.use(express.json({ limit: "1mb" }));

/**
 * Aviso claro cuando el cuerpo no viene como JSON.
 *
 * Sin esto, una peticion enviada desde Postman con "form-data" o sin la
 * cabecera Content-Type llega con req.body vacio, y la respuesta seria
 * "el correo es obligatorio" aunque el correo si se haya escrito. El mensaje
 * confunde: aqui se indica el problema real.
 */
app.use((req, res, next) => {
  const llevaCuerpo = ["POST", "PUT", "PATCH"].includes(req.method);
  const tipo = req.headers["content-type"] || "";

  if (llevaCuerpo && !tipo.includes("application/json")) {
    return res.status(415).json({
      ok: false,
      mensaje:
        'El cuerpo debe enviarse como JSON. En Postman: pestana Body > raw > ' +
        'formato JSON (eso agrega la cabecera Content-Type: application/json).',
      recibido: tipo || "(sin cabecera Content-Type)",
    });
  }

  return next();
});

// Traza sencilla de cada peticion, util al probar con Postman.
app.use((req, _res, next) => {
  console.log(`${req.method} ${req.originalUrl}`);
  next();
});

/* -------------------------------- Rutas -------------------------------- */

app.get("/", (_req, res) => {
  res.json({
    ok: true,
    api: "AutoPrime API",
    version: "1.0.0",
    mensaje: "Backend funcionando",
    endpoints: {
      auth: "/api/auth",
      usuarios: "/api/usuarios",
      productos: "/api/productos",
      servicios: "/api/servicios",
      citas: "/api/citas",
    },
  });
});

app.use("/api/auth", authRoutes);
app.use("/api/usuarios", usuarioRoutes);
app.use("/api/productos", productoRoutes);
app.use("/api/servicios", servicioRoutes);
app.use("/api/citas", citaRoutes);

/* ------------------------- Manejo de errores --------------------------- */

// 404: ninguna ruta coincidio.
app.use((req, res) => {
  res.status(404).json({
    ok: false,
    mensaje: `La ruta ${req.method} ${req.originalUrl} no existe.`,
  });
});

// Cualquier error no controlado termina aqui.
// eslint-disable-next-line no-unused-vars
app.use((error, _req, res, _next) => {
  console.error("Error no controlado:", error);

  if (error.type === "entity.parse.failed") {
    return res.status(400).json({ ok: false, mensaje: "El JSON enviado no es valido." });
  }

  return res.status(500).json({
    ok: false,
    mensaje: "Error interno del servidor.",
    // El detalle solo se expone en desarrollo.
    detalle: process.env.NODE_ENV === "development" ? error.message : undefined,
  });
});

module.exports = app;
