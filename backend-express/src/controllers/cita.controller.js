const citaModel = require("../models/cita.model");
const servicioModel = require("../models/servicio.model");
const productoModel = require("../models/producto.model");
const { validarCita, ESTADOS_CITA } = require("../utils/validaciones");

/** Franjas que atiende el concesionario. */
const HORARIO = [
  "08:00", "09:00", "10:00", "11:00",
  "14:00", "15:00", "16:00", "17:00",
];

/** Los sabados se cierra al mediodia. */
function franjasDe(fechaISO) {
  const [anio, mes, dia] = fechaISO.split("-").map(Number);
  const diaSemana = new Date(anio, mes - 1, dia).getDay();
  if (diaSemana === 0) return [];              // domingo cerrado
  if (diaSemana === 6) return HORARIO.slice(0, 4); // sabado solo manana
  return HORARIO;
}

/**
 * GET /api/citas/disponibilidad?fecha=YYYY-MM-DD&productoId=3
 * Publico: el frontend lo usa para pintar el calendario.
 */
async function disponibilidad(req, res, next) {
  try {
    const { fecha, productoId } = req.query;

    if (!fecha || !/^\d{4}-\d{2}-\d{2}$/.test(fecha)) {
      return res.status(400).json({
        ok: false,
        mensaje: "Indica una fecha con formato AAAA-MM-DD.",
      });
    }

    const franjas = franjasDe(fecha);
    const ocupadas = await citaModel.horasOcupadas(fecha, productoId || null);

    return res.json({
      ok: true,
      fecha,
      horas: franjas.map((hora) => ({
        hora,
        disponible: !ocupadas.includes(hora),
      })),
    });
  } catch (error) {
    return next(error);
  }
}

/**
 * GET /api/citas
 * El cliente ve solo las suyas; admin y empleado ven todas.
 */
async function listar(req, res, next) {
  try {
    const esCliente = req.usuario.rol === "cliente";
    const citas = await citaModel.listar({
      usuarioId: esCliente ? req.usuario.id : req.query.usuarioId,
      estado: req.query.estado,
      desde: req.query.desde,
    });
    return res.json({ ok: true, total: citas.length, citas });
  } catch (error) {
    return next(error);
  }
}

/** GET /api/citas/resumen */
async function resumen(req, res, next) {
  try {
    const esCliente = req.usuario.rol === "cliente";
    const conteo = await citaModel.resumen(esCliente ? req.usuario.id : null);
    return res.json({ ok: true, resumen: conteo });
  } catch (error) {
    return next(error);
  }
}

/**
 * POST /api/citas  (protegido)
 * El cliente elige fecha, hora, servicio y, opcionalmente, el vehiculo.
 */
async function crear(req, res, next) {
  try {
    const { errores, datos } = validarCita(req.body);
    if (Object.keys(errores).length > 0) {
      return res.status(400).json({ ok: false, mensaje: "Revisa los datos.", errores });
    }

    const servicio = await servicioModel.buscarPorId(datos.servicioId);
    if (!servicio || servicio.estado !== "activo") {
      return res.status(400).json({
        ok: false,
        mensaje: "El servicio seleccionado no esta disponible.",
        errores: { servicioId: "Servicio no valido." },
      });
    }

    if (datos.productoId) {
      const producto = await productoModel.buscarPorId(datos.productoId);
      if (!producto) {
        return res.status(400).json({
          ok: false,
          mensaje: "El vehiculo seleccionado no existe.",
          errores: { productoId: "Vehiculo no valido." },
        });
      }
    }

    // La hora debe pertenecer al horario de atencion de ese dia.
    const franjas = franjasDe(datos.fecha);
    const horaCorta = datos.hora.slice(0, 5);

    if (!franjas.includes(horaCorta)) {
      return res.status(400).json({
        ok: false,
        mensaje: "Esa hora esta fuera del horario de atencion.",
        errores: { hora: "Selecciona una hora del horario disponible." },
      });
    }

    if (await citaModel.existeCupo(datos.fecha, datos.hora, datos.productoId)) {
      return res.status(409).json({
        ok: false,
        mensaje: "Esa franja ya fue reservada. Elige otra hora.",
        errores: { hora: "Franja ocupada." },
      });
    }

    const cita = await citaModel.crear({
      usuarioId: req.usuario.id,
      productoId: datos.productoId,
      servicioId: datos.servicioId,
      fecha: datos.fecha,
      hora: datos.hora,
      notas: datos.notas,
    });

    return res.status(201).json({ ok: true, mensaje: "Cita agendada.", cita });
  } catch (error) {
    // Choque con la restriccion uq_cupo por dos peticiones simultaneas.
    if (error.code === "ER_DUP_ENTRY") {
      return res.status(409).json({
        ok: false,
        mensaje: "Esa franja acaba de ser reservada. Elige otra hora.",
        errores: { hora: "Franja ocupada." },
      });
    }
    return next(error);
  }
}

/** PATCH /api/citas/:id/estado */
async function cambiarEstado(req, res, next) {
  try {
    const { estado } = req.body;

    if (!ESTADOS_CITA.includes(estado)) {
      return res.status(400).json({
        ok: false,
        mensaje: `El estado debe ser uno de: ${ESTADOS_CITA.join(", ")}.`,
      });
    }

    const cita = await citaModel.buscarPorId(req.params.id);
    if (!cita) {
      return res.status(404).json({ ok: false, mensaje: "Cita no encontrada." });
    }

    // El cliente solo puede cancelar sus propias citas.
    if (req.usuario.rol === "cliente") {
      if (cita.usuarioId !== req.usuario.id) {
        return res.status(403).json({ ok: false, mensaje: "Esta cita no es tuya." });
      }
      if (estado !== "cancelada") {
        return res.status(403).json({
          ok: false,
          mensaje: "Solo puedes cancelar tus citas.",
        });
      }
    }

    const actualizada = await citaModel.cambiarEstado(cita.id, estado);
    return res.json({ ok: true, mensaje: `Cita ${estado}.`, cita: actualizada });
  } catch (error) {
    return next(error);
  }
}

/** DELETE /api/citas/:id  — solo admin */
async function eliminar(req, res, next) {
  try {
    const cita = await citaModel.buscarPorId(req.params.id);
    if (!cita) {
      return res.status(404).json({ ok: false, mensaje: "Cita no encontrada." });
    }
    await citaModel.eliminar(cita.id);
    return res.json({ ok: true, mensaje: "Cita eliminada." });
  } catch (error) {
    return next(error);
  }
}

module.exports = { disponibilidad, listar, resumen, crear, cambiarEstado, eliminar };
