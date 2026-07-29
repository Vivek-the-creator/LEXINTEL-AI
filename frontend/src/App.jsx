import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import GuestRoute from "./components/layout/GuestRoute";
import DashboardLayout from "./components/layout/DashboardLayout";

import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import NotFoundPage from "./pages/NotFoundPage";

import DashboardPage from "./pages/dashboard/DashboardPage";
import UploadsPage from "./pages/dashboard/UploadsPage";
import ProfilePage from "./pages/dashboard/ProfilePage";
import CasesPage from "./pages/dashboard/CasesPage";
import MyCasesPage from "./pages/dashboard/MyCasesPage";
import CaseDetailPage from "./pages/dashboard/CaseDetailPage";
import ReportsPage from "./pages/dashboard/ReportsPage";
import ConversationsPage from "./pages/dashboard/ConversationsPage";
import SettingsPage from "./pages/dashboard/SettingsPage";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
            <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
            <Route path="/forgot-password" element={<GuestRoute><ForgotPasswordPage /></GuestRoute>} />

            <Route
              path="/dashboard"
              element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}
            >
              <Route index element={<DashboardPage />} />
              <Route path="cases" element={<CasesPage />} />
              <Route path="my-cases" element={<MyCasesPage />} />
              <Route path="my-cases/:caseId" element={<CaseDetailPage />} />
              <Route path="uploads" element={<UploadsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="conversations" element={<ConversationsPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            <Route path="/404" element={<NotFoundPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "var(--toast-bg, #fff)",
              color: "var(--toast-color, #0f172a)",
              border: "1px solid var(--toast-border, #e2e8f0)",
              borderRadius: "12px",
              fontSize: "14px",
              fontWeight: "500",
              boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
            },
          }}
        />
      </AuthProvider>
    </ThemeProvider>
  );
}
