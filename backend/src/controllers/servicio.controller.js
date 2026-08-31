const servicioModel = require("../models/servicio.model");

/** GET /api/servicios  — publico (solo los activos) */
async function listar(req, res, next) {
  try {
    const incluirTodos = req.usuario && req.usuario.rol !== "cliente";
    const servicios = await servicioModel.listar({ soloActivos: !incluirTodos });
    return res.json({ ok: true, total: servicios.length, servicios });
  } catch (error) {
    return next(error);
  }
}

/** GET /api/servicios/:id */
async function obtener(req, res, next) {
  try {
    const servicio = await servicioModel.buscarPorId(req.params.id);
    if (!servicio) {
      return res.status(404).json({ ok: false, mensaje: "Servicio no encontrado." });
    }
    return res.json({ ok: true, servicio });
  } catch (error) {
    return next(error);
  }
}

function validar(cuerpo, parcial = false) {
  const errores = {};
  const datos = {};

  if (!parcial || cuerpo.nombre !== undefined) {
    const nombre = (cuerpo.nombre || "").trim();
    if (!nombre) errores.nombre = "El nombre es obligatorio.";
    else if (nombre.length > 60) errores.nombre = "Maximo 60 caracteres.";
    else datos.nombre = nombre;
  }

  if (!parcial || cuerpo.descripcion !== undefined) {
    const desc = (cuerpo.descripcion || "").trim();
    if (!desc) errores.descripcion = "La descripcion es obligatoria.";
    else if (desc.length > 200) errores.descripcion = "Maximo 200 caracteres.";
    else datos.descripcion = desc;
  }

  if (cuerpo.duracionMin !== undefined) {
    const dur = Number(cuerpo.duracionMin);
    if (!Number.isInteger(dur) || dur < 15 || dur > 480)
      errores.duracionMin = "La duracion debe estar entre 15 y 480 minutos.";
    else datos.duracion_min = dur;
  }

  if (cuerpo.precio !== undefined) {
    const precio = Number(cuerpo.precio);
    if (!Number.isFinite(precio) || precio < 0) errores.precio = "Precio no valido.";
    else datos.precio = Math.round(precio);
  }

  if (cuerpo.estado !== undefined) {
    if (!["activo", "inactivo"].includes(cuerpo.estado))
      errores.estado = "El estado debe ser activo o inactivo.";
    else datos.estado = cuerpo.estado;
  }

  return { errores, datos };
}

/** POST /api/servicios  — admin y empleado */
async function crear(req, res, next) {
  try {
    const { errores, datos } = validar(req.body);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    const servicio = await servicioModel.crear({
      nombre: datos.nombre,
      descripcion: datos.descripcion,
      duracionMin: datos.duracion_min,
      precio: datos.precio,
    });
    return res.status(201).json({ ok: true, mensaje: "Servicio creado.", servicio });
  } catch (error) {
    return next(error);
  }
}

/** PUT /api/servicios/:id */
async function actualizar(req, res, next) {
  try {
    const existente = await servicioModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Servicio no encontrado." });
    }

    const { errores, datos } = validar(req.body, true);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    const servicio = await servicioModel.actualizar(existente.id, datos);
    return res.json({ ok: true, mensaje: "Servicio actualizado.", servicio });
  } catch (error) {
    return next(error);
  }
}

/** DELETE /api/servicios/:id  — solo admin */
async function eliminar(req, res, next) {
  try {
    const existente = await servicioModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Servicio no encontrado." });
    }
    await servicioModel.eliminar(existente.id);
    return res.json({ ok: true, mensaje: "Servicio eliminado." });
  } catch (error) {
    if (error.code === "ER_ROW_IS_REFERENCED_2") {
      return res.status(409).json({
        ok: false,
        mensaje: "No se puede eliminar: hay citas asociadas. Inactivalo en su lugar.",
      });
    }
    return next(error);
  }
}

module.exports = { listar, obtener, crear, actualizar, eliminar };
