// PATH: frontend/src/pages/Home.jsx

import { Container, Box, Typography, useTheme } from '@mui/material';

function Ip() {
  const theme = useTheme();
  
  return (
    <Container
      maxWidth="md"
      sx={{ mt: 8, mb: 8, textAlign: 'center', backgroundColor: theme.palette.background.default }}
    >
      <Typography variant="h3" sx={{ mb: 2 }}>
        Transformador de imputaciones de IP DIV3 a SAP
      </Typography>
      <Box
        sx={{
          width: '60px',
          height: '4px',
          bgcolor: theme.palette.primary.main,
          mx: 'auto',
          mb: 4,
          borderRadius: theme.shape.borderRadius
        }}
      />
      <Typography variant="body1" sx={{ mb: 3 }}>
        Esta plataforma ha sido diseñada para facilitar la gestión y seguimiento de
        procesos dentro de IP DIV3. Aquí encontrarás herramientas que te permitirán
        optimizar tareas como la generación de archivos para imputaciones.
      </Typography>
      <Typography variant="body1" sx={{ mb: 3 }}>
        Utiliza el menú lateral para acceder a las diferentes funcionalidades. Las
        opciones disponibles se actualizarán conforme se implementen nuevas
        herramientas.
      </Typography>
    </Container>
  );
}

export default Ip;