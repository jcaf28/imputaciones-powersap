// PATH: frontend/src/components/SideNav.jsx

import { Drawer, List, ListItemButton, ListItemText } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import routes from '../routes/routesAuto';

function SideNav() {
  const location = useLocation();
  const serviceName = import.meta.env.VITE_SERVICE_NAME || '';

  return (
    <Drawer
      variant="permanent"
      anchor="left"
      sx={{
        width: 240,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: 240, top: 64 },
      }}
    >
      <List>
        {routes.map(({ path, label }) => (
          <ListItemButton
            key={path}
            component={Link}
            to={path}
            selected={location.pathname === `/${serviceName}${path}`}
          >
            <ListItemText primary={label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}

export default SideNav;
