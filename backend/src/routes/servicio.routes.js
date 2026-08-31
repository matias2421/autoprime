const { Router } = require("express");
const ctrl = require("../controllers/servicio.controller");
const { verificarToken, permitirRoles } = require("../middlewares/auth.middleware");

const router = Router();

router.get("/", ctrl.listar);
router.get("/:id", ctrl.obtener);

router.post("/", verificarToken, permitirRoles("administrador", "empleado"), ctrl.crear);
router.put("/:id", verificarToken, permitirRoles("administrador", "empleado"), ctrl.actualizar);
router.delete("/:id", verificarToken, permitirRoles("administrador"), ctrl.eliminar);

module.exports = router;
