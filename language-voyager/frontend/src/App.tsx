import React from 'react';
import { useLocation } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { ThemeProvider } from './components/theme-provider';
import { BrowserRouter as Router } from 'react-router-dom';
import AppSidebar from './components/Sidebar';
import Breadcrumbs from './components/Breadcrumbs';
import AppRouter from './components/AppRouter';
import { NavigationProvider } from './context/NavigationContext';
import { WebSocketProvider } from './context/WebSocketContext';
import {
  SidebarInset,
  SidebarProvider
} from './components/ui/sidebar';

function AppContent() {
  const location = useLocation();
  const isAuthRoute = location.pathname.startsWith('/auth/');

  // For auth routes, render without sidebar/navigation
  if (isAuthRoute) {
    return <AppRouter />;
  }

  // For main app routes, render with full layout
  return (
    <div className="relative flex min-h-screen">
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex-1">
          <main className="flex min-h-[calc(100vh-theme(spacing.16))] flex-col gap-8 p-4 md:gap-8 md:p-10">
            <Breadcrumbs />
            <AppRouter />
          </main>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Provider store={store}>
        <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
          <NavigationProvider>
            <WebSocketProvider>
              <AppContent />
            </WebSocketProvider>
          </NavigationProvider>
        </ThemeProvider>
      </Provider>
    </Router>
  );
}
