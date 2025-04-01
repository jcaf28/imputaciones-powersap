// PATH: frontend/src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { PageProvider } from './contexts/PageContext';
import { ThemeProviderWrapper } from './contexts/ThemeContext';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProviderWrapper>
      <CssBaseline />
      <BrowserRouter> 
        <PageProvider>
          <App />
        </PageProvider>
      </BrowserRouter>
    </ThemeProviderWrapper>
  </React.StrictMode>
);
