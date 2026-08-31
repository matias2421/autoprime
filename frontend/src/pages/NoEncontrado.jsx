import Button from "../components/ui/Button";
import Icono from "../components/ui/Icono";

function NoEncontrado() {
  return (
    <section className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-5 py-32 text-center sm:px-8">
      <span className="flex h-16 w-16 items-center justify-center border border-accion/40 text-accion">
        <Icono nombre="alerta" className="h-8 w-8" />
      </span>

      <p className="etiqueta mt-8 text-accion-claro">Error 404</p>
      <h1 className="display mt-4 text-5xl text-hueso sm:text-7xl">
        Esta página
        <br />
        no existe
      </h1>
      <p className="mt-6 max-w-md leading-relaxed text-ceniza">
        Puede que el enlace esté roto o que el modelo que buscabas ya no esté
        disponible en el catálogo.
      </p>

      <div className="mt-10 flex flex-wrap justify-center gap-3">
        <Button to="/" tamano="lg">
          Volver al inicio
          <Icono nombre="flecha" className="h-4 w-4" />
        </Button>
        <Button to="/modelos" variante="contorno" tamano="lg">
          Ver los modelos
        </Button>
      </div>
    </section>
  );
}

export default NoEncontrado;
