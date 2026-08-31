import { useCallback, useState } from "react";
import Button from "../../components/ui/Button";
import Icono from "../../components/ui/Icono";
import Input from "../../components/ui/Input";
import Modal from "../../components/ui/Modal";
import Select from "../../components/ui/Select";
import { PanelLayout, Tarjeta, Aviso, Estado } from "../../components/panel/PanelLayout";
import { citasApi, usuariosApi } from "../../api/cliente";
import { useAuth } from "../../hooks/useAuth";
import { useCarga } from "../../hooks/useCarga";
import {
  LIMITES,
  TIPOS_DOCUMENTO,
  soloAlfanumerico,
  soloDigitos,
  soloLetras,
  textoDireccion,
  sinEspacios,
  validarApellido,
  validarCorreo,
  validarDireccion,
  validarDocumento,
  validarNombre,
  validarPassword,
  validarTelefono,
  validarTipoDocumento,
} from "../../utils/validaciones";

const ROLES = [
  { valor: "administrador", etiqueta: "Administrador" },
  { valor: "empleado", etiqueta: "Empleado" },
  { valor: "cliente", etiqueta: "Cliente" },
];

const VACIO = {
  nombre: "",
  apellido: "",
  tipoDocumento: "",
  numeroDocumento: "",
  direccion: "",
  telefono: "",
  correo: "",
  password: "",
  rol: "cliente",
};

const SANITIZADORES = {
  nombre: soloLetras,
  apellido: soloLetras,
  numeroDocumento: soloAlfanumerico,
  direccion: textoDireccion,
  telefono: soloDigitos,
  correo: sinEspacios,
  password: sinEspacios,
};

/** Valida el formulario del modal. En edicion la contrasena no se pide. */
function validarFormulario(datos, editando) {
  const errores = {};
  const poner = (campo, mensaje) => {
    if (mensaje) errores[campo] = mensaje;
  };

  poner("nombre", validarNombre(datos.nombre));
  poner("apellido", validarApellido(datos.apellido));
  poner("tipoDocumento", validarTipoDocumento(datos.tipoDocumento));
  poner("numeroDocumento", validarDocumento(datos.numeroDocumento, datos));
  poner("direccion", validarDireccion(datos.direccion));
  poner("telefono", validarTelefono(datos.telefono));
  poner("correo", validarCorreo(datos.correo));
  if (!editando) poner("password", validarPassword(datos.password));

  return errores;
}

/**
 * Panel de administrador (requisito 10).
 * CRUD completo de usuarios: ver, agregar, editar, cambiar estado y eliminar.
 */
