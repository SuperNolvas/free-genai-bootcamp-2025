import React, { createContext, useContext, useState } from 'react';
import { useLocation } from 'react-router-dom';

interface NavigationContextType {
  breadcrumbs: { name: string; path: string }[];
  setBreadcrumbs: (breadcrumbs: { name: string; path: string }[]) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export function NavigationProvider({ children }: { children: React.ReactNode }) {
  const [breadcrumbs, setBreadcrumbs] = useState<{ name: string; path: string }[]>([]);
  const location = useLocation();

  return (
    <NavigationContext.Provider value={{ breadcrumbs, setBreadcrumbs }}>
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
}