const { Router } = require("express");
const ctrl = require("../controllers/producto.controller");
const { verificarToken, permitirRoles } = require("../middlewares/auth.middleware");

const router = Router();

// Publicas: el catalogo se puede ver sin iniciar sesion.
router.get("/", ctrl.listar);
router.get("/:slug", ctrl.obtener);

// Protegidas
router.post("/", verificarToken, permitirRoles("administrador", "empleado"), ctrl.crear);
router.put("/:id", verificarToken, permitirRoles("administrador", "empleado"), ctrl.actualizar);
router.delete("/:id", verificarToken, permitirRoles("administrador"), ctrl.eliminar);

module.exports = router;
