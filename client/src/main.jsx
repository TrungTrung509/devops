import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@/styles/global.scss';
import AppProviders from '@/app/providers/AppProviders';
import AuthBootstrap from '@/app/providers/AuthBootstrap';
import AppRouter from '@/app/router/AppRouter';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppProviders>
      <AuthBootstrap>
        <AppRouter />
      </AuthBootstrap>
    </AppProviders>
  </StrictMode>
);
