import { Routes, Route, Navigate } from 'react-router-dom';
import LoginForm from '@/components/auth/LoginForm';
import RegisterForm from '@/components/auth/RegisterForm';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

import Dashboard from '@/pages/Dashboard';
import StudyActivities from '@/pages/StudyActivities';
import StudyActivityShow from '@/pages/StudyActivityShow';
import StudyActivityLaunch from '@/pages/StudyActivityLaunch';
import Words from '@/pages/Words';
import WordShow from '@/pages/WordShow';
import Groups from '@/pages/Groups';
import GroupShow from '@/pages/GroupShow';
import Sessions from '@/pages/Sessions';
import StudySessionShow from '@/pages/StudySessionShow';
import Settings from '@/pages/Settings';

export default function AppRouter() {
  return (
    <div className="min-h-screen">
      <main className="container mx-auto px-4 py-8">
        <Routes>
          {/* Auth routes */}
          <Route path="/auth/login" element={<LoginForm />} />
          <Route path="/auth/register" element={<RegisterForm />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/study-activities" element={
            <ProtectedRoute>
              <StudyActivities />
            </ProtectedRoute>
          } />
          <Route path="/study-activities/:id" element={
            <ProtectedRoute>
              <StudyActivityShow />
            </ProtectedRoute>
          } />
          <Route path="/study-activities/:id/launch" element={
            <ProtectedRoute>
              <StudyActivityLaunch />
            </ProtectedRoute>
          } />
          <Route path="/words" element={
            <ProtectedRoute>
              <Words />
            </ProtectedRoute>
          } />
          <Route path="/words/:id" element={
            <ProtectedRoute>
              <WordShow />
            </ProtectedRoute>
          } />
          <Route path="/groups" element={
            <ProtectedRoute>
              <Groups />
            </ProtectedRoute>
          } />
          <Route path="/groups/:id" element={
            <ProtectedRoute>
              <GroupShow />
            </ProtectedRoute>
          } />
          <Route path="/sessions" element={
            <ProtectedRoute>
              <Sessions />
            </ProtectedRoute>
          } />
          <Route path="/sessions/:id" element={
            <ProtectedRoute>
              <StudySessionShow />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  );
}