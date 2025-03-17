import { useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { AppDispatch, RootState } from '../store/store';
import { login, register, logout, fetchUserProfile } from '../store/slices/authSlice';
import type { LoginRequest, RegisterRequest } from '../types/api';

export function useAuth() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { token, user, isLoading, error } = useSelector((state: RootState) => state.auth);

  // Fetch user profile when we have a token but no user data
  useEffect(() => {
    if (token && !user && !isLoading) {
      dispatch(fetchUserProfile());
    }
  }, [token, user, isLoading, dispatch]);

  const handleLogin = useCallback(async (credentials: LoginRequest) => {
    try {
      await dispatch(login(credentials)).unwrap();
      navigate('/dashboard');
    } catch (error) {
      // Error is handled by Redux
    }
  }, [dispatch, navigate]);

  const handleRegister = useCallback(async (data: RegisterRequest) => {
    try {
      await dispatch(register(data)).unwrap();
      navigate('/auth/login', { 
        state: { message: 'Registration successful! Please log in.' }
      });
    } catch (error) {
      // Error is handled by Redux
    }
  }, [dispatch, navigate]);

  const handleLogout = useCallback(() => {
    dispatch(logout());
    navigate('/auth/login');
  }, [dispatch, navigate]);

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated: !!token,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
  };
}