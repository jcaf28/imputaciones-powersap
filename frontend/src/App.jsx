// PATH: frontend/src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import SideNav from './components/SideNav';
import Ip from './pages/Ip';
import ImputacionesIP from './pages/ImputacionesIP';

function App() {
  const serviceName = import.meta.env.VITE_SERVICE_NAME || '';
  
  return (
    <BrowserRouter basename={`/${serviceName}`}>
      <Header />
      <SideNav />
      <Routes>
        <Route path="/" element={<Ip />} />
        <Route path="/imputaciones-ip" element={<ImputacionesIP />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
