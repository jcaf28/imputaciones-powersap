// PATH: frontend/src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { PageProvider } from './contexts/PageContext';
import { ThemeProviderWrapper } from './contexts/ThemeContext';
import App from './App';

const serviceName = import.meta.env.VITE_SERVICE_NAME || '';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProviderWrapper>
      <CssBaseline />
      <BrowserRouter basename={`/${serviceName}`}>
        <PageProvider>
          <App />
        </PageProvider>
      </BrowserRouter>
    </ThemeProviderWrapper>
  </React.StrictMode>
);
