import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './auth/ProtectedRoute'

const Map = React.lazy(() => import('@/pages/Map'))
const Lessons = React.lazy(() => import('@/pages/Lessons'))
const Achievements = React.lazy(() => import('@/pages/Achievements'))
const Settings = React.lazy(() => import('@/pages/Settings'))
const Login = React.lazy(() => import('@/pages/auth/Login'))
const Register = React.lazy(() => import('@/pages/auth/Register'))
const ForgotPassword = React.lazy(() => import('@/pages/auth/ForgotPassword'))
const ResetPassword = React.lazy(() => import('@/pages/auth/ResetPassword'))

const AppRouter = () => {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Routes>
        {/* Auth Routes */}
        <Route path="/auth">
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="forgot-password" element={<ForgotPassword />} />
          <Route path="reset-password" element={<ResetPassword />} />
        </Route>

        {/* Protected App Routes */}
        <Route path="/" element={<Navigate to="/map" replace />} />
        <Route
          path="/map"
          element={
            <ProtectedRoute>
              <Map />
            </ProtectedRoute>
          }
        />
        <Route
          path="/lessons"
          element={
            <ProtectedRoute>
              <Lessons />
            </ProtectedRoute>
          }
        />
        <Route
          path="/achievements"
          element={
            <ProtectedRoute>
              <Achievements />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />

        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/map" replace />} />
      </Routes>
    </React.Suspense>
  )
}

export default AppRouter