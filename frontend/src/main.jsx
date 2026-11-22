
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import AuthProvider from './auth/AuthProvider.jsx';
import { ConfirmacionProvider } from './context/ConfirmacionProvider.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ConfirmacionProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ConfirmacionProvider>
    </BrowserRouter>
  </StrictMode>
);
