// PATH: frontend/src/App.jsx

import { Routes, Route } from 'react-router-dom'; 
import { Box } from '@mui/material'; 
import Header from './components/Header';
import SideNav from './components/SideNav';
import Ip from './pages/Ip';
import ImputacionesIP from './pages/ImputacionesIP';

function App() {
  return (
    <>
      <Header />
      <Box sx={{ display: 'flex', mt: 8 }}>
        <SideNav />
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Routes>
            <Route path="/ip" element={<Ip />} />
            <Route path="/ip/imputaciones-ip" element={<ImputacionesIP />} />
          </Routes>
        </Box>
      </Box>
    </>
  );
}

export default App;
