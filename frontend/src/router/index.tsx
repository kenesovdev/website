import { Navigate, Route, Routes } from 'react-router-dom';

import AdminRoute from '../components/AdminRoute';
import ProtectedRoute from '../components/ProtectedRoute';
import AdminLayout from '../pages/admin/AdminLayout';
import MainLayout from '../layouts/MainLayout';
import HomePage from '../pages/HomePage';
import LeaderboardPage from '../pages/LeaderboardPage';
import LoginPage from '../pages/LoginPage';
import NotFoundPage from '../pages/NotFoundPage';
import ProblemDetailPage from '../pages/ProblemDetailPage';
import ProblemsPage from '../pages/ProblemsPage';
import ProfilePage from '../pages/ProfilePage';
import RegisterPage from '../pages/RegisterPage';
import AdminProblemsPage from '../pages/admin/AdminProblemsPage';
import CreateEditProblemPage from '../pages/admin/CreateEditProblemPage';
import SubmissionsPage from '../pages/SubmissionsPage';

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="profile/:handle" element={<ProfilePage />} />
        <Route path="leaderboard" element={<LeaderboardPage />} />

        <Route
          path="problems"
          element={
            <ProtectedRoute>
              <ProblemsPage />
            </ProtectedRoute>
          }
        />
        <Route path="problems/:slug" element={<ProblemDetailPage />} />

        <Route
          path="submissions"
          element={
            <ProtectedRoute>
              <SubmissionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="problems/:slug/submissions"
          element={
            <ProtectedRoute>
              <SubmissionsPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="admin"
          element={
            <AdminRoute>
              <AdminLayout />
            </AdminRoute>
          }
        >
          <Route index element={<Navigate to="/admin/problems" replace />} />
          <Route path="problems" element={<AdminProblemsPage />} />
          <Route path="problems/create" element={<CreateEditProblemPage />} />
          <Route path="problems/:slug/edit" element={<CreateEditProblemPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
