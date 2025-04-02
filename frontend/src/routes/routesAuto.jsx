// PATH: frontend/src/routes/routesAuto.jsx

const modules = import.meta.glob('../pages/*.jsx', { eager: true });

const routes = Object.entries(modules)
  .map(([path, module]) => {
    const name = path.match(/\/pages\/(.+)\.jsx$/)?.[1];
    if (!name || name.toLowerCase() === 'home') return null;

    const meta = module.meta || {};
    const label = meta.label || name.replace(/([A-Z])/g, ' $1').trim();
    const priority = meta.priority ?? 99; // por defecto al final

    return {
      path: `/${name.toLowerCase()}`,
      label,
      priority,
      element: <module.default />,
    };
  })
  .filter(Boolean)
  .sort((a, b) => a.priority - b.priority); // 🔥 orden final

export default routes;
