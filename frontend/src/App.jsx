import Preloader from "./components/Preloader";
import AppRouter from "./router/AppRouter";
import { IdiomaProvider } from "./context/IdiomaContext";

function App() {
  return (
    <IdiomaProvider>
      {/*
        La cortina se monta fuera del router: aparece en cada carga y recarga
        del documento, pero no al navegar entre páginas.
      */}
      <Preloader />
      <AppRouter />
    </IdiomaProvider>
  );
}

export default App;
