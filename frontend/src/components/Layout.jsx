import { useState, useEffect, useRef } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { alertService } from '../services/alertService';

const Layout = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const notificationRef = useRef(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [notificationAlerts, setNotificationAlerts] = useState([]);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const isDashboard = location.pathname === '/dashboard' || location.pathname === '/';
  const hasBackground = ['/dashboard', '/', '/cameras', '/alerts', '/activities', '/live-feed', '/users', '/profile'].includes(location.pathname);

  const fetchNotificationData = async () => {
    try {
      setNotificationLoading(true);
      // Use same API as Alerts page so count matches "pending" tab
      const data = await alertService.getAll({ limit: 100 });
      const alerts = Array.isArray(data) ? data : data?.alerts ?? [];
      const pendingCount = alerts.filter((a) => a.status === 'pending').length;
      setNotificationCount(pendingCount);
      setNotificationAlerts(alerts.slice(0, 10));
    } catch {
      setNotificationCount(0);
      setNotificationAlerts([]);
    } finally {
      setNotificationLoading(false);
    }
  };

  useEffect(() => {
    fetchNotificationData();
  }, []);

  // Auto-refresh notification count (e.g. when new alerts are created)
  useEffect(() => {
    const interval = setInterval(fetchNotificationData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const onFocus = () => fetchNotificationData();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  useEffect(() => {
    const onRefreshNotifications = () => fetchNotificationData();
    window.addEventListener('refresh-notifications', onRefreshNotifications);
    return () => window.removeEventListener('refresh-notifications', onRefreshNotifications);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notificationRef.current && !notificationRef.current.contains(e.target)) {
        setNotificationOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`min-h-screen ${hasBackground ? 'bg-transparent' : 'bg-gray-50'}`}>
      <nav className={`fixed top-0 left-0 right-0 z-50 shadow-lg border-b border-slate-700 ${hasBackground ? 'bg-slate-800/95 backdrop-blur-md' : 'bg-slate-800'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-white">Smart CCTV</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                {isAdmin && (
                  <Link
                    to="/cameras"
                    className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                  >
                    Cameras
                  </Link>
                )}
                <Link
                  to="/live-feed"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Live Feed
                </Link>
                <Link
                  to="/alerts"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Alerts
                </Link>
                <Link
                  to="/activities"
                  className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  Activities
                </Link>
                {isAdmin && (
                  <Link
                    to="/users"
                    className="border-transparent text-gray-300 hover:border-blue-400 hover:text-white inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                  >
                    User Management
                  </Link>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative" ref={notificationRef}>
                <button
                  type="button"
                  onClick={() => {
                    setNotificationOpen((o) => !o);
                    if (!notificationOpen) fetchNotificationData();
                  }}
                  className="relative p-2 text-gray-300 hover:text-white rounded-md hover:bg-slate-700 transition-colors"
                  aria-label="Notifications"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  {notificationCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                      {notificationCount > 99 ? '99+' : notificationCount}
                    </span>
                  )}
                </button>
                {notificationOpen && (
                  <div className="absolute right-0 mt-2 w-80 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-50 max-h-[24rem] flex flex-col">
                    <div className="px-4 py-3 border-b border-gray-200">
                      <h3 className="text-sm font-semibold text-gray-900">Alerts</h3>
                      {notificationCount > 0 && (
                        <p className="text-xs text-gray-500 mt-0.5">{notificationCount} pending</p>
                      )}
                    </div>
                    <div className="overflow-y-auto flex-1">
                      {notificationLoading ? (
                        <div className="px-4 py-6 text-center text-sm text-gray-500">Loading...</div>
                      ) : notificationAlerts.length === 0 ? (
                        <div className="px-4 py-6 text-center text-sm text-gray-500">No alerts</div>
                      ) : (
                        <ul className="py-1">
                          {notificationAlerts.map((alert) => (
                            <li key={alert.id} className="px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0">
                              <Link
                                to="/alerts"
                                onClick={() => setNotificationOpen(false)}
                                className="block"
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                                    {alert.severity}
                                  </span>
                                  <span className="text-xs text-gray-400 shrink-0">
                                    {alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                                  </span>
                                </div>
                                <p className="text-sm font-medium text-gray-900 mt-1">
                                  {alert.alert_type ? alert.alert_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()) : 'Alert'}
                                </p>
                                <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">{alert.message}</p>
                                {alert.camera_name && (
                                  <p className="text-xs text-gray-400 mt-1">Camera: {alert.camera_name}</p>
                                )}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 rounded-b-lg">
                      <Link
                        to="/alerts"
                        onClick={() => setNotificationOpen(false)}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        View all alerts →
                      </Link>
                    </div>
                  </div>
                )}
              </div>
              <Link
                to="/profile"
                className="text-sm text-gray-200 hover:text-white transition-colors"
              >
                {user?.username} ({user?.role})
              </Link>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className={`max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 pt-24 ${hasBackground ? 'bg-transparent' : ''}`}>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

