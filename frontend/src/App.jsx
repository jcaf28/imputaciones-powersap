// PATH: frontend/src/App.jsx
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SideNav from './components/SideNav';
import Ip from './pages/Ip';
import ImputacionesIP from './pages/ImputacionesIP';

function App() {
  return (
    <>
      <Header />
      <div style={{ display: 'flex', marginTop: '64px' }}>
        <SideNav />
        <main style={{ flexGrow: 1, padding: '16px' }}>
          <Routes>
            <Route path="/" element={<Ip />} />
            <Route path="/imputaciones-ip" element={<ImputacionesIP />} />
          </Routes>
        </main>
      </div>
    </>
  );
}

export default App;

