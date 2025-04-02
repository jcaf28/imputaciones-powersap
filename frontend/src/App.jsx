// PATH: frontend/src/App.jsx

import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SideNav from './components/SideNav';
import routes from './routes/routesAuto';
import Home from './pages/Home'; // Página principal

function App() {
  return (
    <>
      <Header />
      <div style={{ display: 'flex', marginTop: '64px' }}>
        <SideNav />
        <main style={{ flexGrow: 1, padding: '16px' }}>
          <Routes>
            <Route path="/" element={<Home />} />
            {routes.map(({ path, element }) => (
              <Route key={path} path={path} element={element} />
            ))}
          </Routes>
        </main>
      </div>
    </>
  );
}

export default App;
