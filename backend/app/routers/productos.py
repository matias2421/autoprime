"""Catálogo de vehículos."""

from fastapi import APIRouter, Path, status

from app.crud import productos as crud_productos
from app.dependencias import Personal, ProductoRuta, SesionDep, SoloAdmin
from app.schemas.comunes import EstadoProducto, Familia, RespuestaSimple
from app.schemas.producto import ProductoActualizar, ProductoCrear, ProductoSalida
from app.schemas.sobres import SobreProducto, SobreProductos

router = APIRouter(prefix="/api/productos", tags=["Productos"])


@router.get("", response_model=SobreProductos, summary="Listar el catálogo")
def listar(
    sesion: SesionDep,
    familia: Familia | None = None,
    estado: EstadoProducto | None = None,
) -> SobreProductos:
    """Consulta pública: el catálogo se ve sin iniciar sesión."""
    productos = crud_productos.listar(sesion, familia=familia, estado=estado)
    salida = [ProductoSalida.desde_modelo(p) for p in productos]
    return SobreProductos(productos=salida, total=len(salida))


@router.post(
    "",
    response_model=SobreProducto,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir un vehículo",
)
def crear(datos: ProductoCrear, sesion: SesionDep, _: Personal) -> SobreProducto:
    producto = crud_productos.crear(sesion, datos.model_dump())
    return SobreProducto(producto=ProductoSalida.desde_modelo(producto))


@router.get(
    "/{identificador}", response_model=SobreProducto, summary="Consultar por id o slug"
)
def obtener(
    sesion: SesionDep,
    identificador: str = Path(description="Id numérico o slug del vehículo"),
) -> SobreProducto:
    """Acepta las dos formas de referirse a un vehículo.

    El panel de administración trabaja con identificadores numéricos, pero la
    web pública enlaza por slug (`/modelos/pugnator-tricolore`). Resolver
    ambas aquí evita tener dos rutas que devuelven exactamente lo mismo.
    """
    if identificador.isdigit():
        producto = crud_productos.obtener_o_fallar(sesion, int(identificador))
    else:
        producto = crud_productos.obtener_por_slug(sesion, identificador)
    return SobreProducto(producto=ProductoSalida.desde_modelo(producto))


@router.put("/{producto_id}", response_model=SobreProducto, summary="Actualizar")
def actualizar(
    datos: ProductoActualizar,
    producto: ProductoRuta,
    sesion: SesionDep,
    _: Personal,
) -> SobreProducto:
    cambios = datos.model_dump(exclude_unset=True)
    actualizado = crud_productos.actualizar(sesion, producto, cambios)
    return SobreProducto(producto=ProductoSalida.desde_modelo(actualizado))


@router.delete("/{producto_id}", response_model=RespuestaSimple, summary="Eliminar")
def eliminar(
    producto: ProductoRuta, sesion: SesionDep, _: SoloAdmin
) -> RespuestaSimple:
    crud_productos.eliminar(sesion, producto)
    return RespuestaSimple(mensaje="Vehículo eliminado.")
