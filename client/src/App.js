import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Box } from '@mui/material';

// Layout
import MainLayout from './components/Layout/MainLayout';

// Pages
import Login from './pages/Auth/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import LiveMap from './pages/Vessels/LiveMap';
import VesselList from './pages/Vessels/VesselList';
import VesselDetails from './pages/Vessels/VesselDetails';
import PortList from './pages/Ports/PortList';
import PortDetails from './pages/Ports/PortDetails';
import SafetyOverview from './pages/Safety/SafetyOverview';
import Analytics from './pages/Analytics/Analytics';
import VoyageReplay from './pages/Analytics/VoyageReplay';
import DashboardList from './pages/Dashboards/DashboardList';
import DashboardBuilder from './pages/Dashboards/DashboardBuilder';
import UserManagement from './pages/Admin/UserManagement';
import SystemConfig from './pages/Admin/SystemConfig';
import AuditLogs from './pages/Admin/AuditLogs';
import Profile from './pages/Profile/Profile';

// Redux
import { checkAuth } from './store/slices/authSlice';
import { initSocket } from './services/socket';

function App() {
  const dispatch = useDispatch();
  const { user, token } = useSelector((state) => state.auth);

  useEffect(() => {
    // Check if user is authenticated on mount
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      dispatch(checkAuth());
    }
  }, [dispatch]);

  useEffect(() => {
    // Initialize socket connection when authenticated
    if (token) {
      initSocket(token);
    }
  }, [token]);

  // Protected Route component
  const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    if (!token) {
      return <Navigate to="/login" replace />;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
      return <Navigate to="/dashboard" replace />;
    }

    return children;
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={!token ? <Login /> : <Navigate to="/dashboard" />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* Vessels */}
          <Route path="vessels">
            <Route index element={<VesselList />} />
            <Route path="map" element={<LiveMap />} />
            <Route path=":id" element={<VesselDetails />} />
          </Route>

          {/* Ports */}
          <Route path="ports">
            <Route index element={<PortList />} />
            <Route path=":id" element={<PortDetails />} />
          </Route>

          {/* Safety */}
          <Route path="safety" element={<SafetyOverview />} />

          {/* Analytics (Analyst+) */}
          <Route
            path="analytics"
            element={
              <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="analytics/voyage/:id"
            element={
              <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                <VoyageReplay />
              </ProtectedRoute>
            }
          />

          {/* Dashboards (Analyst+) */}
          <Route path="dashboards">
            <Route index element={<DashboardList />} />
            <Route
              path="new"
              element={
                <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                  <DashboardBuilder />
                </ProtectedRoute>
              }
            />
            <Route
              path=":id"
              element={
                <ProtectedRoute allowedRoles={['analyst', 'admin']}>
                  <DashboardBuilder />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Admin Routes */}
          <Route
            path="admin/users"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <UserManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/config"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SystemConfig />
              </ProtectedRoute>
            }
          />
          <Route
            path="admin/audit"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AuditLogs />
              </ProtectedRoute>
            }
          />

          {/* Profile */}
          <Route path="profile" element={<Profile />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Box>
  );
}

export default App;
