// PATH: frontend/src/components/Header.jsx

import { AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Home, Brightness4, Brightness7 } from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { useThemeMode } from '../contexts/ThemeContext';

function Header() {
  const { themeMode, toggleTheme } = useThemeMode();

  return (
    <AppBar position="fixed" sx={{ width: '100%' }}>
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        {/* Botón Home */}
        <IconButton component={Link} to="/ip" color="inherit">
          <Home />
        </IconButton>
        
        <Typography variant="h6">Imputaciones PowerApps D3</Typography>
        
        {/* Botón de cambio de tema */}
        <IconButton onClick={toggleTheme} color="inherit">
          {themeMode === 'light' ? <Brightness4 /> : <Brightness7 />}
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}

export default Header;