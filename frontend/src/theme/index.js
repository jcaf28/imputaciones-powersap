// PATH: frontend/src/theme/index.js

import { createTheme } from '@mui/material/styles';

const commonTypography = {
  fontFamily: 'Roboto, Arial, sans-serif',
  fontFamilyMono: 'Roboto Mono, monospace',
  h1: { fontSize: '2.5rem', fontWeight: 700 },
  h2: { fontSize: '2.2rem', fontWeight: 700 },
  h3: { fontSize: '2rem', fontWeight: 700 },
  h4: { fontSize: '1.7rem', fontWeight: 600 },
  h5: { fontSize: '1.5rem', fontWeight: 600 },
  h6: { fontSize: '1.3rem', fontWeight: 600 },
  subtitle1: { fontSize: '1.1rem', fontWeight: 500 },
  subtitle2: { fontSize: '1rem', fontWeight: 500 },
  body1: { fontSize: '1rem' },
  body2: { fontSize: '0.9rem' },
  button: { textTransform: 'none', fontWeight: 600 },
  caption: { fontSize: '0.8rem', fontStyle: 'italic' },
  overline: { fontSize: '0.75rem', letterSpacing: 1.5, textTransform: 'uppercase' }
};

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#f50057' },
    background: { default: '#f4f4f4', paper: '#ffffff' },
    text: { primary: '#333333', secondary: '#555555' }
  },
  typography: {
    ...commonTypography,
    h1: { ...commonTypography.h1, color: '#1976d2' },
    h2: { ...commonTypography.h2, color: '#1976d2' },
    h3: { ...commonTypography.h3, color: '#1976d2' }
    // El resto hereda `text.primary`
  },
  shape: { borderRadius: 8 }
});

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#bb86fc' },
    secondary: { main: '#03dac6' },
    background: { default: '#121212', paper: '#1e1e1e' },
    text: { primary: '#ffffff', secondary: '#aaaaaa' }
  },
  typography: {
    ...commonTypography,
    h1: { ...commonTypography.h1, color: '#bb86fc' },
    h2: { ...commonTypography.h2, color: '#bb86fc' },
    h3: { ...commonTypography.h3, color: '#bb86fc' }
    // El resto hereda `text.primary`
  },
  shape: { borderRadius: 8 }
});

export { lightTheme, darkTheme };
