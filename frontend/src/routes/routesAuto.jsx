// Detecta todos los archivos JSX en pages/
const modules = import.meta.glob('../pages/*.jsx', { eager: true });

const routes = Object.entries(modules)
  .map(([path, module]) => {
    const name = path.match(/\/pages\/(.+)\.jsx$/)?.[1];
    if (!name || name.toLowerCase() === 'home') return null;

    const label = name.replace(/([A-Z])/g, ' $1').trim();
    return {
      path: `/${name.toLowerCase()}`,
      label,
      // Instancia el componente (JSX)
      element: <module.default />,
    };
  })
  .filter(Boolean);

export default routes;
