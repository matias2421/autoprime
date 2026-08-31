const productoModel = require("../models/producto.model");
const { validarProducto } = require("../utils/validaciones");

/** GET /api/productos  — publico */
async function listar(req, res, next) {
  try {
    const productos = await productoModel.listar({
      familia: req.query.familia,
      estado: req.query.estado,
    });
    return res.json({ ok: true, total: productos.length, productos });
  } catch (error) {
    return next(error);
  }
}

/** GET /api/productos/:slug  — publico (acepta id o slug) */
async function obtener(req, res, next) {
  try {
    const clave = req.params.slug;
    const producto = /^\d+$/.test(clave)
      ? await productoModel.buscarPorId(clave)
      : await productoModel.buscarPorSlug(clave);

    if (!producto) {
      return res.status(404).json({ ok: false, mensaje: "Vehiculo no encontrado." });
    }
    return res.json({ ok: true, producto });
  } catch (error) {
    return next(error);
  }
}

/** POST /api/productos  — admin y empleado */
async function crear(req, res, next) {
  try {
    const { errores, datos } = validarProducto(req.body);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    if (await productoModel.existeSlug(datos.slug)) {
      return res.status(409).json({
        ok: false,
        mensaje: "Ya existe un vehiculo con ese slug.",
        errores: { slug: "Este slug ya esta en uso." },
      });
    }

    const producto = await productoModel.crear(datos);
    return res.status(201).json({ ok: true, mensaje: "Vehiculo creado.", producto });
  } catch (error) {
    return next(error);
  }
}

/** PUT /api/productos/:id  — admin y empleado */
async function actualizar(req, res, next) {
  try {
    const existente = await productoModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Vehiculo no encontrado." });
    }

    const { errores, datos } = validarProducto(req.body, true);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    if (datos.slug && (await productoModel.existeSlug(datos.slug, existente.id))) {
      return res.status(409).json({
        ok: false,
        mensaje: "Ese slug ya esta en uso.",
        errores: { slug: "Este slug ya esta en uso." },
      });
    }

    const producto = await productoModel.actualizar(existente.id, datos);
    return res.json({ ok: true, mensaje: "Vehiculo actualizado.", producto });
  } catch (error) {
    return next(error);
  }
}

/** DELETE /api/productos/:id  — solo admin */
async function eliminar(req, res, next) {
  try {
    const existente = await productoModel.buscarPorId(req.params.id);
    if (!existente) {
      return res.status(404).json({ ok: false, mensaje: "Vehiculo no encontrado." });
    }
    await productoModel.eliminar(existente.id);
    return res.json({ ok: true, mensaje: "Vehiculo eliminado." });
  } catch (error) {
    return next(error);
  }
}

module.exports = { listar, obtener, crear, actualizar, eliminar };
