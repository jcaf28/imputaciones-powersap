// PATH: frontend/src/components/SideNav.jsx

import { Drawer, List, ListItemButton, ListItemText } from '@mui/material';
import { Link } from 'react-router-dom';
import { usePage } from '../contexts/PageContext';

function SideNav() {
  const { selectedPage, setSelectedPage } = usePage();

  return (
    <Drawer
      variant="permanent"
      anchor="left"
      sx={{ width: 240, flexShrink: 0, [`& .MuiDrawer-paper`]: { width: 240, top: 64 } }}
    >
      <List>
        <ListItemButton
          component={Link}
          to="/ip/imputaciones-ip"
          selected={selectedPage === "/ip/imputaciones-ip"}
          onClick={() => setSelectedPage("/ip/imputaciones-ip")}
        >
          <ListItemText primary="Imputaciones IP" />
        </ListItemButton>
      </List>
    </Drawer>
  );
}

export default SideNav;