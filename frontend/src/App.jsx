import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Alerts from './pages/Alerts';
import Activities from './pages/Activities';
import LiveFeed from './pages/LiveFeed';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="cameras" element={<Cameras />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="activities" element={<Activities />} />
            <Route path="live-feed" element={<LiveFeed />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;

