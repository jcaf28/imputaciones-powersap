// PATH: frontend/src/contexts/PageContext.jsx

import { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const PageContext = createContext();

export function PageProvider({ children }) {
  // Detectamos la ruta actual
  const location = useLocation();
  // Estado que indica qué página está seleccionada
  const [selectedPage, setSelectedPage] = useState(location.pathname);

  // Cada vez que la ubicación cambie, actualizamos "selectedPage"
  useEffect(() => {
    setSelectedPage(location.pathname);
  }, [location.pathname]);

  return (
    <PageContext.Provider value={{ selectedPage, setSelectedPage }}>
      {children}
    </PageContext.Provider>
  );
}

export function usePage() {
  return useContext(PageContext);
}