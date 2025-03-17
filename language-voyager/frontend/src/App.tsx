import React from 'react';
import logo from './logo.svg';
import './App.css';
import { useLocation } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { ThemeProvider } from "@/components/theme-provider"
import { BrowserRouter as Router } from 'react-router-dom'
import AppSidebar from '@/components/Sidebar'
import Breadcrumbs from '@/components/Breadcrumbs'
import AppRouter from '@/components/AppRouter'
import { NavigationProvider } from '@/context/NavigationContext'

import {
  SidebarInset,
  SidebarProvider
} from "@/components/ui/sidebar"

function AppContent() {
  const location = useLocation();
  const isAuthRoute = location.pathname.startsWith('/auth/');

  // For auth routes, render without sidebar/navigation
  if (isAuthRoute) {
    return <AppRouter />;
  }

  // For main app routes, render with full layout
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Breadcrumbs />
        <AppRouter />
      </SidebarInset>
    </SidebarProvider>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <NavigationProvider>
          <Router>
            <AppContent />
          </Router>
        </NavigationProvider>
      </ThemeProvider>
    </Provider>
  );
}
