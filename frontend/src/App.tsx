import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { useAuthStore } from './store/useAuthStore';
import DashboardPage from './features/dashboard/Dashboard';
import DevicesPage from './features/devices/DevicesPage';
import ControlsPage from './features/controls/ControlsPage';
import ConfigurationPage from './features/configuration/ConfigurationPage';
import CalibrationPage from './features/calibration/CalibrationPage';
import OtaPage from './features/ota/OtaPage';
import HistoryPage from './features/history/HistoryPage';
import EnvironmentPage from './features/environment/EnvironmentPage';
import LoginPage from './features/auth/LoginPage';
import SetupPage from './features/auth/SetupPage';

const AuthGuard = () => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<SetupPage />} />

        <Route element={<AuthGuard />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/controls" element={<ControlsPage />} />
            <Route path="/environment" element={<EnvironmentPage />} />
            <Route path="/configuration" element={<ConfigurationPage />} />
            <Route path="/calibration" element={<CalibrationPage />} />
            <Route path="/ota" element={<OtaPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