function PanelAdmin() {
  const { usuario: yo } = useAuth();

  const [aviso, setAviso] = useState("");
  const [filtros, setFiltros] = useState({ rol: "", estado: "", buscar: "" });

  const [modalAbierto, setModalAbierto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [formulario, setFormulario] = useState(VACIO);
  const [erroresForm, setErroresForm] = useState({});
  const [tocados, setTocados] = useState({});
  const [guardando, setGuardando] = useState(false);
  const [porEliminar, setPorEliminar] = useState(null);

  /* ------------------------------ Carga ------------------------------ */
  const obtener = useCallback(async () => {
    const [u, c] = await Promise.all([
      usuariosApi.listar(filtros),
      citasApi.resumen().catch(() => null),
    ]);
    return { usuarios: u.usuarios, resumen: c ? c.resumen : null };
  }, [filtros]);

  const { datos, cargando, error, setError, recargar: cargar } = useCarga(obtener);

  const usuarios = datos?.usuarios ?? [];
  const resumenCitas = datos?.resumen ?? null;

  /* ---------------------------- Formulario ---------------------------- */
  const abrirCrear = () => {
    setEditando(null);
    setFormulario(VACIO);
    setErroresForm({});
    setTocados({});
    setModalAbierto(true);
  };

  const abrirEditar = (u) => {
    setEditando(u);
    setFormulario({
      nombre: u.nombre,
      apellido: u.apellido,
      tipoDocumento: u.tipoDocumento,
      numeroDocumento: u.numeroDocumento,
      direccion: u.direccion,
      telefono: u.telefono,
      correo: u.correo,
      password: "",
      rol: u.rol,
    });
    setErroresForm({});
    setTocados({});
    setModalAbierto(true);
  };

  const cambiarCampo = (evento) => {
    const { name, value } = evento.target;
    const limpio = SANITIZADORES[name] ? SANITIZADORES[name](value) : value;
    const siguiente = { ...formulario, [name]: limpio };

    setFormulario(siguiente);
    setTocados((t) => ({ ...t, [name]: true }));
    setErroresForm(validarFormulario(siguiente, Boolean(editando)));
  };

  const campo = (nombre) => ({
    name: nombre,
    value: formulario[nombre],
    onChange: cambiarCampo,
    onBlur: () => setTocados((t) => ({ ...t, [nombre]: true })),
    error: tocados[nombre] ? erroresForm[nombre] : "",
  });

  const guardar = async (evento) => {
    evento.preventDefault();

    const errores = validarFormulario(formulario, Boolean(editando));
    setErroresForm(errores);
    setTocados(Object.fromEntries(Object.keys(VACIO).map((k) => [k, true])));

    if (Object.keys(errores).length > 0) return;

    setGuardando(true);
    setError("");
    try {
      if (editando) {
        await usuariosApi.actualizar(editando.id, {
          nombre: formulario.nombre,
          apellido: formulario.apellido,
          tipoDocumento: formulario.tipoDocumento,
          numeroDocumento: formulario.numeroDocumento,
          direccion: formulario.direccion,
          telefono: formulario.telefono,
          correo: formulario.correo,
        });
        setAviso(`Usuario ${formulario.correo} actualizado.`);
      } else {
        await usuariosApi.crear(formulario);
        setAviso(`Usuario ${formulario.correo} creado.`);
      }
      setModalAbierto(false);
      cargar();
    } catch (e) {
      setError(e.message);
      setErroresForm((prev) => ({ ...prev, ...(e.errores || {}) }));
    } finally {
      setGuardando(false);
    }
  };

  /* ----------------------------- Acciones ----------------------------- */
  const alternarEstado = async (u) => {
    setError("");
    try {
      const nuevo = u.estado === "activo" ? "inactivo" : "activo";
      await usuariosApi.cambiarEstado(u.id, nuevo);
      setAviso(`${u.correo} quedó ${nuevo}.`);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  };

  const eliminar = async () => {
    setError("");
    try {
      await usuariosApi.eliminar(porEliminar.id);
      setAviso(`${porEliminar.correo} fue eliminado.`);
      setPorEliminar(null);
      cargar();
    } catch (e) {
      setError(e.message);
      setPorEliminar(null);
    }
  };

  const conteo = (rol) => usuarios.filter((u) => u.rol === rol).length;

  return (
    <PanelLayout
      etiqueta="Panel de administración"
      titulo="Gestión de usuarios"
      descripcion="Consulta, agrega, edita, activa o elimina las cuentas del sistema. Solo el rol administrador tiene acceso a esta pantalla."
      acciones={
        <Button onClick={abrirCrear}>
          <Icono nombre="usuario" className="h-4 w-4" />
          Agregar usuario
        </Button>
      }
    >
      {/* ----------------------------- Resumen ----------------------------- */}
      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Tarjeta titulo="Usuarios" valor={usuarios.length} icono="usuario" acento />
        <Tarjeta titulo="Administradores" valor={conteo("administrador")} icono="escudo" />
        <Tarjeta titulo="Empleados" valor={conteo("empleado")} icono="herramienta" />
        <Tarjeta titulo="Clientes" valor={conteo("cliente")} icono="etiqueta" />
      </div>

      {resumenCitas && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Tarjeta titulo="Citas pendientes" valor={resumenCitas.pendiente} icono="reloj" acento />
          <Tarjeta titulo="Confirmadas" valor={resumenCitas.confirmada} icono="check" />
          <Tarjeta titulo="Completadas" valor={resumenCitas.completada} icono="check" />
          <Tarjeta titulo="Canceladas" valor={resumenCitas.cancelada} icono="cerrar" />
        </div>
      )}

      {/* ----------------------------- Filtros ----------------------------- */}
      <div className="mt-10 grid gap-4 sm:grid-cols-3">
        <Select
          label="Filtrar por rol"
          value={filtros.rol}
          onChange={(e) => setFiltros((f) => ({ ...f, rol: e.target.value }))}
          placeholder="Todos los roles"
          opciones={ROLES}
        />
        <Select
          label="Filtrar por estado"
          value={filtros.estado}
          onChange={(e) => setFiltros((f) => ({ ...f, estado: e.target.value }))}
          placeholder="Todos los estados"
          opciones={[
            { valor: "activo", etiqueta: "Activo" },
            { valor: "inactivo", etiqueta: "Inactivo" },
          ]}
        />
        <Input
          label="Buscar"
          icono="usuario"
          value={filtros.buscar}
          onChange={(e) => setFiltros((f) => ({ ...f, buscar: e.target.value }))}
          placeholder="Nombre, correo o documento"
        />
      </div>

      <div className="mt-6 space-y-3">
        {error && <Aviso tipo="error">{error}</Aviso>}
        {aviso && !error && <Aviso tipo="exito">{aviso}</Aviso>}
      </div>

      {/* ------------------------------ Tabla ------------------------------ */}
      <div className="cristal mt-6 overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="border-b border-linea">
            <tr>
              {["Usuario", "Documento", "Contacto", "Rol", "Estado", "Acciones"].map((h) => (
                <th key={h} scope="col" className="etiqueta px-4 py-4 text-plomo">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-linea">
            {cargando ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ceniza">
                  Cargando usuarios...
                </td>
              </tr>
            ) : usuarios.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ceniza">
                  No hay usuarios que coincidan con el filtro.
                </td>
              </tr>
            ) : (
              usuarios.map((u) => (
                <tr key={u.id} className="transition-colors duration-200 hover:bg-carbon">
                  <td className="px-4 py-4">
                    <p className="font-medium text-hueso">
                      {u.nombre} {u.apellido}
                      {u.id === yo.id && (
                        <span className="ml-2 font-sans text-xs uppercase tracking-[0.12em] text-accion-claro">
                          (tú)
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-plomo">{u.correo}</p>
                  </td>
                  <td className="px-4 py-4 text-ceniza">
                    {u.tipoDocumento} {u.numeroDocumento}
                  </td>
                  <td className="px-4 py-4 text-ceniza">
                    <p>{u.telefono}</p>
                    <p className="text-xs text-plomo">{u.direccion}</p>
                  </td>
                  <td className="px-4 py-4">
                    <span className="font-sans text-xs uppercase tracking-[0.12em] text-ceniza">
                      {u.rol}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <Estado valor={u.estado} />
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => abrirEditar(u)}
                        className="min-h-11 cursor-pointer border border-linea px-3 font-sans
                                   text-xs uppercase tracking-[0.12em] text-hueso transition-colors
                                   duration-200 hover:border-hueso"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => alternarEstado(u)}
                        disabled={u.id === yo.id}
                        className="min-h-11 cursor-pointer border border-linea px-3 font-sans
                                   text-xs uppercase tracking-[0.12em] text-ceniza transition-colors
                                   duration-200 hover:border-hueso hover:text-hueso
                                   disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {u.estado === "activo" ? "Inactivar" : "Activar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setPorEliminar(u)}
                        disabled={u.id === yo.id}
                        className="min-h-11 cursor-pointer border border-accion/40 px-3 font-sans
                                   text-xs uppercase tracking-[0.12em] text-accion-claro
                                   transition-colors duration-200 hover:bg-accion-fondo hover:text-hueso
                                   disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* -------------------- Modal crear / editar -------------------- */}
      <Modal
        abierto={modalAbierto}
        alCerrar={() => setModalAbierto(false)}
        titulo={editando ? "Editar usuario" : "Agregar usuario"}
        descripcion={
          editando
            ? `Actualizando la cuenta de ${editando.correo}.`
            : "La contraseña se guardará hasheada con bcrypt."
        }
        ancho="max-w-3xl"
      >
        <form onSubmit={guardar} noValidate className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <Input label="Nombre" icono="usuario" maxLength={LIMITES.nombre} {...campo("nombre")} />
            <Input label="Apellido" icono="usuario" maxLength={LIMITES.apellido} {...campo("apellido")} />
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <Select label="Tipo de documento" opciones={TIPOS_DOCUMENTO} {...campo("tipoDocumento")} />
            <Input
              label="Número de documento"
              icono="documento"
              inputMode={formulario.tipoDocumento === "PA" ? "text" : "numeric"}
              maxLength={LIMITES.documento}
              {...campo("numeroDocumento")}
            />
          </div>

          <Input label="Dirección" icono="ubicacion" maxLength={LIMITES.direccion} {...campo("direccion")} />

          <div className="grid gap-6 sm:grid-cols-2">
            <Input
              label="Teléfono"
              icono="telefono"
              inputMode="numeric"
              maxLength={LIMITES.telefono}
              {...campo("telefono")}
            />
            <Input
              label="Correo electrónico"
              icono="correo"
              type="email"
              maxLength={LIMITES.correo}
              {...campo("correo")}
            />
          </div>

          {!editando && (
            <div className="grid gap-6 sm:grid-cols-2">
              <Input
                label="Contraseña"
                type="password"
                maxLength={LIMITES.password}
                ayuda="Mayúscula, minúscula, número y símbolo."
                {...campo("password")}
              />
              <Select
                label="Rol"
                opciones={ROLES}
                placeholder="Selecciona un rol"
                {...campo("rol")}
              />
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-linea pt-6 sm:flex-row-reverse">
            <Button type="submit" ancho tamano="lg" cargando={guardando}>
              {editando ? "Guardar cambios" : "Crear usuario"}
            </Button>
            <Button
              variante="contorno"
              ancho
              tamano="lg"
              onClick={() => setModalAbierto(false)}
              disabled={guardando}
            >
              Cancelar
            </Button>
          </div>
        </form>
      </Modal>

      {/* -------------------- Confirmación de borrado -------------------- */}
      <Modal
        abierto={Boolean(porEliminar)}
        alCerrar={() => setPorEliminar(null)}
        titulo="Eliminar usuario"
        ancho="max-w-lg"
      >
        <p className="text-sm leading-relaxed text-ceniza">
          Vas a eliminar de forma permanente la cuenta de{" "}
          <span className="font-semibold text-hueso">{porEliminar?.correo}</span> y
          todas sus citas asociadas. Si solo quieres bloquear el acceso, es mejor
          inactivarla.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row-reverse">
          <Button ancho tamano="lg" onClick={eliminar}>
            Sí, eliminar
          </Button>
          <Button variante="contorno" ancho tamano="lg" onClick={() => setPorEliminar(null)}>
            Cancelar
          </Button>
        </div>
      </Modal>
    </PanelLayout>
  );
}

export default PanelAdmin;
