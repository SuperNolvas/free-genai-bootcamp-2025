import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store/store';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function withAuthGuard<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: React.ReactNode
) {
  return function WithAuthGuardWrapper(props: P) {
    const { token } = useSelector((state: RootState) => state.auth);

    if (!token) {
      return fallback || null;
    }

    return <WrappedComponent {...props} />;
  };
}

export default function AuthGuard({ children, fallback }: AuthGuardProps) {
  const { token } = useSelector((state: RootState) => state.auth);

  if (!token) {
    return fallback || null;
  }

  return <>{children}</>;
}