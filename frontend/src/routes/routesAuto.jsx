// frontend/src/routes/routesAuto.jsx
import React from 'react';

const modules = import.meta.glob('../pages/*.jsx', { eager: true });

// ¿Estamos en modo desarrollo?
const isDev = import.meta.env.MODE === 'development';

const routes = Object.entries(modules)
  .map(([path, module]) => {
    const name = path.match(/\/pages\/(.+)\.jsx$/)?.[1];
    if (!name || name.toLowerCase() === 'home') return null;

    const meta = module.meta || {};

    // ─── oculta páginas solo-dev en producción ───
    if (!isDev && meta.devOnly) return null;

    const label = meta.label || name.replace(/([A-Z])/g, ' $1').trim();
    const priority = meta.priority ?? 99;

    const Page = module.default;         // evita “key=” warning

    return {
      path: `/${name.toLowerCase()}`,
      label,
      priority,
      element: <Page />,
    };
  })
  .filter(Boolean)
  .sort((a, b) => a.priority - b.priority);

export default routes;
